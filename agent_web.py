#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@Time    :   2023/12/07 18:16:13
@Author  :   ChenHao
@Contact :   jerrychen1990@gmail.com
'''

import streamlit as st
from xagents.agent.core import AgentResp
from xagents.agent.xagent import XAgent
from xagents.kb.service import list_knowledge_base_names

from xagents.model import list_llm_models
from xagents.util import get_log

logger = get_log(__name__)

DEFAULT_MODEL = "GLM"
DEFAULT_KB = "guizhoumaotai"
DEFAULT_TEMPERATURE = 0.01
DEFAULT_TOP_K = 3
DEFAULT_EXPAND_LEN = 500
DEFAULT_FORWARD_RATE = 0.5

models = list_llm_models()
model = st.sidebar.selectbox('选择模型类型', models, index=models.index(DEFAULT_MODEL))

versions = ["chatglm_66b", "chatglm_turbo"]
version = st.sidebar.selectbox('选择模型版本', versions, index=0)
temperature = st.sidebar.number_input('设置温度', value=DEFAULT_TEMPERATURE, min_value=0.01, max_value=1.0, step=0.01)


use_kb = st.sidebar.checkbox('使用知识库', value=True)

chat_kwargs = dict(temperature=temperature)

if use_kb:
    kb_names = list_knowledge_base_names()
    kb_name = st.sidebar.selectbox('选择知识库', kb_names, index=kb_names.index(DEFAULT_KB))
    top_k = st.sidebar.number_input('召回数', value=DEFAULT_TOP_K, min_value=1, max_value=10, step=1)
    expand_len = st.sidebar.number_input('扩展长度', value=DEFAULT_EXPAND_LEN, min_value=1, max_value=2000, step=1)
    forward_rate = st.sidebar.slider('向下扩展比例', value=DEFAULT_FORWARD_RATE, min_value=0.0, max_value=1., step=0.01)

    chat_kwargs.update(top_k=top_k, expand_len=expand_len, forward_rate=forward_rate)


else:
    kb_name = None


def get_agent():
    agent = st.session_state.get("agent")
    if not agent:
        agent = XAgent(name="tmp_agent",
                       memory_config=dict(size=10),
                       llm_config=dict(model_cls=model, name=model, version=version),
                       kb_name=kb_name)
        st.session_state.agent = agent
    return agent


def init():
    if "messages" not in st.session_state:
        st.session_state.messages = []


agent = get_agent()
init()

clear = st.sidebar.button("清空历史")
if clear or True:
    agent.clear_memory()
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if message := st.chat_input("你好，你是谁？"):
    with st.chat_message("user"):
        st.markdown(message)
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        reference_placeholder = st.empty()

        full_response = ""
    resp: AgentResp = agent.chat(message=message, use_kb=use_kb, do_expand=True, **chat_kwargs)
    for token in resp.message:
        full_response += token
        message_placeholder.markdown(full_response + "▌")
    message_placeholder.markdown(full_response)
    if resp.references:
        logger.debug("adding chunks info")
        with reference_placeholder.expander("参考信息", expanded=False):
            references = [f"[{idx+1}]  {chunk.to_detail_text()}" for idx, chunk in enumerate(resp.references)]
            references = "\n\n--------\n\n".join(references)
            st.markdown(references)

    st.session_state.messages.append(
        {"role": "user", "content": message})
    st.session_state.messages.append(
        {"role": "assistant", "content": full_response})
