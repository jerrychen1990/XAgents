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

from xagents.kb.service import create_knowledge_base, get_knowledge_base, list_knowledge_base_names, list_valid_exts, list_vecstores, list_distance_strategy
from xagents.kb.splitter import get_splitter
from xagents.model.service import list_embd_models
from stqdm import stqdm


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


def knowledge_base_info_page(kb: KnwoledgeBase):
    with st.form(f"{kb.name} 信息"):
        st.write(f"{kb.name}详细信息")
        kb_name = kb.name
        prompt_template = st.text_area("prompt模板", kb.prompt_template, height=150)
        kb_infos = kb.list_kb_file_info()

        # doc_details = pd.DataFrame(get_kb_file_details(kb))
        if not len(kb_infos):
            st.info(f"知识库 `{kb_name}` 中暂无文件")
        else:
            st.write(f"知识库 `{kb_name}` 中已有文件:")
            # st.info("知识库中包含源文件与向量库，请从下表中选择文件后操作")
            # doc_details.drop(columns=["kb_name"], inplace=True)
            # doc_details = doc_details[[
            #     "No", "file_name", "document_loader", "text_splitter", "docs_count", "in_folder", "in_db",
            # ]]
            # doc_details["in_folder"] = doc_details["in_folder"].replace(True, "✓").replace(False, "×")
            # doc_details["in_db"] = doc_details["in_db"].replace(True, "✓").replace(False, "×")
            # gb = config_aggrid(
            #     doc_details,
            #     {
            #         ("No", "序号"): {},
            #         ("file_name", "文档名称"): {},
            #         # ("file_ext", "文档类型"): {},
            #         # ("file_version", "文档版本"): {},
            #         ("document_loader", "文档加载器"): {},
            #         ("docs_count", "文档数量"): {},
            #         ("text_splitter", "分词器"): {},
            #         # ("create_time", "创建时间"): {},
            #         ("in_folder", "源文件"): {"cellRenderer": cell_renderer},
            #         ("in_db", "向量库"): {"cellRenderer": cell_renderer},
            #     },
            #     "multiple",
            # )

            # doc_grid = AgGrid(
            #     doc_details,
            #     gb.build(),
            #     columns_auto_size_mode="FIT_CONTENTS",
            #     theme="alpine",
            #     custom_css={
            #         "#gridToolBar": {"display": "none"},
            #     },
            #     allow_unsafe_jscode=True,
            #     enable_enterprise_modules=False
            # )

            # selected_rows = doc_grid.get("selected_rows", [])

            # cols = st.columns(4)
            # file_name, file_path = file_exists(kb, selected_rows)
            # if file_path:
            #     with open(file_path, "rb") as fp:
            #         cols[0].download_button(
            #             "下载选中文档",
            #             fp,
            #             file_name=file_name,
            #             use_container_width=True, )
            # else:
            #     cols[0].download_button(
            #         "下载选中文档",
            #         "",
            #         disabled=True,
            #         use_container_width=True, )

            st.info(kb_infos)

        if st.form_submit_button("更新"):
            kb.prompt_template = prompt_template
            kb.save()
            st.toast("prompt updated!")

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
