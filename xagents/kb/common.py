#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@Time    :   2023/12/11 15:39:40
@Author  :   ChenHao
@Contact :   jerrychen1990@gmail.com
'''


from abc import abstractmethod
import enum

from pydantic import BaseModel, Field


from typing import List, Optional

from xagents.config import *
from langchain_core.documents import Document


class ContentType(str, enum.Enum):
    TABLE = "TABLE"
    TITLE = "TITLE"
    TEXT = "TEXT"


class Chunk(BaseModel):
    content: str = Field(description="chunk的内容")
    content_type: ContentType = Field(description="chunk类型", default=ContentType.TEXT)
    search_content: Optional[str] = Field(description="用来检索的内容", default=None)
    page_idx: int = Field(description="chunk在文档中的页码,从1开始")


class KBChunk(Chunk):
    kb_name: str = Field(description="知识库名称")
    file_name: str = Field(description="文件名称")
    idx: int = Field(description="chunk在文档中的顺序,从0开始")
    
    def to_dict(self):
        return super().model_dump_json()

    def to_document(self) -> Document:
        if self.search_content:
            page_content, metadata = self.search_content, dict(content=self.content)
        else:
            page_content, metadata = self.content, dict()

        metadata.update(chunk_type=self.content_type.value, idx=self.idx, page_idx=self.page_idx,
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


class TableType(str, enum.Enum):
    KV_TABLE = "KV_TABLE"


class Table:
    @abstractmethod
    def to_desc(self) -> List[str]:
        raise NotImplementedError


class Dim1Table(Table, BaseModel):
    keys: List[str] = Field(description="key字段")
    values: List[str] = Field(description="value字段", default=None)

    def to_desc(self) -> List[str]:
        logger.debug(f"parsing a dim1table with {len(self.keys)} keys")
        descs = []
        assert len(self.keys) == len(self.values)
        for k, v in zip(self.keys, self.values):
            descs.append(f"{k}是{v}")
        return descs


class Dim2Table(Table, BaseModel):
    dim1_keys: List[str] = Field(description="第一个维度的key")
    dim2_keys: List[str] = Field(description="第二个维度的可以")
    values: List[List[str]] = Field(description="value字段", default=None)

    def to_desc(self) -> List[str]:
        descs = []
        logger.debug(f"parsing a dim2table with {len(self.values)} rows and {len(self.values[0])} cols")

        assert len(self.dim1_keys) == len(self.values) and len(self.dim2_keys) == len(self.values[0])
        for r, k1 in enumerate(self.dim1_keys):
            for c, k2 in enumerate(self.dim2_keys):
                if len(self.dim1_keys) <= len(self.dim2_keys):
                    descs.append(f"({k1},{k2})是{self.values[r][c]}")
                else:
                    descs.append(f"({k2},{k1})是{self.values[r][c]}")
        return descs
