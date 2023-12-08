#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@Time    :   2023/12/08 11:27:57
@Author  :   ChenHao
@Contact :   jerrychen1990@gmail.com
'''


import enum
from typing import List, Optional
from pydantic import BaseModel, Field
from xagents.config import *
import shutil
from snippets import jdump_lines
from xagents.kb.vector_store import VectorStore, get_vecstore_cls
from xagents.kb.loader import get_loader_cls
from xagents.kb.splitter import BaseSplitter
from xagents.model import EMBD, get_embd_model
from langchain_core.documents import Document


class ChunkType(str, enum.Enum):
    TABLE = "TABLE"
    TITLE = "TITLE"
    TEXT = "TEXT"

# 知识库处理后的切片基础类型


class Chunk(BaseModel):
    content: str = Field(description="chunk的内容")
    search_content: Optional[str] = Field(description="用来检索的内容", default=None)
    chunk_type: ChunkType = Field(description="chunk类型", default=ChunkType.TEXT)
    idx: int = Field(description="chunk在文档中的顺序,从0开始")
    page_idx: Optional[int] = Field(description="chunk在文档中的页码,从1开始")
    kb_name: str = Field(description="知识库名称")
    file_name: str = Field(description="文件名称")

    def to_lite_dict(self):
        return self.model_dump(mode="json", exclude={"idx", "kb_name", "file_name"}, exclude_defaults=True)

    def to_document(self) -> Document:
        if self.search_content:
            page_content, metadata = self.search_content, dict(content=self.content)
        else:
            page_content, metadata = self.content, dict()

        metadata.update(chunk_type=self.chunk_type.value, idx=self.idx, page_idx=self.page_idx,
                        kb_name=self.kb_name, file_name=self.file_name)
        return Document(page_content=page_content, metadata=metadata)

    @classmethod
    def from_document(cls, document: Document):
        content = document.metadata.pop("content", None)
        item = dict(content=content, search_content=document.page_content) if content else dict(content=document.page_content)
        item.update(document.metadata)
        return cls(**item)


class RecalledChunk(Chunk):
    score: float = Field(description="召回chunk的分数")
    forwards: List[Chunk] = Field(description="chunk的下文扩展", default=[])
    backwards: List[Chunk] = Field(description="chunk的上文扩展", default=[])

    @classmethod
    def from_document(cls, document: Document, score: float):
        chunk = cls.__bases__[0].from_document(document)
        recalled_chunk = cls(**chunk.__dict__, score=score)
        return recalled_chunk


def get_kb_dir(kb_name) -> str:
    return os.path.join(KNOWLEDGE_BASE_DIR, kb_name)


class KnwoledgeBaseFile:
    def __init__(self, kb_name: str, origin_file_path: str):
        self.kb_name = kb_name
        self.file_name = os.path.basename(origin_file_path)
        self.stem, self.suffix = os.path.splitext(self.file_name)
        self.chunks: List[Chunk] = []
        self.origin_file_path = origin_file_path
        self._save_origin()

    def _save_origin(self):
        dst_path = os.path.join(get_kb_dir(self.kb_name), "origin", self.file_name)
        os.makedirs(os.path.dirname(dst_path), exist_ok=True)
        logger.info(f"save origin file to {dst_path}")
        shutil.copy(self.origin_file_path, dst_path)

    # 加载/切割文件

    def _split(self, text_pages: List[str]) -> List[Chunk]:
        chunks, idx = [], 0
        splitter = BaseSplitter()
        for page_idx, page in enumerate(text_pages):
            texts = splitter.split(page)
            for text in texts:
                chunk = Chunk(content=text, idx=idx, page_idx=page_idx, kb_name=self.kb_name, file_name=self.file_name)
                chunks.append(chunk)
                idx += 1

        return chunks

    def _save_chunks(self):
        dst_path = os.path.join(get_kb_dir(self.kb_name), "chunks", self.file_name+".jsonl")
        os.makedirs(os.path.dirname(dst_path), exist_ok=True)
        logger.info(f"save chunks to {dst_path}")
        to_dumps = [c.to_lite_dict() for c in self.chunks]
        jdump_lines(to_dumps, dst_path)

    def parse(self) -> List[Chunk]:
        logger.info("start parsing")
        loader_cls = get_loader_cls(self.file_name)
        loader = loader_cls()
        text_pages = loader.load(self.origin_file_path)
        logger.info(f"load {len(text_pages)} pages")
        self.chunks = self._split(text_pages)
        logger.info(f"splitted to {len(self.chunks)} chunks")
        self._save_chunks()
        return self.chunks

    # 保存到向量数据库
    def save2vector_store(self):
        if not self.chunks:
            raise ValueError("chunks is empty")
        documents: List[Document] = [chunk.to_document() for chunk in self.chunks]
        return documents


class KnwoledgeBase:

    def __init__(self, name: str, description=None, kb_files: List[KnwoledgeBaseFile] = [],
                 vecstore_cls: str = "FAISS", embedding_config: dict = dict(model_cls="ZhipuEmbedding")) -> None:
        self.name = name
        self.description = description if description else f"{self.name}知识库"
        self.kb_files = kb_files
        self.vecstore_cls = get_vecstore_cls(vecstore_cls)
        self.vecstore: VectorStore = None
        self.embd_model: EMBD = get_embd_model(embedding_config)

    def add_chunks(self, chunks: List[Chunk]):
        logger.info(f"adding {len(chunks)} chunks to vecstore")
        documents: List[Document] = [chunk.to_document() for chunk in chunks]
        if not self.vecstore:
            self.vecstore = self.vecstore_cls.from_documents(documents, embedding=self.embd_model)
        else:
            self.vecstore.add_documents(documents, embedding=self.embd_model)

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
