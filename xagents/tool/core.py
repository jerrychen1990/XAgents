#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@Time    :   2024/01/04 14:01:01
@Author  :   ChenHao
@Contact :   jerrychen1990@gmail.com
'''

from typing import Any, Callable, Dict, List

from pydantic import BaseModel, Field


class Parameter(BaseModel):
    name: str
    type: str
    desctiption: str
    required: bool


class BaseTool(BaseModel):
    name:str = Field(..., description="工具名称")
    description:str = Field(..., description="工具描述")
    parameters: List[Parameter] = Field(..., description="工具参数")
    callable:Callable = Field(..., description="工具执行函数")
    
    
    def execute(self, *args, **kwargs) -> Any:
        return self.callable(*args, **kwargs)

    def to_markdown(self):
        tool_info = f"**[名称]**:{self.name}\n\n**[描述]**:{self.description}\n\n"
        param_infos = []
        for parameter in self.parameters:
            param_infos.append(
                f"- **[参数名]**:{parameter.name}\n\n **[类型]**:{parameter.type}\n\n **[描述]**:{parameter.desctiption}\n\n **[必填]**:{parameter.required}")
        param_infos = "\n\n".join(param_infos)
        return tool_info + param_infos


class ToolCall(BaseModel):
    name: str = Field(description="工具名称")
    parameters: Dict[str, Any] = Field(description="工具调用的参数")
    extra_info: dict = Field(description="额外的信息,比如GLM需要的call_id", default=dict())
    resp: Any = Field(description="工具执行的返回结果,为执行时为None", default=None)

    def to_markdown(self):
        return f"**[调用工具]**: {self.name} **[参数]**: {self.parameters} **[返回结果]**: {self.resp}"
