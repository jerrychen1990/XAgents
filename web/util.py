#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@Time    :   2023/12/15 14:50:21
@Author  :   ChenHao
@Contact :   jerrychen1990@gmail.com
'''

from xagents.config import TEMP_DIR
from xagents.kb.service import get_knowledge_base, list_knowledge_base_names
from web.config import *
from xagents.model.service import list_llm_models, list_llm_versions
from snippets import *
from xagents.tool.service import list_tools
from xagents.util import get_log
from streamlit.delta_generator import DeltaGenerator
logger = get_log(__name__)


def get_default_idx(options, default_value):
    try:
        return options.index(default_value)
    except Exception:
        return 0


def load_kb_options(st: DeltaGenerator, default_use_kb=True):
    chat_kwargs = dict()
    use_kb = st.checkbox('使用知识库', value=default_use_kb)
    kb_name, kb_prompt_template = None, None

    if use_kb:
        kb_names = list_knowledge_base_names()
        kb_name = st.selectbox('选择知识库', kb_names, index=get_default_idx(kb_names, DEFAULT_KB))
        if kb_name:
            kb = get_knowledge_base(kb_name)

            filter_files = st.checkbox("筛选知识库文件", value=False)
            if filter_files:
                kb_files = kb.list_files()
                kb_files = [e.file_name for e in kb_files]
                file_names: List[str] = st.multiselect('选择知识库文件', kb_files)
                chat_kwargs.update(file_names=file_names)

            rerank_config = dict()
            use_rerank = st.checkbox("模型重排序",value=False)
            if use_rerank:
                rerank_url =st.text_input("rerank模型地址", "http://36.103.177.140:8000/get_rel_score")
                rerank_config.update(url=rerank_url,model_cls="ZhipuReranker")


            top_k = st.number_input('召回数', value=DEFAULT_TOP_K, min_value=1, max_value=10, step=1)
            score_threshold = st.number_input('阈值', value=DEFAULT_THRESHOLD, min_value=0.0, max_value=1.0)
            do_expand = st.checkbox('上下文扩展', value=True)
            kb_prompt_template = st.text_area('prompt模板', value=kb.prompt_template, height=150)
            do_split_query = st.checkbox('查询语句分句', value=True)
            chat_kwargs.update(top_k=top_k, do_expand=do_expand, do_split_query=do_split_query, rerank_config=rerank_config)

            if do_expand:
                expand_len = st.number_input('扩展长度', value=DEFAULT_EXPAND_LEN, min_value=1, max_value=2000, step=1)
                forward_rate = st.slider('向下扩展比例', value=DEFAULT_FORWARD_RATE, min_value=0.0, max_value=1., step=0.01)

                chat_kwargs.update(expand_len=expand_len, forward_rate=forward_rate, score_threshold=score_threshold)
    return use_kb, kb_name, kb_prompt_template, chat_kwargs


def load_model_options(st:DeltaGenerator):
    models = list_llm_models()

    model = st.selectbox('选择模型类型', models, index=get_default_idx(models, DEFAULT_MODEL))
    versions = list_llm_versions(model)
    version = st.selectbox('选择模型版本', versions, index=0)
    temperature = st.number_input('设置温度', value=DEFAULT_TEMPERATURE, min_value=0.01, max_value=1.0, step=0.01)

    chat_kwargs = dict(temperature=temperature)
    return model, version, chat_kwargs

def load_tool_options(st:DeltaGenerator):
    use_tool = st.checkbox('使用工具', value=False)
    tools = []
    if use_tool:
        all_tools =  list_tools()
        # default = get_tool(DEFAULT_TOOL)
        
        tools = st.multiselect(label="工具包", options=all_tools, default= None, format_func=lambda x: x.name)
    return tools    


def show_save_button(st, file_name, records, keep_name=True, **kwargs):
    stem, surfix = os.path.splitext(file_name)
    if keep_name:
        dst_file_name = file_name

    else:
        dst_file_name = f"{stem}_download{surfix}"
    dst_file_path = f"{TEMP_DIR}/{dst_file_name}"
    logger.info(f"writing file to {dst_file_path}")
    dump_list(records, dst_file_path)
    with open(dst_file_path, "rb") as f:
        byte_content = f.read()
        st.download_button(label="下载文件", key=dst_file_path, data=byte_content,
                           file_name=dst_file_name, mime="application/octet-stream", **kwargs)


def show_upload_table(st, label="上传文件，xlsx,csv类型"):
    uploaded_file = st.file_uploader(
        label=label, type=["xlsx", "csv"])
    if uploaded_file:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        elif uploaded_file.name.endswith(".xlsx"):
            df = pd.read_excel(uploaded_file)
        df.fillna("", inplace=True)
        records = df.to_dict(orient="records")
        columns = list(records[0].keys())
        return uploaded_file, records, columns
    return uploaded_file, None, None
