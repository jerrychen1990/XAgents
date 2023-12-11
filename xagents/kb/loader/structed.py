#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@Time    :   2023/12/11 17:04:22
@Author  :   ChenHao
@Contact :   jerrychen1990@gmail.com
'''
import os
from typing import List
from xagents.kb.common import Chunk
from xagents.kb.loader.common import AbastractLoader
from snippets import read2list


class StructedLoader(AbastractLoader):
    def __init__(self, content_key="content", page_idx_key="page", content_type_key="chunk_type") -> None:
        self.content_key = content_key
        self.page_idx_key = page_idx_key
        self.content_type_key = content_type_key

    def load(self, file_path: str) -> List[Chunk]:
        records = read2list(file_path)
        chunks = []
        for item in records[:]:
            rs_item = dict(content=item[self.content_key], page_idx=item.get(self.page_idx_key, 1),
                           content_type=item[self.content_type_key])
            chunks.append(Chunk(**rs_item))
        return chunks


if __name__ == "__main__":
    from xagents.config import XAGENT_HOME
    loader = StructedLoader()

    file_path = os.path.join(XAGENT_HOME, "data/raw/贵州茅台2022年报.json")
    chunks = loader.load(file_path=file_path)

    print(len(chunks))
    print(chunks[0])
