#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@Time    :   2023/12/08 14:38:44
@Author  :   ChenHao
@Contact :   jerrychen1990@gmail.com
'''

import copy
import re
from abc import abstractmethod
from typing import List

import numpy as np
from xagents.config import *
from xagents.kb.common import Chunk, ContentType, Dim1Table, Dim2Table, Table
from snippets import groupby
from xagents.util import DEFAULT_LOG

logger = DEFAULT_LOG


def arr2table(row: str, col: str, arr: np.ndarray) -> Table:
    # logger.debug(f"convert {row=},{col=}, {arr=} to table")

    row_num, col_num = arr.shape

    if row_num == 2:
        return Dim1Table(keys=arr[0], values=arr[1], row_context=row, col_context=col)
    if col_num == 2:
        return Dim1Table(keys=arr[:, 0], values=arr[:, 1], row_context=row, col_context=col)
    key1s = arr[1:, 0]
    key2s = arr[0][1:]
    body = arr[1:, 1:]
    return Dim2Table(dim1_keys=key1s, dim2_keys=key2s, values=body, row_context=row, col_context=col)


# 将arr按照值相同的行|列做拆分
def split_arr_by_same_value(arr: np.ndarray, info, axis):
    assert arr.ndim == 2
    row_num, col_num = arr.shape
    context_key = "row" if axis == 1 else "col"
    # logger.debug(f"splitting {arr=} with {context_key}")

    tgt = np.repeat(arr[:, [0]], col_num, axis=1) if context_key == "row" else np.repeat(arr[[0], :], row_num, axis=0)
    # logger.debug(f"{tgt=}")

    identical_lines = np.all(arr == tgt, axis=axis)
    identical_idxs = np.where(identical_lines)[0]
    # logger.debug(f"split with {identical_idxs=}")
    if len(identical_idxs) == 0:
        return [(copy.copy(info), arr)]

    pre = -1
    context = ""
    rs = []
    for idx in identical_idxs:
        if pre+1 < idx:
            # print(f"{context_key} from {pre+1} to {idx}")
            tmp_info = copy.copy(info)
            tmp_info[context_key] = context
            sub_arr = arr[pre+1:idx, :] if axis == 1 else arr[:, pre+1:idx]
            rs.append((tmp_info, sub_arr))
        context = arr[idx][0] if axis == 1 else arr[0][idx]
        pre = idx

    size = arr.shape[0] if axis == 1 else arr.shape[1]

    if pre < size-1:
        tmp_info = copy.copy(info)
        tmp_info[context_key] = context
        sub_arr = arr[pre+1:size, :] if axis == 1 else arr[:, pre+1:size]
        rs.append((tmp_info, sub_arr))
    return rs


def merge_arrs(arrs, axis=1):
    to_merge = None
    to_merge_key = None
    rs = dict()
    for info, arr in arrs:
        # print(arr.shape)
        if to_merge is not None:
            merged = np.concatenate([to_merge, arr], axis=axis)
            # print(merged)
            key = "".join([to_merge_key, info["col"]])
            rs[key] = merged
            to_merge = None
        else:
            if arr.shape[1] == 1 and axis == 1:
                to_merge = arr
                to_merge_key = info["col"]
            else:
                key = info.get("col", "")
                rs[key] = arr
    return rs


def markdown2tables(md_table: str) -> List[Table]:
    lines = md_table.split("\n")
    lines = [[e.strip() for e in e.split("|")[1:-1]] for e in lines if e.strip()]
    lines = [e for e in lines if not re.match("-+", e[0])]
    arr = np.array(lines)
    # 按照值完全一样的行切分
    arrs = split_arr_by_same_value(arr, dict(), 1)
    # 按照值完全一样的列切分
    # print(arrs)
    rs = []
    for info, arr in arrs:
        rs.extend(split_arr_by_same_value(arr, info, 0))
    # 按照行聚合
    grouped_arrs = groupby(rs, key=lambda x: x[0].get("row", ""))
    # print(grouped_arrs)
    for row in grouped_arrs.keys():
        grouped_arrs[row] = merge_arrs(grouped_arrs[row])
    # logger.debug(f"{grouped_arrs=}")
    # return grouped_arrs
    rs_tables = []
    for r, arrs in grouped_arrs.items():
        for c, arr in arrs.items():
            table = arr2table(row=r, col=c, arr=arr)
            rs_tables.append(table)

    return rs_tables


class AbstractSplitter:
    @abstractmethod
    def split(self, text: str) -> List[str]:
        raise NotImplementedError

    def split_chunk(self, chunk: Chunk) -> List[Chunk]:
        return [Chunk(content=e.strip(), content_type=chunk.content_type, page_idx=chunk.page_idx) for e in self.split(chunk.content) if e.strip()]


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
            tables = markdown2tables(chunk.content)
            for table in tables:
                descs = table.to_desc()
                table_chunks = [Chunk(content=e, content_type=ContentType.PARSED_TABLE, page_idx=chunk.page_idx) for e in descs]
                chunks.extend(table_chunks)
        return chunks


if __name__ == "__main__":
    spliter = BaseSplitter()
    texts = ["第一节  释义  ................................ ", " "]
    for text in texts:
        print(spliter.split(text))
