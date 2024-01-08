#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@Time    :   2023/12/14 15:50:39
@Author  :   ChenHao
@Contact :   jerrychen1990@gmail.com
'''


import streamlit as st
from web.util import load_model_options, load_kb_options, load_tool_options
from xagents.agent.core import AgentResp
from xagents.agent.xagent import XAgent

from xagents.util import get_log
from web.config import *

logger = get_log(__name__)


def load_view():
    model, version, chat_kwargs = load_model_options(st.sidebar)
    use_kb, kb_name, kb_prompt_template, _chat_kwargs = load_kb_options(st.sidebar, default_use_kb=True)
    tools = load_tool_options(st.sidebar)
    
    fake_chat = st.sidebar.checkbox(label="fake_chat", value=False)

    chat_kwargs.update(**_chat_kwargs, fake_chat=fake_chat)

    def get_agent():
        agent = st.session_state.get("agent")
        if True:
            agent = XAgent(name="tmp_agent",
                           memory_config=dict(size=10),
                           tools=tools,
                           llm_config=dict(model_cls=model, name=model, version=version),
                           kb_prompt_template=kb_prompt_template,
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
            tool_call_placeholder = st.empty()


            full_response = ""
        resp: AgentResp = agent.chat(message=message, use_kb=use_kb, do_remember=False, **chat_kwargs)
        for token in resp.content:
            full_response += token
            message_placeholder.markdown(full_response + "▌")
        message_placeholder.markdown(full_response)
        
        # logger.debug(f"{resp=}")
        
        
        if resp.references:
            # logger.debug("adding chunks info")
            st.markdown("参考信息")

            # 展示参考信息
            for idx, chunk in enumerate(resp.references):
                chunk_text = chunk.to_detail_text(with_context=False)
                st.markdown(f"[{idx+1}]  {chunk_text}")
                with st.expander(f"展示上下文", expanded=False):
                    plain_text = chunk.to_plain_text()
                    st.text(plain_text)
                    
        # 展示工具使用
        if resp.tool_call:
            tool_call_placeholder.markdown(resp.tool_call.to_markdown())
            

        st.session_state.messages.append(
            {"role": "user", "content": message})
        st.session_state.messages.append(
            {"role": "assistant", "content": full_response})
