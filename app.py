
#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@Time    :   2023/12/14 15:53:37
@Author  :   ChenHao
@Contact :   jerrychen1990@gmail.com
'''


import streamlit as st
from web import agent_web, analyse_web, batch_agent

st.set_page_config(layout="wide", page_title='AI工具集合')

_VIEWS = [agent_web, analyse_web, batch_agent]
_VIEW_MAP = {e.__name__: e for e in _VIEWS}


NAVBAR_PATHS = {
    "Agent对话": "web.agent_web",
    "结果分析": "web.analyse_web",
    "批量测评": "web.batch_agent"
}


SETTINGS = {
    'OPTIONS': 'options',
    'CONFIGURATION': 'configuration'
}


def inject_custom_css():
    with open('web/styles.css') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)


def get_current_route():
    try:
        return st.experimental_get_query_params()['nav'][0]
    except:
        return "web.agent_web"


def navbar_component():
    navbar_items = ''
    for key, value in NAVBAR_PATHS.items():
        navbar_items += (
            f'<a class="navitem"  target="_self" href="/?nav={value}">{key}</a>')
    component = rf'''
            <nav class="container navbar" id="navbar">
                <ul class="navlist">
                {navbar_items}
                </ul>
            </nav>
            '''
    st.markdown(component, unsafe_allow_html=True)


inject_custom_css()
navbar_component()


def navigation():
    route = get_current_route()
    view = _VIEW_MAP[route]
    view.load_view()


navigation()
