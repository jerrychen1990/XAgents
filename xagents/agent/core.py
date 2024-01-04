#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@Time    :   2023/12/07 17:54:34
@Author  :   ChenHao
@Contact :   jerrychen1990@gmail.com
'''

from typing import Generator, List, Optional, Union

from abc import abstractmethod

from pydantic import BaseModel, Field

from xagents.kb.common import RecalledChunk
from xagents.tool.core import ToolCall


class AgentResp(BaseModel):
    content: Union[str, Generator] = Field(description="返回的消息")
    references: Optional[List[RecalledChunk]] = Field(description="召回的片段")
    tool_call:Optional[ToolCall] = Field(description="工具调用")


class AbstractAgent:

    def __init__(self, name) -> None:
        self.name = name

    @abstractmethod
    def chat(self, message: str, stream=True, do_remember=True) -> AgentResp:
        raise NotImplementedError

    @abstractmethod
    def remember(self, role: str, message: str):
        raise NotImplementedError
