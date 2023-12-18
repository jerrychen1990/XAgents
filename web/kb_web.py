#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@Time    :   2023/12/12 11:30:58
@Author  :   ChenHao
@Contact :   jerrychen1990@gmail.com
'''
import os
import streamlit as st
from web.util import get_default_idx
from xagents.config import TEMP_DIR
from xagents.kb.core import KnwoledgeBase

from xagents.kb.service import create_knowledge_base, get_knowledge_base, list_knowledge_base_names, list_spliters, list_valid_exts, list_vecstores, list_distance_strategy
from xagents.kb.splitter import get_splitter
from xagents.model.service import list_embd_models

from web.config import *


def new_kb_page(kb_names, vs_names, embd_names, distance_strategys):
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
            index=get_default_idx(vs_names, DEFAULT_VS_TYPE),
            key="vs_type",
        )
        vs_config = _get_vs_config(vs_cls=vs_type, kb_name=kb_name)

        embd_model = embd_col.selectbox(
            "向量模型",
            embd_names,
            index=get_default_idx(embd_names, DEFAULT_EMBD_MODEL),
            key="embd_model",
        )

        distance_strategy = distance_col.selectbox(
            "距离度量",
            distance_strategys,
            index=get_default_idx(distance_strategys, DEFAULT_DISTANCE_STRATEGY),
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
            dict(model_cls="ZhipuEmbedding", batch_size=32, norm=True)
            embedding_config = dict(
                model_cls=embd_model,
            )
            create_knowledge_base(name=kb_name, desc=kb_desc, vecstore_config=vs_config,
                                  embedding_config=embedding_config, distance_strategy=distance_strategy)
            msg = f"创建知识库{kb_name}成功"
            st.toast(msg)
            st.info(msg)
            st.rerun()


def _get_vs_config(vs_cls, kb_name):
    conf = dict(vs_cls=vs_cls)
    if vs_cls == "XES":
        conf.update(es_url="http://localhost:9200", index_name=f"{kb_name}_index")
    return conf


def show_knowledge_base(kb_name: str):
    kb = get_knowledge_base(name=kb_name)
    # 上传文件
    st.text_area("请输入知识库介绍:", value=kb.description, max_chars=None, key=None,
                 help=None, on_change=None, args=None, kwargs=None)
    files = st.file_uploader("上传知识文件：",
                             list_valid_exts(),
                             accept_multiple_files=True,
                             )

    # with st.sidebar:
    with st.expander(
            "文件处理配置",
            expanded=True,
    ):
        cols = st.columns(3)
        # 分词器
        splitters = list_spliters()
        splitter = cols[0].selectbox(label="分段器", options=splitters, index=get_default_idx(splitters, DEFAULT_SPLITTER))
        # 切分词
        cutter = cols[1].text_input(label="切分词,正则表达式", value=DEFAULT_CUTTER)
        # 是否处理表格
        cols[2].write("")
        cols[2].write("")
        parse_table = cols[2].checkbox("是否处理表格", DEFAULT_PARSE_TABLE)

    if st.button(
            "添加文件到知识库",
            # use_container_width=True,
            disabled=len(files) == 0,
    ):
        splitter_config = dict(spliter_cls=splitter, parse_table=parse_table, splitter=cutter)
        splitter = get_splitter(splitter_config)
        with st.spinner("添加文件中，勿刷新或关闭页面。"):
            for file in files:
                st.info(f"adding {file.name}...")
                tmp_file_path = os.path.join(TEMP_DIR, "files", f"{file.name}")
                os.makedirs(os.path.dirname(tmp_file_path), exist_ok=True)
                with open(tmp_file_path, "wb") as f:
                    f.write(file.getvalue())
                kb.add_file(tmp_file_path, splitter=splitter)
                msg = f"添加知识库文件{file.name} success!"
                st.toast(msg)
    st.divider()
    return kb


def rebuild_and_delete(kb: KnwoledgeBase):
    rebuild, _, delete = st.columns(3)

    if rebuild.button(
            "重新构建向量索引",
            # help="无需上传文件，通过其它方式将文档拷贝到对应知识库content目录下，点击本按钮即可重建知识库。",
            use_container_width=True,
    ):
        with st.spinner("向量库重构中，请耐心等待，勿刷新或关闭页面。"):
            empty = st.empty()
            empty.progress(0.0, "")
            kb.rebuild()
            st.rerun()

    if delete.button(
            "删除知识库",
            use_container_width=True,
            type="primary"

    ):
        kb.delete()
        st.info(f"删除{kb.name}成功!")
        st.rerun()


def load_view():
    kb_names = list_knowledge_base_names()
    vs_names = list_vecstores()
    embd_names = list_embd_models()
    distance_strategys = list_distance_strategy()

    selected_kb = st.sidebar.selectbox(
        "请选择或新建知识库：",
        kb_names + ["新建知识库"],
        index=0
    )

    if selected_kb == "新建知识库":
        new_kb_page(kb_names, vs_names, embd_names, distance_strategys)
    else:
        kb = show_knowledge_base(selected_kb)
        rebuild_and_delete(kb)
