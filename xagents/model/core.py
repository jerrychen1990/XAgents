#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@Time    :   2023/12/07 17:45:15
@Author  :   ChenHao
@Contact :   jerrychen1990@gmail.com
'''


from abc import abstractmethod
from typing import Generator, Tuple, Union

from langchain_core.embeddings import Embeddings

from xagents.tool.core import ToolCall

StrOrGen = Union[str, Generator]


class LLM:
    """语言模型的基类
    """
    def __init__(self, name: str, version: str):
        """初始化函数

        Args:
            name (str): LLM的名称
            version (str): 模型版本
        """
        self.name = name
        self.version = version

    @abstractmethod
    def generate(self, prompt:str, history=[], system:str=None, stream=True, **kwargs)->Tuple[ToolCall,StrOrGen]:
        """生成结果

        Args:
            prompt (str): 给LLM的提示词
            history (list, optional): 历史message列表. Defaults to [].
            system (_type_, optional): system信息. Defaults to None.
            stream (bool, optional): 是否返回generator. Defaults to True.
        Returns:
            Tuple[ToolCall,StrOrGen]: ToolCall:工具调用实例，可以为空, StrOrGen:模型回复内容，字符串或generator
        """
        raise NotImplementedError

    @classmethod
    def list_version(cls):
        raise NotImplementedError


class EMBD(Embeddings):
    @classmethod
    def get_dim(cls) -> int:
        raise NotImplementedError

class Reranker:
    def __init__(self, name: str, version: str):
        self.name = name
        self.version = version

    @abstractmethod
    def cal_similarity(self, text1:str, text2:str)->float:
        raise NotImplementedError

    

