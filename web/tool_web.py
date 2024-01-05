#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@Time    :   2024/01/05 15:24:49
@Author  :   ChenHao
@Contact :   jerrychen1990@gmail.com
'''
import streamlit as st
from xagents.tool.service import list_tools
from xagents.util import get_log
logger = get_log(name=__name__)

def load_view():
    tools = list_tools()
    for tool in tools:
        tool_info = tool.model_dump_json(exclude="callable",indent=4)
        # logger.info(tool_info)
        # logger.info(type(tool_info))
        
        st.json(tool_info)
        
        # st.markdown(tool.to_markdown())
    
    