#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@Time    :   2024/01/04 14:01:01
@Author  :   ChenHao
@Contact :   jerrychen1990@gmail.com
'''

from abc import abstractmethod
from typing import Any, Dict, List

from pydantic import BaseModel

class Parameter(BaseModel):
    name:str
    type:str
    desctiption:str
    required:bool
    



class BaseTool:
    def __init__(self, name:str, description:str) -> None:
        self.name=name
        self.description=description
    
    @property
    @abstractmethod
    def parameters(self)->List[Parameter]:
        raise NotImplementedError

    @abstractmethod
    def execute(self, *args, **kwargs) -> Any:
        raise NotImplementedError


class ToolCall(BaseModel):
    name:str
    parameters:Dict[str, Any]
    extra_info:dict = {}





