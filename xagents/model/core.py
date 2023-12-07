#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@Time    :   2023/12/07 17:45:15
@Author  :   ChenHao
@Contact :   jerrychen1990@gmail.com
'''


from abc import abstractmethod


class LLM:
    def __init__(self, name: str, version: str):
        self.name = name
        self.version = version

    @abstractmethod
    def generate(self, prompt, history=[], system=None, stream=True):
        raise NotImplementedError
