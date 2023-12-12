#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@Time    :   2023/12/07 18:33:25
@Author  :   ChenHao
@Contact :   jerrychen1990@gmail.com
'''


from abc import abstractmethod


class AbstractMemory:
    @abstractmethod
    def remember(self, role: str, content: str):
        raise NotImplementedError

    @abstractmethod
    def to_llm_history(self):
        raise NotImplementedError

    def clear(self):
        raise NotImplementedError


class BaseMemory(AbstractMemory):
    def __init__(self, size: int):
        self.size = size
        self.memory = []

    def remember(self, role: str, content: str):
        self.memory.append(dict(role=role, content=content))

    def to_llm_history(self):
        return self.memory

    def clear(self):
        self.memory.clear()
