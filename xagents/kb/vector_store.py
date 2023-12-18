#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@Time    :   2023/12/08 16:57:23
@Author  :   ChenHao
@Contact :   jerrychen1990@gmail.com
'''

from langchain.vectorstores.faiss import FAISS
from langchain.vectorstores.elasticsearch import ElasticsearchStore
from langchain.vectorstores import VectorStore as VectorStore


_vecstores = [FAISS, ElasticsearchStore]
_name2vecstores = {e.__name__: e for e in _vecstores}


def list_vecstores():
    return [e.__name__ for e in _vecstores]


def get_vecstore_cls(name: str):
    return _name2vecstores[name]
