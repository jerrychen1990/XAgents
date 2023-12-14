#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@Time    :   2023/11/27 16:44:57
@Author  :   ChenHao
@Contact :   jerrychen1990@gmail.com
'''

import os
import streamlit as st
import pandas as pd
from xagents.config import TEMP_DIR
from xagents.kb.common import RecalledChunk
from xagents.util import get_log
from snippets import *

day = 1214
logger = get_log(__name__)


def fmt_func(v):
    m = {0: "完全错误", 0.5: "部分正确", 1: "完全正确"}
    return m[v]


def save_file():
    file_name = st.session_state.get("file_name")
    records = st.session_state.get("records")
    stem, surfix = os.path.splitext(file_name)
    dst_file_name = f"{stem}_download.{surfix}"
    dst_file_path = f"{TEMP_DIR}/{dst_file_name}"
    logger.info(f"writing file to {dst_file_path}")
    dump_list(records, dst_file_path)
    with open(dst_file_path, "rb") as f:
        byte_content = f.read()
        st.download_button(label="下载文件", key=dst_file_name, data=byte_content,
                           file_name=dst_file_name, mime="application/octet-stream")


def get_recall_str(item, key):
    if not key in item:
        return ""
    recall = eval(item[key])
    # logger.info(item[key])
    # logger.info(type(item[key]))

    chunks = [RecalledChunk(**e) for e in recall]
    return "\n".join(e.to_plain_text() for e in chunks)


def load_view():

    logger.info("reload")

    def read_file():
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        elif uploaded_file.name.endswith(".xlsx"):
            df = pd.read_excel(uploaded_file)
        df.fillna("", inplace=True)
        records = df.to_dict(orient="records")
        columns = list(records[0].keys())
        st.session_state.file_name = uploaded_file.name
        return records, columns

    def init():
        if "records" in st.session_state:
            return

        logger.info("initing records")
        records, columns = read_file()
        st.info(f"{len(records)} records to evalute")
        for col in ["question", "kb_name"]:
            if col not in columns:
                st.toast(f"{col} missing!")
                return None
        st.session_state["cur_idx"] = 0
        st.session_state["records"] = records
        st.session_state["labels"] = list(set(e.get("label", "其他") for e in records))

        return records

    def show_item():
        idx = st.session_state.get("cur_idx", 0)
        logger.info(f"getting item:{idx}")
        item = records[idx]
        logger.info(item)

        to_update = dict()
        left, right = st.columns(2)
        left.markdown(f"**第{idx+1}条**")
        right.markdown(f"**kb_name**：" + item['kb_name'])

        question = left.text_input(label="question", value=item['question'])
        to_update.update(question=question)

        # labels = st.session_state.labels
        qustion_labels = ["其他", "简单查询", "段落统计", "指标计算", "容混概念"]

        question_label = item.get('question_label', '其他')
        logger.info(f"{question_label=}")

        index = qustion_labels.index(question_label) if question_label in qustion_labels else 0

        question_label = right.selectbox(label="类型", options=qustion_labels, index=index)

        # with st.expander("recall"):
        gold_recall = left.text_area(label="gold_recall", value=item.get('gold_recall', ''), height=250)
        to_update["gold_recall"] = gold_recall

        recall_value = get_recall_str(item, f'recall_{day}')
        right.text_area(label="recall", value=recall_value, height=250)

        gold_answer = left.text_area(label="gold answer", value=item.get('gold_answer', ''), height=150)
        to_update["gold_answer"] = gold_answer

        right.text_area(label="answer", value=item.get(f'answer_{day}', ""), height=150)

        score_options = [0, 0.5, 1]
        # index = score_options.index(item.get("recall_score", 0))

        # recall_score = left.selectbox(label="recall score", options=[0, 0.5, 1], index=index, format_func=fmt_func)

        index = score_options.index(item.get("answer_score_{day}", 0))
        answer_score = left.selectbox(label="answer_score", options=[0, 0.5, 1], index=index, format_func=fmt_func)

        # recall_score =  left.number_input(label="recall score",min_value=0, max_value=10, step=1, value=item.get("recall_score", 0))
        # answer_score = right.number_input(label="answer score",min_value=0, max_value=10, step=1, value=item.get("answer_score", 0))

        analyse_labels = ["其他", "召回错误", "答案有问题", "模型幻觉", "计算错误", "回答不完整", "答非所问"]
        label = item.get("analyse_label", "其他")
        idx = analyse_labels.index(label) if label in analyse_labels else 0

        analyse_label = left.selectbox(label="category", options=analyse_labels, index=0)

        comment = right.text_area(label="comment", value=item.get("comment", ""), height=50)

        to_update.update(answer_score=answer_score, analyse_label=analyse_label, comment=comment, question_label=question_label)
        item.update(**to_update)

        st.info(item)

    def on_next():
        logger.info("on next")
        st.session_state.cur_idx += 1
        logger.info(f"cur_idx = {st.session_state.cur_idx}")

    def on_previous():
        logger.info("on previous")
        st.session_state.cur_idx -= 1
        logger.info(f"cur_idx = {st.session_state.cur_idx}")

    uploaded_file = st.file_uploader(label="待测评文件", type=["xlsx", "csv"])
    if uploaded_file:
        init()

    records = st.session_state.get("records")
    idx = st.session_state.get("cur_idx", 0)

    if records:
        save_file()
        left, right = st.columns(2)

        if idx > 0:
            previous = left.button("previous")
            if previous:
                on_previous()
                st.rerun()
        if idx < len(records)-1:
            next = right.button("next")
            if next:
                on_next()
                st.rerun()

        try:
            show_item()
        except Exception as e:
            logger.exception(e)
