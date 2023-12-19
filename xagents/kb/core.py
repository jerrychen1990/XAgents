#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@Time    :   2023/12/08 11:27:57
@Author  :   ChenHao
@Contact :   jerrychen1990@gmail.com
'''


import copy
import re
from typing import List, Type, Union
from xagents.config import *
import shutil
from snippets import jdump_lines, jload_lines, log_cost_time, read2list, jdump, jload
from xagents.kb.vector_store import XVecStore, get_vecstore_cls
from xagents.kb.loader import load_file
from xagents.kb.splitter import AbstractSplitter
from xagents.kb.common import *
from xagents.model.service import EMBD, get_embd_model
from langchain_core.documents import Document
from langchain.vectorstores.utils import DistanceStrategy


# 知识库处理后的切片基础类型


def get_kb_dir(kb_name) -> str:
    return os.path.join(KNOWLEDGE_BASE_DIR, kb_name)


def get_chunk_path(kb_name, file_name) -> str:
    return os.path.join(get_kb_dir(kb_name), "chunk", file_name+".jsonl")


def get_origin_path(kb_name, file_name) -> str:
    return os.path.join(get_kb_dir(kb_name), "origin", file_name)


def get_config_path(kb_name) -> str:
    return os.path.join(get_kb_dir(kb_name), "config.json")


class KnwoledgeBaseFile:
    def __init__(self, kb_name: str, origin_file_path: str):
        self.kb_name = kb_name
        self.file_name = os.path.basename(origin_file_path)
        self.stem, self.suffix = os.path.splitext(self.file_name)
        self.chunks: List[KBChunk] = None
        self.origin_file_path = origin_file_path
        self._save_origin()

    def _save_origin(self):
        dst_path = get_origin_path(self.kb_name, self.file_name)
        if dst_path == self.origin_file_path:
            return
        os.makedirs(os.path.dirname(dst_path), exist_ok=True)
        logger.info(f"save origin file to {dst_path}")
        shutil.copy(self.origin_file_path, dst_path)

    # 加载/切割文件
    def _split(self, origin_chunks: List[Chunk], splitter: AbstractSplitter) -> List[KBChunk]:
        rs_chunks, idx = [], 0
        for origin_chunk in origin_chunks:
            chunks = splitter.split_chunk(origin_chunk)
            for chunk in chunks:
                # print(chunk.model_dump(mode="json"))
                chunk = KBChunk(**chunk.model_dump(mode="json"), idx=idx, kb_name=self.kb_name, file_name=self.file_name)
                rs_chunks.append(chunk)
                idx += 1
        return rs_chunks

    def _save_chunks(self):
        dst_path = get_chunk_path(self.kb_name, self.file_name)
        os.makedirs(os.path.dirname(dst_path), exist_ok=True)
        logger.info(f"save chunks to {dst_path}")
        to_dumps = [c.to_dict() for c in self.chunks]
        # logger.info(f"{to_dumps=}")
        jdump_lines(to_dumps, dst_path)

    def load_chunks(self, chunk_path: str) -> List[KBChunk]:
        chunk_dicts = jload_lines(chunk_path)
        logger.info(f"loaded {len(chunk_dicts)} from {chunk_path}")
        self.chunks: List[KBChunk] = [KBChunk(**c, idx=idx, kb_name=self.kb_name, file_name=self.file_name) for idx, c in enumerate(chunk_dicts)]
        return self.chunks

    def remove(self):
        chunk_path = get_chunk_path(self.kb_name, self.file_name)
        if os.path.exists(chunk_path):
            os.remove(chunk_path)

        origin_path = get_origin_path(self.kb_name, self.file_name)
        if os.path.exists(origin_path):
            os.remove(origin_path)

    def parse(self, splitter: AbstractSplitter, do_save=True) -> List[KBChunk]:
        logger.info("start parsing")
        origin_chunks: List[Chunk] = load_file(self.origin_file_path)
        logger.info(f"load {len(origin_chunks)} origin_chunks")
        # logger.info(origin_chunks[:4])
        self.chunks = self._split(origin_chunks, splitter)
        logger.info(f"splitted to {len(self.chunks)} kb_chunks")

        if do_save:
            self._save_chunks()
        return self.chunks


class KnwoledgeBase:

    def __init__(self, name: str,
                 embedding_config: dict,
                 description=None,
                 vecstore_config: str = dict(vs_cls="FAISS"),
                 distance_strategy: DistanceStrategy = DistanceStrategy.MAX_INNER_PRODUCT
                 ) -> None:
        self.name = name
        self.description = description if description else f"{self.name}知识库"
        self._build_dirs()
        self.conf = dict(name=name, embedding_config=embedding_config, description=description,
                         vecstore_config=vecstore_config, distance_strategy=distance_strategy)

        self.embd_model: EMBD = get_embd_model(embedding_config)

        self.kb_files: List[KnwoledgeBaseFile] = self._load_kb_files()
        self.distance_strategy = distance_strategy

        # self.vecstore: XVecStore = get_vector_store(vecstore_config, embd_model=self.embd_model)
        self.vecstore_config = copy.copy(vecstore_config)
        self.vecstore_config.update(embedding=self.embd_model)
        self.vecstore_cls: Type[XVecStore] = get_vecstore_cls(self.vecstore_config.pop("vs_cls"))
        self.vecstore = self._load_vecstore()

    @classmethod
    def from_config(cls, config: Union[dict, str]):
        if isinstance(config, str):
            config = jload(config)

        return cls(**config)

    def _build_dirs(self):
        self.kb_dir = get_kb_dir(self.name)
        self.origin_dir = os.path.join(self.kb_dir, "origin")

        self.chunk_dir = os.path.join(self.kb_dir, "chunk")
        self.vecstore_path = os.path.join(self.kb_dir, "vectstore")
        self.config_path = get_config_path(self.name)
        os.makedirs(self.origin_dir, exist_ok=True)
        os.makedirs(self.chunk_dir, exist_ok=True)

    def _get_kb_file_by_name(self, file_name: str) -> KnwoledgeBaseFile:
        name2file = {e.file_name: e for e in self.kb_files}
        return name2file.get(file_name)

    def _load_kb_files(self, re_parse=False) -> List[KnwoledgeBaseFile]:
        logger.info("loading kb files...")
        kb_files = []
        for file_name in os.listdir(self.origin_dir):
            logger.info(f"loading kb_file:{file_name}")
            kb_file: KnwoledgeBaseFile = KnwoledgeBaseFile(kb_name=self.name, origin_file_path=os.path.join(self.origin_dir, file_name))
            chunk_path = get_chunk_path(self.kb_dir, file_name)
            if os.path.exists(chunk_path):
                kb_file.load_chunks(chunk_path)
            kb_files.append(kb_file)
        return kb_files

    def _load_vecstore(self) -> XVecStore:
        if self.vecstore_cls.is_local():
            if os.path.exists(self.vecstore_path):
                logger.info(f"loading vecstore from {self.vecstore_path}")
                vecstore: XVecStore = self.vecstore_cls.load_local(folder_path=self.vecstore_path,
                                                                   embeddings=self.embd_model, distance_strategy=self.distance_strategy)
            else:
                logger.info(f"{self.vecstore_path} not exists, create a new local vecstore")
                vecstore: XVecStore = self.vecstore_cls.from_config(self.vecstore_config)
        else:
            logger.info(f"vecstore is remote, create a new remote vecstore")
            vecstore: XVecStore = self.vecstore_cls.from_config(self.vecstore_config)
        return vecstore

    def _add_chunks(self, chunks: List[KBChunk]):
        logger.info(f"adding {len(chunks)} chunks to vecstore")
        documents: List[Document] = [chunk.to_document() for chunk in chunks]
        if self.vecstore:
            self.vecstore.add_documents(documents, embedding=self.embd_model)
        else:
            self.vecstore = self.vecstore_cls.from_documents(documents=documents, embedding=self.embd_model, **self.vecstore_config)
        if self.vecstore.is_local():
            logger.info("storing vectors...")
            self.vecstore.save_local(self.vecstore_path)

    def add_kb_file(self, kb_file: KnwoledgeBaseFile, splitter: AbstractSplitter):
        logger.info(f"adding {kb_file.file_name} to {self.name}")
        if not kb_file.chunks:
            kb_file.parse(splitter=splitter, do_save=True)
        self._add_chunks(kb_file.chunks)
        logger.info("add kb_file done")

    def add_file(self, file_path: str, splitter: AbstractSplitter):
        kb_file = KnwoledgeBaseFile(kb_name=self.name, origin_file_path=file_path)
        self.add_kb_file(kb_file, splitter=splitter)

    def list_files(self) -> List[KnwoledgeBaseFile]:
        return self.kb_files

    def remove_file(self, kb_file: Union[KnwoledgeBaseFile, str]):
        if isinstance(kb_file, str):
            kb_file = self._get_kb_file_by_name(kb_file)
        if not kb_file:
            return

        self.kb_files.remove(kb_file)
        kb_file.remove()
        self.rebuild()

    def delete(self):
        logger.info(f"deleting kb:{self.name}")
        shutil.rmtree(path=self.kb_dir)
        logger.info(f"{self.name} deleted")

    def save(self):
        jdump(self.conf, self.config_path)

    @log_cost_time(name="rebuild vectstore")
    def rebuild(self, re_parse=False):
        all_chunks = []

        for kb_file in self.kb_files:
            logger.info(f"rebuilding {kb_file.file_name}")
            if not kb_file.chunks or re_parse:
                kb_file.parse()
            chunks = kb_file.chunks
            all_chunks.extend(chunks)
        logger.info(f"rebuilding vecstore with {len(all_chunks)} chunks")
        logger.debug(f"sample chunk:{all_chunks[0]}")
        self.vecstore = None
        self._add_chunks(chunks)

    @log_cost_time(name="kb_search")
    def search(self, query: str, top_k: int = 3, score_threshold=None,
               do_split_query=False,
               do_expand=False, expand_len: int = 500, forward_rate: float = 0.5) -> List[RecalledChunk]:
        if not self.vecstore:
            logger.error("向量索引尚未建立，无法搜索!")
            return []

        recalled_chunks = []
        querys = split_query(query, do_split_query)
        logger.debug(f"split origin query into {len(querys)} querys")

        def _get_score(s):
            if self.distance_strategy in [DistanceStrategy.EUCLIDEAN_DISTANCE]:
                return 1.-s
            return s
        for query in querys:
            logger.debug(f"searching {query}  with vecstore_cls: {self.vecstore.__class__.__name__}")
            docs_with_score = self.vecstore.similarity_search_with_score(query, k=top_k, score_threshold=score_threshold)
            logger.debug(f"{len(docs_with_score)} origin chunks found")
            logger.debug(f"{query}'s related docs{[d.page_content[:30] for d,s in docs_with_score]}")

            tmp_recalled_chunks = [RecalledChunk.from_document(d, score=_get_score(s), query=query) for d, s in docs_with_score]
            recalled_chunks.extend(tmp_recalled_chunks)

        logger.info(f"{len(recalled_chunks)} origin chunks found")
        recalled_chunks.sort(key=lambda x: x.score, reverse=True)
        recalled_chunks = recalled_chunks[:top_k]
        logger.info(f"get {len(recalled_chunks)} final chunks after sort")

        if do_expand:
            logger.info("expanding recalled chunks")
            for chunk in recalled_chunks:
                expand_chunk(chunk, expand_len, forward_rate)

        return recalled_chunks


def split_query(query: str, do_split_query=False) -> List[str]:
    if do_split_query:
        rs = [e.strip() for e in re.split("\?|？", query) if e.strip()]
        return rs
    else:
        return [query]


# 扩展上下文到给定的长度
def expand_chunk(chunk: RecalledChunk, expand_len: int, forward_rate=0.5) -> RecalledChunk:
    logger.debug(f"expanding chunk {chunk}")
    chunk_path = get_chunk_path(chunk.kb_name, chunk.file_name)
    chunks = []
    for item in read2list(chunk_path):
        tmp = Chunk(**item)
        chunks.append(tmp)
    chunk_idx = chunk.idx

    to_expand = expand_len - len(chunk.content)
    if to_expand <= 0:
        return chunk

    forward_len = int(to_expand * forward_rate)
    backward_len = to_expand - forward_len
    logger.debug(f"epxand chunk with :{forward_len=}, {backward_len=}")
    backwards, forwards = [], []

    # 查找前面的chunk
    idx = chunk_idx-1
    while idx >= 0:
        tmp_chunk = chunks[idx]
        backward_len -= len(tmp_chunk.content)
        if backward_len < 0:
            break
        backwards.append(tmp_chunk)
        idx -= 1
    backwards.reverse()

    idx = chunk_idx + 1
    while idx < len(chunks):
        tmp_chunk = chunks[idx]
        forward_len -= len(tmp_chunk.content)
        if forward_len < 0:
            break
        forwards.append(tmp_chunk)
        idx += 1

    logger.debug(f"expand with {len(backwards)} backward chunks and {len(forwards)} forward chunks")
    chunk.backwards = backwards
    chunk.forwards = forwards
    return chunk


if __name__ == "__main__":
    origin_file_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "../data/raw/贵州茅台2022年报-4.pdf")
    kb_file = KnwoledgeBaseFile(kb_name="test", origin_file_path=origin_file_path)
    chunks = kb_file.parse()
    print(chunks[:2])
