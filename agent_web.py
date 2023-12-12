#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@Time    :   2023/12/07 18:16:13
@Author  :   ChenHao
@Contact :   jerrychen1990@gmail.com
'''

import streamlit as st
from xagents.agent.xagent import XAgent

from xagents.model import list_llm_models


models = list_llm_models()

model = st.sidebar.selectbox('Select a model', models)

versions = ["chatglm_turbo"]

version = st.sidebar.selectbox('Select a version', versions)


def get_agent():
    agent = st.session_state.get("agent")
    if not agent:
        agent = XAgent(name="tmp_agent", llm_config=dict(model_cls=model, name=model, version=version))
        st.session_state.agent = agent
    return agent


def init():
    if "messages" not in st.session_state:
        st.session_state.messages = []


agent = get_agent()
init()

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if message := st.chat_input("你好，你是谁？"):
    with st.chat_message("user"):
        st.markdown(message)
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
    resp = agent.chat(message=message)
    for token in resp:
        full_response += token
        message_placeholder.markdown(full_response + "▌")
    message_placeholder.markdown(full_response)
    st.session_state.messages.append(
        {"role": "user", "content": message})
    st.session_state.messages.append(
        {"role": "assistant", "content": full_response})
