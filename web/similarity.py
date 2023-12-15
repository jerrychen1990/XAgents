#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@Time    :   2023/12/15 10:48:10
@Author  :   ChenHao
@Contact :   jerrychen1990@gmail.com
'''


from typing import List
import streamlit as st
from agit.utils import cal_vec_similarity
from web.kb_web import DEFAULT_EMBD_MODEL
from xagents.model.service import list_embd_models, get_embd_model
from xagents.model import EMBD
from web.config import *

# from scripts.cal_text_similarity import sort_similarity


reverse_metric = {"cosine", "ip"}

DEFAULT_QUERY = "番茄"

DEFAULT_CANDS = """番茄
==
西红柿
==
洋柿子
==
番茄番茄番茄番茄番茄番茄
==
^番茄~
==
番薯
==
茄子
==
tomato
    """

embd_models = list_embd_models()


def sort_similarity(text: str, cands: List[str], embd_model: EMBD, normalize, metric):
    query_emb = embd_model.embed_query(text)
    rs = []
    cand_embds = embd_model.embed_documents(cands)
    for cand, cand_embd in zip(cands, cand_embds):
        similarity = cal_vec_similarity(query_emb, cand_embd, normalize=normalize, metric=metric)
        rs.append((cand, similarity))
    rs.sort(key=lambda x: x[1], reverse=metric in reverse_metric)
    return rs


@st.cache_data
def do_get_embd_model(embedding_model, normalize) -> EMBD:
    config = dict(model_cls=embedding_model, norm=normalize)
    return get_embd_model(config)


def load_view():
    embd_idx = embd_models.index(DEFAULT_EMBD_MODEL)
    embedding_model = st.sidebar.selectbox(
        "embedding模型", options=embd_models, index=embd_idx)

    metric = st.sidebar.selectbox("相似度算法", options=["cosine", "l2_distance", "ip"])
    normalize = st.sidebar.checkbox("是否归一化", value=True)

    text = st.text_input("搜索词", value=DEFAULT_QUERY)

    cands = st.text_area("候选词（==）隔开", value=DEFAULT_CANDS, height=300)

    submit = st.button("排序")
    if submit:
        # cands = st.session_state.cands
        embd_model = do_get_embd_model(embedding_model, normalize)

        cands = cands.split("==")
        cands = [e.strip() for e in cands if e.strip()]
        # st.info(f"sorting {cands=}")
        rs = sort_similarity(text, cands, embd_model, normalize=normalize, metric=metric)
        for cand, simi in rs:
            st.markdown(f"**{cand}**:[{simi:2.3f}]")
