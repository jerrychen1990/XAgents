#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@Time    :   2023/12/12 18:53:53
@Author  :   ChenHao
@Contact :   jerrychen1990@gmail.com
'''
import datetime
import time
import streamlit as st
import pandas as pd
from snippets import dump_list, batch_process, jdumps
from web.util import load_kb_options, load_model_options
from xagents.config import *
from xagents.agent.core import AgentResp
from xagents.agent.xagent import XAgent
from xagents.util import get_log
from web.config import *

logger = get_log(__name__)


def load_upload_table(label="上传文件，xlsx,csv类型"):
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


def load_view():

    surfix = ""
    # surfix = st.text_input(label="字段后缀", value="")
    model, version, chat_kwargs = load_model_options(st.sidebar)
    use_kb, kb_name, kb_prompt_template, _chat_kwargs = load_kb_options(st.sidebar, default_use_kb=True)
    chat_kwargs.update(**_chat_kwargs)

    work_num = st.sidebar.number_input(
        key="work_num", label="并发数", min_value=1, max_value=10, value=1, step=1)

    uploaded_file, records, columns = load_upload_table()

    def get_resp_func(item):
        prompt = item["question"]
        _kb_name = item.get("kb_name", kb_name)
        llm_config = dict(model_cls=model, name=model, version=version)
        memory_config = dict(size=10)

        agent = XAgent(name="tmp_batch_agent", llm_config=llm_config,
                       memory_config=memory_config, kb_name=_kb_name,
                       kb_prompt_template=kb_prompt_template)
        resp: AgentResp = agent.chat(message=prompt, stream=False, do_remember=False, use_kb=use_kb, **chat_kwargs)

        item[f"answer_{surfix}" if surfix else "answer"] = resp.message
        item[f"recall_{surfix}" if surfix else "recall"] = jdumps(resp.references)

        rt = dict(question=item['question'], answer=resp.message)
        if "gold_answer" in item:
            rt.update(gold_answer=item["gold_answer"])
        return rt

    submit = st.button(label="提交")
    if submit:
        load_batch_view(get_resp_func=get_resp_func, records=records, columns=columns, file_name=uploaded_file.name,
                        workers=work_num, require_keys=["question", "kb_name"])


def load_batch_view(get_resp_func, records, columns, file_name,
                    workers=1, max_num=100, require_keys=None):
    # 保存文件函数
    def save_file():
        dst_file_name = f"{stem}_{idx}_{len(records)}_{datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S.%f')}.{surfix}"
        dst_file_path = f"{TEMP_DIR}/{dst_file_name}"
        logger.info(f"writing file to {dst_file_path}")
        dump_list(records, dst_file_path)
        with open(dst_file_path, "rb") as f:
            byte_content = f.read()
            st.download_button(label="下载文件", key=dst_file_name, data=byte_content,
                               file_name=dst_file_name, mime="application/octet-stream")

    # 校验数据
    start = time.time()
    if not records:
        st.toast("尚未上传文件!")
        return
    if require_keys:
        lack_keys = set(require_keys) - set(columns)
        if lack_keys:
            lack_info = "|".join(lack_keys)
            st.toast(f"{lack_info}列缺失!")
            return
    if len(records) > max_num:
        st.toast(f"一次最多上传{max_num}条数据!")
        return

    batch_func = batch_process(workers)(get_resp_func)
    stem, surfix = file_name.split(".")
    idx = 0
    results = batch_func(records[idx:])

    # progress_detail = st.empty()
    for item in results:
        # item = results[idx]
        idx += 1
        cost = time.time() - start
        cost_per_item = cost/idx
        pct = (idx)/len(records)
        remain = cost_per_item * (len(records)-idx)
        text = f"[进度:{pct:.2%} {idx}/{len(records)}][平均{cost_per_item:.2f}秒/条][耗时{cost:.2f}秒][剩余{remain:.2f}秒]"
        st.progress(value=pct, text=text)
        # st.info(f"question:{item['question']}")
        for k, v in item.items():
            st.info(f"{k}:{v}")

    save_file()
    st.markdown("任务完成")
