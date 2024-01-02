#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@Time    :   2023/11/27 16:44:57
@Author  :   ChenHao
@Contact :   jerrychen1990@gmail.com
'''

import streamlit as st
from web.util import get_default_idx, show_save_button, show_upload_table
from xagents.kb.common import RecalledChunk
from xagents.util import get_log
from snippets import *

analyse_labels = ["其他", "召回错误", "模型幻觉", "计算错误", "回答不完整", "指令理解错误"]
qustion_labels = ["其他", "简单查询", "段落统计", "指标计算"]


logger = get_log(__name__)


def fmt_func(v):
    m = {0: "完全错误", 0.5: "部分正确", 1: "完全正确"}
    return m[v]


def get_recall_str(item, key):
    if not item.get(key, None):
        return ""
    recall = eval(item[key])
    chunks = [RecalledChunk(**e) for e in recall]
    return "\n".join(e.to_detail_text(with_context=True, max_len=100) for e in chunks)


def on_next():
    logger.info("on next")
    st.session_state.cur_idx += 1
    logger.info(f"cur_idx = {st.session_state.cur_idx}")


def on_previous():
    logger.info("on previous")
    st.session_state.cur_idx -= 1
    logger.info(f"cur_idx = {st.session_state.cur_idx}")


def show_item(idx):
    item = st.session_state.records[idx]
    logger.info(item)

    with st.form("当前数据"):
        left, right = st.columns(2)
        left.markdown(f"**第{idx+1}条**")
        right.markdown(f"**kb_name**：" + item['kb_name'])
        question = left.text_input(label="question", value=item['question'])

        question_label = item.get('question_label', '其他')
        index = get_default_idx(qustion_labels, question_label)
        question_label = right.selectbox(label="类型", options=qustion_labels, index=index)

        gold_recall = left.text_area(label="gold_recall", key="gold_recall", value=item.get('gold_recall', ''), height=250)
        recall_value = get_recall_str(item, "recall")
        recall = right.text_area(label="recall", value=recall_value, height=250)

        gold_answer = left.text_area(label="gold answer",  value=item.get('gold_answer', ''), height=150)
        answer = right.text_area(label="answer",  value=item.get('answer', ''), height=150)

        score_options = [0, 0.5, 1]
        index = get_default_idx(score_options, item.get('answer_score', 0))
        answer_score = left.selectbox(label="answer_score", options=score_options, index=index, format_func=fmt_func)

        index = get_default_idx(analyse_labels, item.get('analyse_label', '其他'))
        analyse_label = right.selectbox(label="analyse_label", options=analyse_labels, index=index, disabled=answer_score == 1)

        comment = st.text_area(label="comment", value=item.get('comment', ''), height=150)

        submitted = st.form_submit_button("更新")
        if submitted:
            item.update(question=question, question_label=question_label, gold_recall=gold_recall,
                        recall=recall, gold_answer=gold_answer, answer=answer, answer_score=answer_score, analyse_label=analyse_label, comment=comment)
            logger.info(item)
            on_next()
            st.rerun()


def init(records, uploaded_file):
    logger.info("init")
    if "records" not in st.session_state or uploaded_file.name != st.session_state["cur_file"]:
        st.session_state["cur_idx"] = 0
        st.session_state["records"] = records
        st.session_state.cur_file = uploaded_file.name


def load_view():
    logger.info("reload")
    uploaded_file, records, _ = show_upload_table(st)
    if records:
        init(records=records, uploaded_file=uploaded_file)

    if records:
        try:
            show_item(st.session_state.cur_idx)
        except Exception as e:
            logger.exception(e)
        save, left, right = st.columns(3)
        stem, surfix = os.path.splitext(uploaded_file.name)
        dst_file_name = f"{stem}_{datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d-%H:%M:%S')}{surfix}"
        show_save_button(save, file_name=dst_file_name, records=st.session_state["records"], use_container_width=True)
        if left.button("上一个", disabled=st.session_state.cur_idx == 0, use_container_width=True):
            on_previous()
            st.rerun()
        if right.button("下一个", disabled=st.session_state.cur_idx == len(records)-1, use_container_width=True):
            on_next()
            st.rerun()
