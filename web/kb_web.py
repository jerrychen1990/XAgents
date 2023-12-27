#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@Time    :   2023/12/12 11:30:58
@Author  :   ChenHao
@Contact :   jerrychen1990@gmail.com
'''
from st_aggrid import JsCode, AgGrid

# from test import show
import os
from typing import Literal, Tuple, Dict
import streamlit as st
import pandas as pd
from web.util import get_default_idx
from xagents.config import TEMP_DIR
from xagents.kb.core import KnwoledgeBase
from xagents.model.service import list_embd_models

from xagents.kb.service import create_knowledge_base, get_knowledge_base, list_distance_strategy, list_knowledge_base_names, list_valid_exts, list_vecstores
from xagents.kb.splitter import get_splitter
from stqdm import stqdm
from st_aggrid.grid_options_builder import GridOptionsBuilder


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
            st.session_state.cur_kb = kb_name
            st.rerun()


def _get_vs_config(vs_cls, kb_name):
    conf = dict(vs_cls=vs_cls)
    if vs_cls == "XES":
        conf.update(es_url="http://localhost:9200", index_name=f"{kb_name}_index")
    return conf


def add_kb_file_page(kb: KnwoledgeBase):
    files = st.file_uploader("上传知识文件：",
                             list_valid_exts(),
                             accept_multiple_files=True,
                             )

    # with st.sidebar:
    with st.expander(
            "文件处理配置",
            expanded=True,
    ):
        cols = st.columns(4)
        # 分词器
        # splitters = list_spliters()
        # splitter = cols[0].selectbox(label="分段器", options=splitters, index=get_default_idx(splitters, DEFAULT_SPLITTER))
        splitter = DEFAULT_SPLITTER
        # 切分词
        cutter = cols[0].text_input(label="切分词,正则表达式", value=DEFAULT_CUTTER)
        min_len = cols[1].number_input(label="最小词长", min_value=1, max_value=500, value=DEFAULT_MIN_LEN)
        max_len = cols[2].number_input(label="最大词长", min_value=1, max_value=500, value=DEFAULT_MAX_LEN)

        # 是否处理表格
        cols[3].write("")
        cols[3].write("")
        parse_table = cols[3].checkbox("是否处理表格", DEFAULT_PARSE_TABLE)

    if st.button(
            "添加文件到知识库",
            # use_container_width=True,
            disabled=len(files) == 0,
    ):
        splitter_config = dict(spliter_cls=splitter, min_len=min_len, max_len=max_len, parse_table=parse_table, splitter=cutter)
        splitter = get_splitter(splitter_config)
        with st.spinner("添加文件中，勿刷新或关闭页面。"):
            for file in stqdm(files):
                st.info(f"adding {file.name}...")
                tmp_file_path = os.path.join(TEMP_DIR, "files", f"{file.name}")
                os.makedirs(os.path.dirname(tmp_file_path), exist_ok=True)
                with open(tmp_file_path, "wb") as f:
                    f.write(file.getvalue())
                kb.add_file(tmp_file_path, splitter=splitter)
                msg = f"添加知识库文件{file.name} success!"
                st.toast(msg)
    st.divider()


cell_renderer = JsCode("""function(params) {if(params.value==true){return '✓'}else{return '×'}}""")


def config_aggrid(
        df: pd.DataFrame,
        columns: Dict[Tuple[str, str], Dict] = {},
        selection_mode: Literal["single", "multiple", "disabled"] = "single",
        use_checkbox: bool = False,
) -> GridOptionsBuilder:
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_column("No", width=40)
    for (col, header), kw in columns.items():
        gb.configure_column(col, header, wrapHeaderText=True, **kw)
    gb.configure_selection(
        selection_mode=selection_mode,
        use_checkbox=use_checkbox,
        # pre_selected_rows=st.session_state.get("selected_rows", [0]),
    )
    return gb


# def file_exists(kb: str, selected_rows: List) -> Tuple[str, str]:
#     '''
#     check whether a doc file exists in local knowledge base folder.
#     return the file's name and path if it exists.
#     '''
#     if selected_rows:
#         file_name = selected_rows[0]["file_name"]
#         file_path = get_file_content_path(kb, file_name)
#         if os.path.isfile(file_path):
#             return file_name, file_path
#     return "", ""


def knowledge_base_info_page(kb: KnwoledgeBase):
    with st.form(f"{kb.name} 信息"):
        st.write(f"{kb.name}详细信息")
        kb_name = kb.name
        prompt_template = st.text_area("prompt模板", kb.prompt_template, height=150)

        if st.form_submit_button("更新"):
            kb.prompt_template = prompt_template
            kb.save()
            st.toast("prompt updated!")

    kb_infos = kb.list_kb_file_info()
    kb_info_df = pd.DataFrame.from_records(kb_infos)
    if not len(kb_infos):
        st.info(f"知识库 `{kb_name}` 中暂无文件")
    else:
        st.write(f"知识库 `{kb_name}` 中已有文件:")
        st.info("知识库中包含源文件与向量库，请从下表中选择文件后操作")

        gb = config_aggrid(
            kb_info_df,
            {
                ("No", "序号"): {},
                ("file_name", "文档名称"): {},
                ("loader", "文档加载器"): {},
                ("chunk_len", "切片数量"): {},
            },
            "single",
        )

        doc_grid = AgGrid(
            kb_info_df,
            gb.build(),
            columns_auto_size_mode="FIT_CONTENTS",
            theme="streamlit",
            custom_css={
                "#gridToolBar": {"display": "none"},
            },
            allow_unsafe_jscode=True,
            enable_enterprise_modules=False
        )

        st.write()
        selected_rows = doc_grid.get("selected_rows", [])
        if selected_rows:
            selected_row = selected_rows[0]

            cols = st.columns(4)

            origin_file_path = selected_row.get("origin_file_path")
            if origin_file_path:
                with open(origin_file_path, "r") as f:
                    cols[0].download_button(
                        "下载选中原始文档",
                        "",
                        disabled=False,
                        use_container_width=True
                    )
            chunk_path = selected_row.get("chunk_path")
            if chunk_path:
                with open(chunk_path, "r") as f:
                    cols[1].download_button(
                        "下载选中切片",
                        "",
                        disabled=False,
                        use_container_width=True
                    )
    st.divider()


def control_kb_page(kb: KnwoledgeBase):
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


def init():
    if "cur_kb" not in st.session_state:
        st.session_state.cur_kb = DEFAULT_KB


def load_view():

    kb_names = list_knowledge_base_names()
    vs_names = list_vecstores()
    embd_names = list_embd_models()
    distance_strategys = list_distance_strategy()
    init()

    default_kb_idx = get_default_idx(kb_names, st.session_state.cur_kb)
    selected_kb = st.sidebar.selectbox(
        "请选择或新建知识库：",
        kb_names + ["新建知识库"],
        index=default_kb_idx
    )

    if selected_kb == "新建知识库":
        new_kb_page(kb_names, vs_names, embd_names, distance_strategys)
    else:
        kb = get_knowledge_base(name=selected_kb)
        add_kb_file_page(kb)
        knowledge_base_info_page(kb)
        control_kb_page(kb)
