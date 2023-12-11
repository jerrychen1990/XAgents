#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@Time    :   2023/12/08 14:38:44
@Author  :   ChenHao
@Contact :   jerrychen1990@gmail.com
'''

import re
from abc import abstractmethod
from typing import List
from xagents.config import *
from xagents.kb.common import Chunk, ContentType, Dim1Table, Dim2Table, Table, TableType

from xagents.util import DEFAULT_LOG

logger = DEFAULT_LOG


def is_head_spliter(line):
    return re.match("\||([|-]*)\||", line.strip())


def is_kv_table(cols):
    return len(cols) == 2


def convert_kv_table(lines):
    rs = []
    for line in lines:
        if is_head_spliter(line):
            continue

        rs.append(f"")


def judge_table_type(line):
    if len(line) == 2:
        return TableType.KV_TABLE
    return TableType.KV_TABLE


def lines2table(lines) -> Table:
    row_num = len(lines)
    col_num = len(lines[0])
    if row_num == 2:
        return Dim1Table(keys=lines[0], values=lines[1])
    if col_num == 2:
        return Dim1Table(keys=[l[0] for l in lines], values=[l[1] for l in lines])
    key1s = [l[0] for l in lines[1:]]
    key2s = lines[0][1:]
    body = [e[1:] for e in lines[1:]]
    return Dim2Table(dim1_keys=key1s, dim2_keys=key2s, values=body)


def markdown2table(md_table: str) -> Table:
    lines = md_table.split("\n")
    lines = [[e.strip() for e in e.split("|")[1:-1]] for e in lines]
    lines = [e for e in lines if not re.match("-+", e[0])]

    table: Table = lines2table(lines)
    return table


class AbstractSplitter:
    @abstractmethod
    def split(self, text: str) -> List[str]:
        raise NotImplementedError

    def split_chunk(self, chunk: Chunk) -> List[Chunk]:
        return [Chunk(content=e, content_type=chunk.content_type, page_idx=chunk.page_idx) for e in self.split(chunk.content)]


class BaseSplitter(AbstractSplitter):

    def __init__(self, parse_table=False):
        self.parse_table = parse_table

    def _parse_text(self, text: str) -> str:
        text = text.strip()
        text = re.sub("\s+", " ", text)
        text = re.sub("\.+", "", text)
        return text

    def split(self, text: str, splitter="\n") -> List[str]:
        texts = re.split(splitter, text)
        texts = [self._parse_text(t) for t in texts]
        return texts

    def split_chunk(self, chunk: Chunk) -> List[Chunk]:
        chunks = super().split_chunk(chunk)
        if chunk.content_type == ContentType.TABLE:
            table = markdown2table(chunk.content)
            descs = table.to_desc()
            table_chunks = [Chunk(content=e, content_type=chunk.content_type, page_idx=chunk.page_idx) for e in descs]
            chunks.extend(table_chunks)
        return chunks


if __name__ == "__main__":
    spliter = BaseSplitter()
    texts = ["第一节  释义  ................................ ", " "]
    for text in texts:
        print(spliter.split(text))
