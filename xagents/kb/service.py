#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@Time    :   2023/12/12 11:34:29
@Author  :   ChenHao
@Contact :   jerrychen1990@gmail.com
'''

from typing import List
from xagents.config import *
from xagents.kb.core import KnwoledgeBase, KnwoledgeBaseFile
from xagents.kb.loader import _EXT2LOADER
from xagents.util import get_log
from xagents.kb.vector_store import list_vecstores as lv
from xagents.kb.splitter import _SPLITERS
from langchain.vectorstores.utils import DistanceStrategy


logger = get_log(__name__)


def list_knowledge_base_names():
    kb_names = os.listdir(KNOWLEDGE_BASE_DIR)
    return kb_names


def list_vecstores():
    return lv()


def list_distance_strategy():
    return [e.name for e in DistanceStrategy]


def get_knowledge_base(name: str) -> KnwoledgeBase:
    kb_names = list_knowledge_base_names()
    assert name in kb_names
    # TODO load逻辑，从数据库中获取kb信息
    kb = KnwoledgeBase(name=name, embedding_config=dict(model_cls="ZhipuEmbedding"))
    return kb


def list_kb_files(kb_name: str) -> List[KnwoledgeBaseFile]:
    kb = get_knowledge_base(kb_name)
    kb_files = kb.list_files()
    return kb_files


def list_valid_exts():
    return list(_EXT2LOADER.keys())


def list_spliters() -> List[str]:
    return list(e.__name__ for e in _SPLITERS)


def create_knowledge_base(name: str, desc: str,
                          embedding_config: dict, vecstore_cls: str = "FAISS",
                          distance_strategy: DistanceStrategy = DistanceStrategy.MAX_INNER_PRODUCT
                          ):
    kb_names = list_knowledge_base_names()
    if name in kb_names:
        logger.warning(f"Knowledge base {name} already exists.")
        return
    kb = KnwoledgeBase(name=name, embedding_config=embedding_config,
                       description=desc,
                       vecstore_cls=vecstore_cls, distance_strategy=distance_strategy)
    return kb


if __name__ == "__main__":
    print(list_knowledge_base_names())
    print(list_vecstores())
    print(list_distance_strategy())
