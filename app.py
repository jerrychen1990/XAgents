
#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@Time    :   2023/12/14 15:53:37
@Author  :   ChenHao
@Contact :   jerrychen1990@gmail.com
'''
from web import kb_web, agent_web, batch_agent, analyse_web, similarity, tool_web
from streamlit_option_menu import option_menu
import streamlit as st
st.set_page_config(layout="wide", page_title='XAgent')

pages = {
    "Agent问答": {
        "icon": "chat",
        "page": agent_web,
    },
    "批量问答": {
        "icon": "hdd-stack",
        "page": batch_agent,
    },
    "知识库管理": {
        "icon": "hdd-stack",
        "page": kb_web,
    },
    "工具管理": {
        "icon": "hdd-stack",
        "page": tool_web,
    },
    "问题分析": {
        "icon": "hdd-stack",
        "page": analyse_web,
    },
    "相似度排序": {
        "icon": "hdd-stack",
        "page": similarity,
    },
}
options = list(pages)
icons = [x["icon"] for x in pages.values()]

default_index = 0
selected_page = option_menu(
    "",
    orientation="horizontal",
    options=options,
    menu_icon="chat-quote",
    default_index=default_index,
)

if selected_page in pages:
    pages[selected_page]["page"].load_view()
