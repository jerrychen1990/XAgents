#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@Time    :   2023/12/11 16:30:03
@Author  :   ChenHao
@Contact :   jerrychen1990@gmail.com
'''


import os
import re
from typing import List
from xagents.kb.common import Chunk
from xagents.kb.loader.common import AbastractLoader


def extract_md_table(text):
    tables = re.findall("^\\|(.*)\\|$", text, re.MULTILINE | re.DOTALL)
    return tables


class MarkDownLoader(AbastractLoader):
    def load(self, file_path: str) -> List[Chunk]:
        with open(file_path, "r") as f:
            content = f.read()
            return [Chunk(content=content, page_idx=1)]


if __name__ == "__main__":
    from xagents.config import XAGENT_HOME
    loader = MarkDownLoader()

    file_path = os.path.join(XAGENT_HOME, "data/raw/贵州茅台2022年报-4.md")
    chunks = loader.load(file_path=file_path)

    print(len(chunks))
    print(chunks[0])
