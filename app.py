
#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@Time    :   2023/12/14 15:53:37
@Author  :   ChenHao
@Contact :   jerrychen1990@gmail.com
'''


from web import kb_web, agent_web, batch_agent, analyse_web, similarity
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
    icons=icons,
    menu_icon="chat-quote",
    default_index=default_index,
)

if selected_page in pages:
    pages[selected_page]["page"].load_view()


# _VIEWS = [agent_web, batch_agent, kb_web, analyse_web, similarity, test_web]
# _VIEW_MAP = {e.__name__: e for e in _VIEWS}


# NAVBAR_PATHS = {
#     "Agent问答": "web.agent_web",
#     "批量测评": "web.batch_agent",
#     "知识库管理": "web.kb_web",
#     "结果分析": "web.analyse_web",
#     "相似度计算": "web.similarity",
#     "测试页面": "web.test_web",
# }


# SETTINGS = {
#     'OPTIONS': 'options',
#     'CONFIGURATION': 'configuration'
# }


# def inject_custom_css():
#     with open('web/styles.css') as f:
#         st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)


# def get_current_route():
#     try:
#         return st.experimental_get_query_params()['nav'][0]
#     except:
#         return "web.agent_web"


# def navbar_component():
#     navbar_items = ''
#     for key, value in NAVBAR_PATHS.items():
#         navbar_items += (
#             f'<a class="navitem"  target="_self" href="/?nav={value}">{key}</a>')
#     component = rf'''
#             <nav class="container navbar" id="navbar">
#                 <ul class="navlist">
#                 {navbar_items}
#                 </ul>
#             </nav>
#             '''
#     st.markdown(component, unsafe_allow_html=True)


# inject_custom_css()
# navbar_component()


# def navigation():
#     route = get_current_route()
#     view = _VIEW_MAP[route]
#     view.load_view()


# navigation()
