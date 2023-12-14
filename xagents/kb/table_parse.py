#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@Time    :   2023/12/14 10:53:42
@Author  :   ChenHao
@Contact :   jerrychen1990@gmail.com
'''

import re
from typing import Dict, List

import numpy as np
from xagents.config import *
from xagents.kb.common import Dim1Table, Dim2Table, Table
from xagents.util import DEFAULT_LOG

logger = DEFAULT_LOG


def remove_line(arr: np.ndarray, line_values: List, axis) -> np.ndarray:
    for val in line_values:
        idxs = np.all(arr == val, axis=1-axis)
        idxs = np.where(idxs != 1)[0]
        arr = arr[:, idxs] if axis == 1 else arr[idxs]
    return arr


def arr2table(row: str, col: str, arr: np.ndarray) -> Table:
    # logger.debug(f"convert {row=},{col=}, {arr=} to table")
    row_num, col_num = arr.shape
    if row_num == 1 or col_num == 1:
        return None

    if row_num == 2:
        return Dim1Table(keys=arr[0], values=arr[1], row_context=row, col_context=col)
    if col_num == 2:
        return Dim1Table(keys=arr[:, 0], values=arr[:, 1], row_context=row, col_context=col)
    key1s = arr[1:, 0]
    key2s = arr[0][1:]
    body = arr[1:, 1:]
    return Dim2Table(dim1_keys=key1s, dim2_keys=key2s, values=body, row_context=row, col_context=col)


def _is_all_same(line, allow_empty=False) -> str:
    eles = [e for e in line if e]
    if not eles:
        return None
    tgt = eles[0]
    for item in line:
        if item == tgt or (allow_empty and item == ""):
            continue
        return None
    return tgt

# 将arr按照值相同的行|列做拆分


def split_arr_by_same_value(arr: np.ndarray, axis: int, allow_empty=False) -> Dict[str, np.ndarray]:
    assert arr.ndim == 2
    row_num, col_num = arr.shape
    tgt_num = col_num if axis == 1 else row_num

    rs = dict()
    start, key = 0, ""
    for idx in range(tgt_num):
        line = arr[idx] if axis == 0 else arr[:, idx]
        tmp_key = _is_all_same(line, allow_empty)
        if tmp_key:
            if idx > start:
                rs[key] = arr[start:idx] if axis == 0 else arr[:, start:idx]
            key = tmp_key
            start = idx+1
    if start < tgt_num:
        rs[key] = arr[start:] if axis == 0 else arr[:, start:]
    return rs


def merge_arrs(arrs, axis=1):
    to_merge = None
    to_merge_key = None
    rs = dict()
    for info, arr in arrs:
        # print(arr.shape)
        if to_merge is not None:
            # 临时解决
            min_dim = min(to_merge.shape[0], arr.shape[0])

            # logger.debug(f"merging arr:{to_merge}, shape={to_merge.shape}")
            # logger.debug(f"with {arr},  shape={arr.shape}")
            merged = np.concatenate([to_merge[:min_dim, :], arr[:min_dim, :]], axis=axis)
            # print(merged)
            key = "".join([to_merge_key, info.get("col", "")])
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


def md2arr(md_table: str) -> np.ndarray:
    lines = md_table.split("\n")
    lines = [[e.strip() for e in e.split("|")[1:-1]] for e in lines if e.strip()]
    lines = [e for e in lines if not re.match("-+", e[0])]
    arr = np.array(lines)
    arr = np.nan_to_num(arr).astype(str)
    return arr


def markdown2tables(md_table: str, remove_col_vals=["指"]) -> List[Table]:
    try:
        # 转化为np.ndarray
        arr = md2arr(md_table)
        # 删除空行
        arr = remove_line(arr, [""], axis=0)
        # 按照值完全一样，或者只有一个值的行切分
        arrs_groups = split_arr_by_same_value(arr, axis=0, allow_empty=False)
        # logger.debug(f"arr groups after cut by row :{arrs_groups}")
        # 按照值完全一样的列切分

        for row, arr in arrs_groups.items():
            arr = remove_line(arr, remove_col_vals, 1)
            col_group = split_arr_by_same_value(arr,  axis=1, allow_empty=False)
            arrs_groups[row] = col_group

        # logger.debug(f"arr groups after cut by col :{arrs_groups}")

        rs_tables = []
        for r, arrs in arrs_groups.items():
            for c, arr in arrs.items():
                table = arr2table(row=r, col=c, arr=arr)
                if table:
                    rs_tables.append(table)
    except Exception as e:
        logger.exception(e)
        message = f"fail to parse md_table:\n {md_table}"
        logger.error(message)
        raise e

    return rs_tables


if __name__ == "__main__":
    md_table = """
    |常用词语释义|常用词语释义|常用词语释义|
|-----|-----|-----|
|证监会|指|中国证券监督管理委员会|
|上交所|指|上海证券交易所|
|本公司、公司|指|贵州茅台酒股份有限公司|
|控股股东、集团公司|指|中国贵州茅台酒厂（集团）有限责任公司|
|报告期|指|2022年度|
|本报告|指|2022年年度报告|"""

    tables = markdown2tables(md_table)
    for table in tables:
        for desc in table.to_desc():
            print(desc)
        print("\n\n")
