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
from xagents.kb.loader import get_loader_cls
from xagents.kb.splitter import AbstractSplitter
from xagents.kb.common import *
from xagents.model.service import EMBD, get_embd_model, get_rerank_model
from langchain_core.documents import Document
from langchain.vectorstores.utils import DistanceStrategy


def get_kb_dir(kb_name) -> str:
    return os.path.join(KNOWLEDGE_BASE_DIR, kb_name)


def get_chunk_path(kb_name, file_name) -> str:
    return os.path.join(get_kb_dir(kb_name), "chunk", file_name+".jsonl")


def get_origin_path(kb_name, file_name) -> str:
    return os.path.join(get_kb_dir(kb_name), "origin", file_name)


def get_config_path(kb_name) -> str:
    return os.path.join(get_kb_dir(kb_name), "config.json")


# 知识库文件类
class KnwoledgeBaseFile:
    def __init__(self, kb_name: str, origin_file_path: str, loader_kwargs=dict()):
        self.kb_name = kb_name
        self.file_name = os.path.basename(origin_file_path)
        self.stem, self.suffix = os.path.splitext(self.file_name)

        self.chunks: List[KBChunk] = None
        self.origin_file_path = self._save_origin(origin_file_path)
        self.loader_cls = get_loader_cls(self.origin_file_path)
        self.loader = self.loader_cls(**loader_kwargs)
        self.chunk_path = get_chunk_path(self.kb_name, self.file_name)
        self._load_chunks()

    def _save_origin(self, origin_file_path):
        """
        保存原始文件
        """
        dst_path = get_origin_path(self.kb_name, self.file_name)
        if dst_path == origin_file_path:
            return dst_path
        os.makedirs(os.path.dirname(dst_path), exist_ok=True)
        logger.info(f"save origin file to {dst_path}")
        shutil.copy(origin_file_path, dst_path)
        return dst_path

    # 加载/切割文件
    def _split(self, origin_chunks: List[Chunk], splitter: AbstractSplitter) -> List[KBChunk]:
        """
        切分文件
        """
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
        """
        保存切片
        """
        dst_path = get_chunk_path(self.kb_name, self.file_name)
        os.makedirs(os.path.dirname(dst_path), exist_ok=True)
        logger.info(f"save chunks to {dst_path}")
        to_dumps = [c.to_dict() for c in self.chunks]
        # logger.info(f"{to_dumps=}")
        jdump_lines(to_dumps, dst_path)

    def _load_chunks(self) -> List[KBChunk]:
        """
        从切片文件加载切片
        """
        if not os.path.exists(self.chunk_path):
            logger.info(f"{self.chunk_path} not exists, will not load chunks")
            self.chunks = None
            return
        chunk_dicts = jload_lines(self.chunk_path)
        logger.info(f"loaded {len(chunk_dicts)} from {self.chunk_path}")
        self.chunks: List[KBChunk] = [KBChunk(**c, idx=idx, kb_name=self.kb_name, file_name=self.file_name) for idx, c in enumerate(chunk_dicts)]
        return self.chunks

    def remove(self):
        """
        删除知识库文档
        """
        chunk_path = get_chunk_path(self.kb_name, self.file_name)
        if os.path.exists(chunk_path):
            os.remove(chunk_path)

        origin_path = get_origin_path(self.kb_name, self.file_name)
        if os.path.exists(origin_path):
            os.remove(origin_path)

    def parse(self, splitter: AbstractSplitter) -> List[KBChunk]:
        """
        load并切片、存储
        """
        logger.info("start parsing")
        origin_chunks: List[Chunk] = self.loader.load(self.origin_file_path)
        logger.info(f"load {len(origin_chunks)} origin_chunks")
        # logger.info(origin_chunks[:4])
        self.chunks = self._split(origin_chunks, splitter)
        logger.info(f"splitted to {len(self.chunks)} kb_chunks")
        self._save_chunks()
        return self.chunks

    def get_info(self) -> dict:
        """
        获取文件信息
        """
        return dict(file_name=self.file_name, chunk_len=len(self.chunks) if self.chunks else 0,
                    loader=self.loader_cls.__name__, origin_file_path=self.origin_file_path, chunk_path=self.chunk_path)

# 知识库类


class KnwoledgeBase:

    def __init__(self, name: str,
                 embedding_config: dict,
                 description=None,
                 vecstore_config: str = dict(vs_cls="FAISS"),
                 distance_strategy: DistanceStrategy = DistanceStrategy.MAX_INNER_PRODUCT,
                 prompt_template: str = DEFAULT_KB_PROMPT_TEMPLATE
                 ) -> None:
        self.name = name
        self.description = description if description else f"{self.name}知识库"
        self._build_dirs()
        self.prompt_template = prompt_template

        self.embedding_config = copy.copy(embedding_config)
        self.embd_model: EMBD = get_embd_model(self.embedding_config)

        self.kb_files: List[KnwoledgeBaseFile] = self._load_kb_files()
        self.distance_strategy = distance_strategy

        # self.vecstore: XVecStore = get_vector_store(vecstore_config, embd_model=self.embd_model)
        self.vecstore_config = copy.copy(vecstore_config)
        # self.vecstore_config.update(embedding=self.embd_model, distance_strategy=self.distance_strategy)
        self.vecstore_cls: Type[XVecStore] = get_vecstore_cls(self.vecstore_config.get("vs_cls"))
        self.vecstore = self._load_vecstore()

    @classmethod
    def from_config(cls, config: Union[dict, str]):
        if isinstance(config, str):
            config = jload(config)

        return cls(**config)

    def list_kb_file_info(self) -> List[dict]:
        """
        列出知识库文件
        """
        return [dict(No=idx+1, **e.get_info()) for idx, e in enumerate(self.kb_files)]

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
            kb_files.append(kb_file)
        return kb_files

    def _load_vecstore(self) -> XVecStore:
        """
        加载向量库
        """

        tmp_config = dict(**self.vecstore_config, embedding=self.embd_model, distance_strategy=self.distance_strategy)
        del tmp_config["vs_cls"]

        if self.vecstore_cls.is_local():
            if os.path.exists(self.vecstore_path):
                logger.info(f"loading vecstore from {self.vecstore_path}")
                vecstore: XVecStore = self.vecstore_cls.load_local(folder_path=self.vecstore_path,
                                                                   embeddings=self.embd_model, distance_strategy=self.distance_strategy)
            else:
                logger.info(f"{self.vecstore_path} not exists, create a new local vecstore")
                vecstore: XVecStore = self.vecstore_cls.from_config(tmp_config)
        else:
            logger.info(f"vecstore is remote, create a new remote vecstore")
            vecstore: XVecStore = self.vecstore_cls.from_config(tmp_config)
        return vecstore

    def _add_chunks(self, chunks: List[KBChunk]):
        """
        添加切片
        """
        logger.info(f"adding {len(chunks)} chunks to vecstore")
        documents: List[Document] = [chunk.to_document() for chunk in chunks]
        if self.vecstore:
            self.vecstore.add_documents(documents, embedding=self.embd_model)
        else:
            tmp_config = copy.copy(self.vecstore_config)
            del tmp_config["vs_cls"]
            self.vecstore = self.vecstore_cls.from_documents(documents=documents, embedding=self.embd_model,
                                                             **tmp_config, distance_strategy=self.distance_strategy)
        if self.vecstore.is_local():
            logger.info("storing vectors...")
            self.vecstore.save_local(self.vecstore_path)

    def add_kb_file(self, kb_file: KnwoledgeBaseFile, splitter: AbstractSplitter):
        """
        添加文档
        """
        logger.info(f"adding {kb_file.file_name} to {self.name}")
        if not kb_file.chunks:
            kb_file.parse(splitter=splitter)
        self._add_chunks(kb_file.chunks)
        logger.info("add kb_file done")

    def add_file(self, file_path: str, splitter: AbstractSplitter):
        kb_file = KnwoledgeBaseFile(kb_name=self.name, origin_file_path=file_path)
        self.add_kb_file(kb_file, splitter=splitter)

    def list_files(self) -> List[KnwoledgeBaseFile]:
        return self.kb_files

    def remove_file(self, kb_file: Union[KnwoledgeBaseFile, str]):
        """
        删除文档
        """

        if isinstance(kb_file, str):
            kb_file = self._get_kb_file_by_name(kb_file)
        if not kb_file:
            return

        self.kb_files.remove(kb_file)
        kb_file.remove()
        self.rebuild()

    def delete(self):
        """
        删除知识库
        """
        logger.info(f"deleting kb:{self.name}")
        shutil.rmtree(path=self.kb_dir)
        logger.info(f"{self.name} deleted")

    def save(self):
        """
        保存知识库配置文件
        """

        conf = dict(name=self.name, embedding_config=self.embedding_config, description=self.description,
                    vecstore_config=self.vecstore_config, distance_strategy=self.distance_strategy,
                    prompt_template=self.prompt_template)
        logger.info(f"saving config :{conf}")
        jdump(conf, self.config_path)

    @log_cost_time(name="rebuild vectstore")
    def rebuild(self, re_parse=False):
        """
        重新构建向量知识库
        """
        all_chunks = []

        for kb_file in self.kb_files:
            logger.info(f"rebuilding {kb_file.file_name}")
            if not kb_file.chunks or re_parse:
                kb_file.parse()
            chunks = kb_file.chunks
            all_chunks.extend(chunks)
        logger.info(f"rebuilding vecstore with {len(all_chunks)} chunks")
        if all_chunks:
            logger.debug(f"sample chunk:{all_chunks[0]}")
            self.vecstore = None
            self._add_chunks(chunks)
            
            
    def _rerank(self, recalled_chunks:List[RecalledChunk], rerank_config:dict)->List[RecalledChunk]:
        """重排序
        Args:
            recalled_chunks (List[RecalledChunk]): 待排序的切片

        Returns:
            List[RecalledChunk]: 排序后的切片
        """
        logger.debug("reranking...")
        rerank_model = get_rerank_model(rerank_config)
        if rerank_model:
            logger.info("reranking chunks with rerank model")
            for chunk in recalled_chunks:
                similarity = rerank_model.cal_similarity(chunk.query, chunk.content)
                chunk.score = similarity
                
        
        recalled_chunks.sort(key=lambda x:x.score, reverse=True)
        return recalled_chunks
        
        
        
        

    @log_cost_time(name="kb_search")
    def search(self, query: str, top_k: int = 3, score_threshold: float = None,
               do_split_query=False, file_names: List[str] = None, rerank_config:dict={},
               do_expand=False, expand_len: int = 500, forward_rate: float = 0.5) -> List[RecalledChunk]:
        """知识库检索

        Args:
            query (str): 待检索的query
            top_k (int, optional): 返回多少个chunk. Defaults to 3.
            score_threshold (float, optional): 召回的chunk相似度阈值. Defaults to None.
            do_split_query (bool, optional): 是否按照？切分query并分别召回. Defaults to False.
            file_names (List[str], optional): 按照名称过滤需要召回的片段所在的文件. Defaults to None.
            do_expand (bool, optional): 返回的chunk是否做上下文扩展. Defaults to False.
            expand_len (int, optional): 上下文扩展后的chunk字符长度（do_expand=True时生效）. Defaults to 500.
            forward_rate (float, optional): 上下文扩展时向下文扩展的比率（do_expand=True时生效）. Defaults to 0.5.

        Returns:
            List[RecalledChunk]: 相关的切片，按照score降序
        """

        if not self.vecstore:
            logger.error("向量索引尚未建立，无法搜索!")
            return []

        recalled_chunks = []
        # 切分query
        querys = split_query(query, do_split_query)
        logger.debug(f"split origin query into {len(querys)} querys")

        # 将原始score归一化到0-1，越大越接近
        def _get_score(s):
            if self.distance_strategy in [DistanceStrategy.EUCLIDEAN_DISTANCE]:
                return 1.-s
            return s

        # 过滤条件
        _filter = dict()
        if file_names:
            _filter = dict(file_name=file_names)

        for query in querys:
            logger.debug(f"searching {query} with vecstore_cls: {self.vecstore.__class__.__name__}, {_filter=}")

            docs_with_score = self.vecstore.similarity_search_with_score(query, k=top_k, score_threshold=score_threshold, filter=_filter)
            logger.debug(f"{len(docs_with_score)} origin chunks found")
            logger.debug(f"{query}'s related docs{[d.page_content[:30] for d,s in docs_with_score]}")

            tmp_recalled_chunks = [RecalledChunk.from_document(d, score=_get_score(s), query=query) for d, s in docs_with_score]
            recalled_chunks.extend(tmp_recalled_chunks)
            
            
        # 去重，避免召回相同切片
        
        recalled_chunks = list(set(recalled_chunks))
        logger.info(f"{len(recalled_chunks)} origin chunks found")
        
        recalled_chunks=self._rerank(recalled_chunks, rerank_config)[:top_k]
        logger.info(f"get {len(recalled_chunks)} final chunks after sort")

        #上下文扩展
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
