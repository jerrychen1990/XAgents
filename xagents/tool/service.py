#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@Time    :   2024/01/04 18:26:54
@Author  :   ChenHao
@Contact :   jerrychen1990@gmail.com
'''

from typing import Any, List

from xagents.tool.common_tool import calculator
from xagents.tool.core import BaseTool, ToolCall


_ALL_TOOLS = [calculator]
_TOOL_MAP = {e.name:e for e in _ALL_TOOLS}


def invoke_tool_call(tool_call:ToolCall)->Any:
    tool = get_tool(tool_call.name)
    resp = tool.execute(**tool_call.parameters)
    tool_call.resp = resp
    return resp
    

def get_tool(tool_name:str)->BaseTool:
    if tool_name not in _TOOL_MAP:
        raise ValueError(f"Unknown tool: {tool_name}")
    tool:BaseTool = _TOOL_MAP[tool_name]
    return tool
    
def list_tools() -> List[BaseTool]:
    return _ALL_TOOLS
    
if __name__ == "__main__":
    tool_call = ToolCall(name="calculator", parameters={"expression": "1+1"})
    resp = invoke_tool_call(tool_call)
    print(resp)    
    
