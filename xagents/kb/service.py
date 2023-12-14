#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@Time    :   2023/12/12 11:34:29
@Author  :   ChenHao
@Contact :   jerrychen1990@gmail.com
'''

from xagents.config import *
from xagents.kb.core import KnwoledgeBase
from xagents.util import get_log
from xagents.kb.vector_store import list_vecstores as lv
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


if __name__ == "__main__":
    print(list_knowledge_base_names())
    print(list_vecstores())
    print(list_distance_strategy())