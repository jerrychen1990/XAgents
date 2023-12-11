#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@Time    :   2023/12/11 16:29:39
@Author  :   ChenHao
@Contact :   jerrychen1990@gmail.com
'''

import os
from typing import Type
from xagents.kb.loader.common import AbastractLoader
from xagents.kb.loader.markdown import MarkDownLoader
from xagents.kb.loader.pdf import PDFLoader
from xagents.kb.loader.structed import StructedLoader

_EXT2LOADER = {
    "pdf": PDFLoader,
    "markdown": MarkDownLoader,
    "md": MarkDownLoader,
    "json": StructedLoader,
    "jsonl": StructedLoader,
    "csv": StructedLoader
}


def get_loader_cls(file_path: str) -> Type[AbastractLoader]:
    ext = os.path.splitext(file_path)[-1].lower().replace(".", "")
    loader = _EXT2LOADER[ext]
    return loader


def load_file(file_path: str, **kwargs):
    loader_cls = get_loader_cls(file_path)
    loader: AbastractLoader = loader_cls(**kwargs)
    contents = loader.load(file_path)
    return contents
