#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@Time    :   2023/12/08 16:57:23
@Author  :   ChenHao
@Contact :   jerrychen1990@gmail.com
'''

import copy
from typing import Type
from langchain.vectorstores.faiss import FAISS
from langchain.vectorstores import VectorStore
from langchain.vectorstores.elasticsearch import ElasticsearchStore
from langchain.vectorstores import VectorStore as VectorStore

from xagents.model.core import EMBD


class XVecStore(VectorStore):
    def is_local(self):
        raise NotImplementedError()

    @classmethod
    def need_embd(cls):
        raise NotImplementedError()


class XFAISS(XVecStore, FAISS):
    def is_local(self):
        return True

    @classmethod
    def need_embd(cls):
        return False


class XES(XVecStore, ElasticsearchStore):
    def is_local(self):
        return False

    @classmethod
    def need_embd(cls):
        return True


_vecstores = [XFAISS, XES]
_name2vecstores = {e.__name__: e for e in _vecstores}


def list_vecstores():
    return [e.__name__ for e in _vecstores]


def get_vecstore_cls(name: str) -> Type[XVecStore]:
    return _name2vecstores[name]


def get_vector_store(config: dict, embd_model: EMBD = None) -> XVecStore:
    tmp_config = copy.copy(config)
    vs_cls = tmp_config.pop("vs_cls")
    vs_cls = get_vecstore_cls(vs_cls)
    if vs_cls.need_embd():
        if embd_model is None:
            raise ValueError("Need embd model to create vector store")
        tmp_config.update(embedding=embd_model)
    return vs_cls(**tmp_config)
