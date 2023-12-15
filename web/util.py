#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@Time    :   2023/12/15 14:50:21
@Author  :   ChenHao
@Contact :   jerrychen1990@gmail.com
'''

from xagents.kb.service import list_knowledge_base_names
from web.config import *
from xagents.model.service import list_llm_models, list_llm_versions


def get_default_idx(options, default_value):
    try:
        return options.index(default_value)
    except Exception:
        return 0


def load_kb_options(st, default_use_kb=True):
    chat_kwargs = dict()
    use_kb = st.checkbox('使用知识库', value=default_use_kb)
    kb_name, kb_prompt_template = None, None

    if use_kb:
        kb_names = list_knowledge_base_names()
        kb_name = st.selectbox('选择知识库', kb_names, index=get_default_idx(kb_names, DEFAULT_KB))
        top_k = st.number_input('召回数', value=DEFAULT_TOP_K, min_value=1, max_value=10, step=1)
        do_expand = st.checkbox('上下文扩展', value=True)
        kb_prompt_template = st.text_area('prompt模板', value=DEFAULT_KB_PROMPT_TEMPLATE, height=150)
        do_split_query = st.checkbox('查询语句分句', value=True)
        chat_kwargs.update(top_k=top_k, do_expand=do_expand, do_split_query=do_split_query)

        if do_expand:
            expand_len = st.number_input('扩展长度', value=DEFAULT_EXPAND_LEN, min_value=1, max_value=2000, step=1)
            forward_rate = st.slider('向下扩展比例', value=DEFAULT_FORWARD_RATE, min_value=0.0, max_value=1., step=0.01)

            chat_kwargs.update(expand_len=expand_len, forward_rate=forward_rate)
    return use_kb, kb_name, kb_prompt_template, chat_kwargs


def load_model_options(st):
    models = list_llm_models()

    model = st.selectbox('选择模型类型', models, index=get_default_idx(models, DEFAULT_MODEL))
    versions = list_llm_versions(model)
    version = st.selectbox('选择模型版本', versions, index=0)
    temperature = st.number_input('设置温度', value=DEFAULT_TEMPERATURE, min_value=0.01, max_value=1.0, step=0.01)

    chat_kwargs = dict(temperature=temperature)
    return model, version, chat_kwargs
