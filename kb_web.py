#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@Time    :   2023/12/12 11:30:58
@Author  :   ChenHao
@Contact :   jerrychen1990@gmail.com
'''
import streamlit as st

from xagents.kb.service import list_knowledge_base_names, list_vecstores, list_distance_strategy
from xagents.model.service import list_embd_models

DEFAULT_VS_TYPE = "FAISS"
DEFAULT_EMBD_MODEL = "ZhipuEmbedding"
DEFAULT_DISTANCE_STRATEGY = "MAX_INNER_PRODUCT"

kb_names = list_knowledge_base_names()
vs_names = list_vecstores()
embd_names = list_embd_models()
distance_strategys = list_distance_strategy()


selected_kb = st.selectbox(
    "请选择或新建知识库：",
    kb_names + ["新建知识库"],
    index=0
)


def new_kb_page():
    with st.form("新建知识库"):

        kb_name = st.text_input(
            "新建知识库名称",
            placeholder="新知识库名称，不支持中文命名",
            key="kb_name",
        )
        kb_desc = st.text_input(
            "知识库简介",
            placeholder="知识库简介，方便Agent查找",
            key="kb_info",
        )

        vec_col, embd_col, distance_col = st.columns(3)

        vs_type = vec_col.selectbox(
            "向量库类型",
            vs_names,
            index=vs_names.index(DEFAULT_VS_TYPE),
            key="vs_type",
        )

        embd_model = embd_col.selectbox(
            "向量模型",
            embd_names,
            index=embd_names.index(DEFAULT_EMBD_MODEL),
            key="embd_model",
        )

        distance_strategy = distance_col.selectbox(
            "距离度量",
            distance_strategys,
            index=distance_strategys.index(DEFAULT_DISTANCE_STRATEGY),
            key="distance_strategy",
        )
        submit_create_kb = st.form_submit_button(
            "新建",
            # disabled=not bool(kb_name),
            use_container_width=True,
        )

    if submit_create_kb:
        st.info("creating kb")
        if not kb_name or not kb_name.strip():
            st.error(f"知识库名称不能为空！")
        elif kb_name in kb_names:
            st.error(f"名为 {kb_name} 的知识库已经存在！")
        else:
            st.info("创建成功")
            st.rerun()


if selected_kb == "新建知识库":
    new_kb_page()
