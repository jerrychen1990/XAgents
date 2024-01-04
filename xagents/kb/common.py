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


from typing import List, Optional, Tuple

from xagents.config import *
from langchain_core.documents import Document

# 切片类型


class ContentType(str, enum.Enum):
    TABLE = "TABLE"
    TITLE = "TITLE"
    TEXT = "TEXT"
    PARSED_TABLE = "PARSED_TABLE"

# 切片


class Chunk(BaseModel):
    content: str = Field(description="chunk的内容")
    content_type: ContentType = Field(description="chunk类型", default=ContentType.TEXT)
    search_content: Optional[str] = Field(description="用来检索的内容", default=None)
    page_idx: int = Field(description="chunk在文档中的页码,从1开始")

# 知识库中的切片


class KBChunk(Chunk):
    kb_name: str = Field(description="知识库名称")
    file_name: str = Field(description="文件名称")
    idx: int = Field(description="chunk在文档中的顺序,从0开始")

    def to_dict(self):
        return self.model_dump(mode="json", exclude_none=True, exclude={"kb_name", "file_name", "idx"})

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

    def __hash__(self) -> int:
        return hash((self.kb_name, self.file_name, self.idx))
    
    def __eq__(self, __value: object) -> bool:
        return hash(self) == hash(__value)


# 召回的切片
class RecalledChunk(KBChunk):
    query: str = Field(description="召回chunk的query")
    score: float = Field(description="召回chunk的分数")
    forwards: List[Chunk] = Field(description="chunk的下文扩展", default=[])
    backwards: List[Chunk] = Field(description="chunk的上文扩展", default=[])

    @classmethod
    def from_document(cls, document: Document, query: str, score: float)->"RecalledChunk":
        """从langchain的Document构造过来

        Args:
            document (Document): langchain的Document
            query (str): 相关问题
            score (float): 召回得分

        Returns:
            _type_: RecalledChunk
        """
        chunk = cls.__bases__[0].from_document(document)
        recalled_chunk = cls(**chunk.__dict__, query=query, score=score)
        return recalled_chunk
    
    def get_content(self):
        if self.search_content:
            return self.search_content  + "\n" + self.content
        
        return self.content
        

    def to_plain_text(self):
        rs = self.get_content()
        if self.backwards:
            backwords_str = "\n".join([chunk.content for chunk in self.backwards])
            rs = backwords_str + "\n" + rs
        if self.forwards:
            forwards_str = "\n".join([chunk.content for chunk in self.forwards])
            rs = rs+"\n"+forwards_str
        return rs

    def to_detail_text(self, with_context=False, max_len=None) -> str:
        backword_len = sum(len(c.content) for c in self.backwards)
        forwards_len = sum(len(c.content) for c in self.forwards)
        content = self.get_content()
        main_len = len(content)

        detail_text = f"[score={self.score:2.3f}][{main_len}字][扩展后{backword_len+main_len+forwards_len}字][类型{self.content_type.value}][第{self.page_idx}页][index:{self.idx}][相关文档:{self.file_name}][相关问题:{self.query}]\n\n **{content}**"
        if with_context:
            backwords_str, forwards_str = self.get_contexts(max_len=max_len)
            if backwords_str:
                detail_text = backwords_str + "\n\n"+detail_text
            if forwards_str:
                detail_text = detail_text + "\n\n"+forwards_str
        return detail_text

    def get_contexts(self, max_len=None) -> Tuple[str, str]:
        backwords_str, forwards_str = "", ""
        backword_len = sum(len(c.content) for c in self.backwards)
        forwards_len = sum(len(c.content) for c in self.forwards)

        if backword_len:
            backwords_str = "\n".join([f"{chunk.content}" for idx, chunk in enumerate(self.backwards)])
            if max_len:
                backwords_str = backwords_str[:max_len]+"..."
            backwords_str = f"上文[{backword_len}]字\n\n{backwords_str}"

        if forwards_len:
            forwards_str = "\n".join([f"{chunk.content}" for idx, chunk in enumerate(self.forwards)])
            if max_len:
                forwards_str = forwards_str[:max_len]+"..."
            forwards_str = f"下文[{forwards_len}]字\n\n{forwards_str}"

        return backwords_str, forwards_str


# 表格
class Table:
    row_context: str
    col_context: str

    @abstractmethod
    def to_desc(self) -> List[str]:
        raise NotImplementedError

    def get_context_info(self):
        if self.row_context:
            if self.col_context:
                return f"在[{self.row_context}, {self.col_context}]下，"
            else:
                return f"在{self.row_context}下，"
        else:
            if self.col_context:
                return f"在{self.col_context}下，"
            return ""

# 一维表格


class Dim1Table(Table, BaseModel):
    keys: List[str] = Field(description="key字段")
    values: List[str] = Field(description="value字段", default=None)

    def to_desc(self) -> List[str]:
        # logger.debug(f"parsing a dim1table with {len(self.keys)} keys")
        descs = []
        assert len(self.keys) == len(self.values)
        for k, v in zip(self.keys, self.values):
            k, v = k.strip(), v.strip()
            if k and v:
                descs.append(f"{self.get_context_info()}{k}是{v}")
        return descs

# 二维表格


class Dim2Table(Table, BaseModel):
    dim1_keys: List[str] = Field(description="第一个维度的key")
    dim2_keys: List[str] = Field(description="第二个维度的可以")
    values: List[List[str]] = Field(description="value字段", default=None)

    def to_desc(self) -> List[str]:
        descs = []
        # logger.debug(f"parsing a dim2table with {len(self.values)} rows and {len(self.values[0])} cols")

        assert len(self.dim1_keys) == len(self.values) and len(self.dim2_keys) == len(self.values[0])
        for r, k1 in enumerate(self.dim1_keys):
            for c, k2 in enumerate(self.dim2_keys):
                k1, k2, v = k1.strip(), k2.strip(), self.values[r][c].strip()
                if k1 and k2 and v:
                    if len(self.dim1_keys) <= len(self.dim2_keys):
                        descs.append(f"{self.get_context_info()}({k1},{k2})是{self.values[r][c]}")
                    else:
                        descs.append(f"{self.get_context_info()}({k2},{k1})是{self.values[r][c]}")
        return descs
