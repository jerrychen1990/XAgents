#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@Time    :   2023/12/07 17:47:22
@Author  :   ChenHao
@Contact :   jerrychen1990@gmail.com
'''

from typing import List

import numpy as np
from xagents.model.core import LLM, EMBD
from agit.backend.zhipuai_bk import call_llm_api, call_embedding_api
from snippets import batch_process
from xagents.util import get_log

logger = get_log(__name__)


class GLM(LLM):
    def __init__(self, name: str, version: str, api_key=None):
        super().__init__(name, version)
        self.api_key = api_key

    @classmethod
    def list_versions(cls):
        return [
            "chatglm3_32b_alpha",
            "chatglm3",
            "chatglm3_130b_int8",
            "chatglm3_130b_int4",
            "chatglm_turbo",
            "chatglm2_edge",
            "chatglm2_12b_32k",
            "chatglm_lite",
            "chatglm_std",
            "chatglm_pro",
            "chatglm_6b",
            "chatglm_12b",
            "chatglm_66b",
            "chatglm_130b"
        ]

    def generate(self, prompt, history=[], system=None, stream=True, temperature=0.01, **kwargs):
        # logger.info(f"{self.__class__} generating resp with {prompt=}, {history=}")

        resp = call_llm_api(prompt=prompt, history=history, model=self.version, temperature=temperature, do_search=False,
                            system=system, stream=stream, api_key=self.api_key, logger=logger, **kwargs)
        return resp


class ZhipuEmbedding(EMBD):
    def __init__(self,  api_key=None, batch_size=16, norm=True):
        self.api_key = api_key
        self.batch_size = batch_size
        self.norm = norm

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        logger.info(f"embedding {len(texts)} with {self.batch_size=}")
        embd_func = batch_process(work_num=self.batch_size, return_list=True)(call_embedding_api)
        embeddings = embd_func(texts, api_key=self.api_key, norm=self.norm)

        return embeddings

    def embed_query(self, text: str) -> List[float]:
        embedding = call_embedding_api(text, api_key=self.api_key, norm=self.norm)
        if isinstance(embedding, np.ndarray):
            embedding = embedding.tolist()

        return embedding

    @classmethod
    def get_dim(cls) -> int:
        return 1024


if __name__ == "__main__":
    # llm_model = GLM(name="glm", version="chatglm_turbo")
    # resp = llm_model.generate("你好", stream=False)
    # print(resp)

    embd_model = ZhipuEmbedding()
    text = ["中国", "美国", "日本", "法国", "英国", "意大利", "西班牙", "德国", "俄罗斯"]
    embds = embd_model.embed_documents(text)
    print(len(embds))
    print(embds[0][:4])
    embd = embd_model.embed_query("你好")
    print(len(embd))
    print(embd[:4])
