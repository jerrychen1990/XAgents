#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@Time    :   2023/12/08 11:27:57
@Author  :   ChenHao
@Contact :   jerrychen1990@gmail.com
'''


from typing import List
from xagents.config import *
import shutil
from snippets import jdump_lines, jload_lines, log_cost_time
from xagents.kb.vector_store import get_vecstore_cls, VectorStore
from xagents.kb.loader import load_file
from xagents.kb.splitter import BaseSplitter
from xagents.kb.common import *
from xagents.model import EMBD, get_embd_model
from langchain_core.documents import Document


# 知识库处理后的切片基础类型


def get_kb_dir(kb_name) -> str:
    return os.path.join(KNOWLEDGE_BASE_DIR, kb_name)


def get_chunk_path(kb_name, file_name) -> str:
    return os.path.join(get_kb_dir(kb_name), "chunk", file_name+".jsonl")


class KnwoledgeBaseFile:
    def __init__(self, kb_name: str, origin_file_path: str):
        self.kb_name = kb_name
        self.file_name = os.path.basename(origin_file_path)
        self.stem, self.suffix = os.path.splitext(self.file_name)
        self.chunks: List[KBChunk] = None
        self.origin_file_path = origin_file_path
        self._save_origin()

    def _save_origin(self):
        dst_path = os.path.join(get_kb_dir(self.kb_name), "origin", self.file_name)
        if dst_path == self.origin_file_path:
            return
        os.makedirs(os.path.dirname(dst_path), exist_ok=True)
        logger.info(f"save origin file to {dst_path}")
        shutil.copy(self.origin_file_path, dst_path)

    # 加载/切割文件

    def _split(self, origin_chunks: List[Chunk]) -> List[KBChunk]:
        rs_chunks, idx = [], 0
        splitter = BaseSplitter(parse_table=True)
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
        jdump_lines(to_dumps, dst_path)

    def load_chunks(self, chunk_path: str):
        chunk_dicts = jload_lines(chunk_path)
        logger.info(f"loaded {len(chunk_dicts)} from {chunk_path}")
        self.chunks: List[Chunk] = [Chunk(**c, idx=idx, kb_name=self.kb_name, file_name=self.file_name) for idx, c in enumerate(chunk_dicts)]
        return self.chunks

    def parse(self) -> List[KBChunk]:
        logger.info("start parsing")
        pages = load_file(self.origin_file_path)
        logger.info(f"load {len(pages)} pages")
        self.chunks = self._split(pages)
        logger.info(f"splitted to {len(self.chunks)} kb_chunks")
        self._save_chunks()
        return self.chunks


class KnwoledgeBase:

    def __init__(self, name: str, description=None, vecstore_cls: str = "FAISS", reparse=False,
                 embedding_config: dict = dict(model_cls="ZhipuEmbedding")) -> None:
        self.name = name
        self.description = description if description else f"{self.name}知识库"
        self._build_dirs()

        self.embd_model: EMBD = get_embd_model(embedding_config)

        self.kb_files: List[KnwoledgeBaseFile] = self._load_kb_files(re_parse=reparse)
        self.vecstore_cls = get_vecstore_cls(vecstore_cls)
        self.vecstore = self._load_vecstore()

    def _build_dirs(self):
        self.kb_dir = get_kb_dir(self.name)
        self.origin_dir = os.path.join(self.kb_dir, "origin")

        self.chunk_dir = os.path.join(self.kb_dir, "chunk")
        self.vecstore_path = os.path.join(self.kb_dir, "vectstore")
        os.makedirs(self.origin_dir, exist_ok=True)
        os.makedirs(self.chunk_dir, exist_ok=True)

    def _load_kb_files(self, re_parse=False) -> List[KnwoledgeBaseFile]:
        logger.info("loading kb files...")
        kb_files = []
        for file_name in os.listdir(self.origin_dir):
            logger.info(f"loading kb_file:{file_name}")
            kb_file: KnwoledgeBaseFile = KnwoledgeBaseFile(kb_name=self.name, origin_file_path=os.path.join(self.origin_dir, file_name))
            chunk_path = get_chunk_path(self.kb_dir, file_name)
            if not re_parse and os.path.exists(chunk_path):
                kb_file.load_chunks(chunk_path)
            else:
                kb_file.parse()
            kb_files.append(kb_file)
        return kb_files

    def _load_vecstore(self) -> VectorStore:
        if os.path.exists(self.vecstore_path):
            logger.info(f"loading vecstore from {self.vecstore_path}")
            vecstore = self.vecstore_cls.load_local(folder_path=self.vecstore_path,
                                                    embeddings=self.embd_model,)
        else:
            logger.info(f"{self.vecstore_path} not exists, will not load vecstore")
            vecstore = None
        return vecstore

    def _add_chunks(self, chunks: List[Chunk]):
        logger.info(f"adding {len(chunks)} chunks to vecstore")
        documents: List[Document] = [chunk.to_document() for chunk in chunks]
        if not self.vecstore:
            self.vecstore = self.vecstore_cls.from_documents(documents, embedding=self.embd_model)
        else:
            self.vecstore.add_documents(documents, embedding=self.embd_model)
        logger.info("storing vectors...")
        self.vecstore.save_local(self.vecstore_path)

    def add_kb_file(self, kb_file: KnwoledgeBaseFile):
        if not kb_file.chunks:
            kb_file.parse()
        self._add_chunks(kb_file.chunks)

    def add_file(self, file_path: str):
        kb_file = KnwoledgeBaseFile(kb_name=self.name, origin_file_path=file_path)
        self.add_kb_file(kb_file)

    @log_cost_time(name="rebuild vectstore")
    def rebuild(self):
        all_chunks = []

        for kb_file in self.kb_files:
            logger.info(f"rebuilding {kb_file}")
            chunks = kb_file.chunks
            all_chunks.extend(all_chunks)
        logger.info(f"rebuilding vecstore with {len(all_chunks)}")
        self.vecstore = None
        self._add_chunks(chunks)

    @log_cost_time(name="kb_search")
    def search(self, query: str, top_k: int = 3, score_threshold=None) -> List[RecalledChunk]:
        if not self.vecstore:
            logger.error("向量索引尚未建立，无法搜索!")
            return []
        docs_with_score = self.vecstore.similarity_search_with_score(query, k=top_k, score_threshold=score_threshold)
        logger.info(f"{len(docs_with_score)} docs found")
        recalled_chunks = [RecalledChunk.from_document(d, score=s) for d, s in docs_with_score]

        return recalled_chunks


if __name__ == "__main__":
    origin_file_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "../data/raw/贵州茅台2022年报-4.pdf")
    kb_file = KnwoledgeBaseFile(kb_name="test", origin_file_path=origin_file_path)
    chunks = kb_file.parse()
    print(chunks[:2])
