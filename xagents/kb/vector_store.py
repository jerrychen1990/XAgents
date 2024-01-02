#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@Time    :   2023/12/08 16:57:23
@Author  :   ChenHao
@Contact :   jerrychen1990@gmail.com
'''

import copy
from typing import Type
from langchain.vectorstores.faiss import FAISS, dependable_faiss_import
from langchain.vectorstores.utils import DistanceStrategy
from langchain.vectorstores import VectorStore
from langchain.docstore.in_memory import InMemoryDocstore
from langchain.vectorstores.elasticsearch import ElasticsearchStore
from langchain.vectorstores import VectorStore as VectorStore

from xagents.model.core import EMBD
from xagents.util import get_log

logger = get_log(__name__)


class XVecStore(VectorStore):
    @classmethod
    def is_local(cls):
        raise NotImplementedError()

    @classmethod
    def need_embd(cls):
        raise NotImplementedError()

    @classmethod
    def from_config(cls, config: dict):
        raise NotImplementedError()


class XFAISS(XVecStore, FAISS):
    @classmethod
    def is_local(cls):
        return True

    @classmethod
    def need_embd(cls):
        return False

    @classmethod
    def from_config(cls, config: dict):

        distance_strategy = config["distance_strategy"]
        embedding: EMBD = config["embedding"]
        dim_len = embedding.get_dim()

        faiss = dependable_faiss_import()
        if distance_strategy == DistanceStrategy.MAX_INNER_PRODUCT:
            index = faiss.IndexFlatIP(dim_len)
        else:
            # Default to L2, currently other metric types not initialized.
            index = faiss.IndexFlatL2(dim_len)
        config.update(embedding_function=config.pop("embedding"))
        config.update(index=index, docstore=InMemoryDocstore(), index_to_docstore_id={})
        logger.debug(f"{config=}")

        vecstore = cls(
            **config
        )
        return vecstore


class XES(XVecStore, ElasticsearchStore):
    @classmethod
    def is_local(cls):
        return False

    @classmethod
    def need_embd(cls):
        return True

    @classmethod
    def from_config(cls, config: dict):
        vecstore = cls(
            **config
        )
        return vecstore


_vecstores = [XFAISS, XES]
_name2vecstores = {e.__name__:e for e in _vecstores}


def list_vecstores():
    return [e.__name__ for e in _vecstores]


def get_vecstore_cls(name: str) -> Type[XVecStore]:
    return _name2vecstores[name]


def get_vector_store(config: dict, embd_model: EMBD = None) -> XVecStore:
    tmp_config = copy.copy(config)
    vs_cls = tmp_config.pop("vs_cls")
    vs_cls = get_vecstore_cls(vs_cls)
    logger.debug(f"getting vecstore with config:{config}")
    # if vs_cls.need_embd():
    #     if embd_model is None:
    #         raise ValueError("Need embd model to create vector store")
    tmp_config.update(embedding=embd_model)
    return vs_cls.from_documents([], **tmp_config)
