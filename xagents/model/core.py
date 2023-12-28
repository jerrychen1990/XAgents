#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@Time    :   2023/12/07 17:45:15
@Author  :   ChenHao
@Contact :   jerrychen1990@gmail.com
'''


from abc import abstractmethod

from langchain_core.embeddings import Embeddings


class LLM:
    def __init__(self, name: str, version: str):
        self.name = name
        self.version = version

    @abstractmethod
    def generate(self, prompt, history=[], system=None, stream=True,
                 temperature=0.01, **kwargs):
        raise NotImplementedError

    def list_version(self):
        raise NotImplementedError


class EMBD(Embeddings):
    @classmethod
    def get_dim(cls) -> int:
        raise NotImplementedError
