#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@Time    :   2023/12/07 17:54:34
@Author  :   ChenHao
@Contact :   jerrychen1990@gmail.com
'''

from typing import Generator, Union

from abc import abstractmethod


class AbstractAgent:

    def __init__(self, name) -> None:
        self.name = name

    @abstractmethod
    def chat(message: str, stream=True) -> Union[Generator, str]:
        raise NotImplementedError
