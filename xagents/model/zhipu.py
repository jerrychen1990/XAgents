#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@Time    :   2023/12/07 17:47:22
@Author  :   ChenHao
@Contact :   jerrychen1990@gmail.com
'''

from typing import Any, Generator, List, Tuple, Union
import requests
import numpy as np
from xagents.model.core import LLM, EMBD, Reranker
from agit.backend.zhipuai_bk import call_llm_api, call_embedding_api
from snippets import batch_process
from xagents.tool.core import ToolCall
from xagents.util import get_log
from xagents.tool import BaseTool

logger = get_log(__name__)


class GLM(LLM):
    def __init__(self, name: str, version: str, api_key=None):
        super().__init__(name, version)
        self.api_key = api_key

    @classmethod
    def list_versions(cls):
        return [
            "chatglm3_32b_alpha",
            "chatglm3_beta",
            "chatglm3_130b_int8",
            "chatglm3_130b",
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

    def _convert_tool_desc(self, tools: List[BaseTool]) -> List[dict]:
        resp = []
        for tool in tools:

            properties = {p.name: dict(type=p.type, desciption=p.desctiption) for p in tool.parameters}
            required = [p.name for p in tool.parameters if p.required]
            parameters = dict(type="object", properties=properties, required=required)
            tool_desc = dict(type="function", function=dict(name=tool.name, description=tool.description, parameters=parameters))
            resp.append(tool_desc)

        return resp
    
    def _convert_tool_call(self, tool_calls:List) -> ToolCall:
        tool_call = tool_calls[0]
        tool_call = ToolCall(name = tool_call.function.name, parameters = eval(tool_call.function.arguments), extra_info=dict(tool_call_id=tool_call.id))
        return tool_call
        
        
    def observe(self, tool_call:ToolCall, observe:Any, tools: List[BaseTool] = [], history=[], **kwargs):
        glm_tools = self._convert_tool_desc(tools)
        message =dict(role="tool", content=str(observe), tool_call_id=tool_call.extra_info["tool_call_id"])
        tool_calls, resp = call_llm_api(prompt=message,history=history, model=self.version, api_key=self.api_key,
                                        tools = glm_tools,
                                        logger=logger, **kwargs)
        return resp

    def generate(self, prompt, history=[], system=None, tools: List[BaseTool] = [], stream=True, temperature=0.01, **kwargs)->Tuple[ToolCall, Union[str, Generator]]:
        # logger.info(f"{self.__class__} generating resp with {prompt=}, {history=}")
        glm_tools = self._convert_tool_desc(tools)
        logger.debug(glm_tools)
        
        tool_calls, resp = call_llm_api(prompt=prompt, history=history, model=self.version, temperature=temperature, tools=glm_tools,
                            do_search=False, system=system, stream=stream, api_key=self.api_key, logger=logger, **kwargs)
        if tool_calls:
            logger.debug(f"tool_calls:{tool_calls}")
            tool_call = self._convert_tool_call(tool_calls)
        else:
            tool_call = None
        return tool_call, resp


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


class ZhipuReranker(Reranker):
    def __init__(self,  url: str, name="reranker", version="ZhipuReranker"):
        self.url = url
        super().__init__(name=name, version=version)

    def cal_similarity(self, text1: str, text2: str):
        logger.debug(f"rerank simi for {text1}, {text2}")
        resp = requests.post(url=self.url, params=dict(text1=text1, text2=text2))
        resp.raise_for_status()
        return resp.json()["data"]["score"]


if __name__ == "__main__":
    # llm_model = GLM(name="glm", version="chatglm_turbo")
    # resp = llm_model.generate("你好", stream=False)
    # print(resp)

    # embd_model = ZhipuEmbedding()
    # text = ["中国", "美国", "日本", "法国", "英国", "意大利", "西班牙", "德国", "俄罗斯"]
    # embds = embd_model.embed_documents(text)
    # print(len(embds))
    # print(embds[0][:4])
    # embd = embd_model.embed_query("你好")
    # print(len(embd))
    # print(embd[:4])

    reranker = ZhipuReranker(url="http://36.103.177.140:8000/get_rel_score", name="zhipu_ranker", version="bge-reranker-base")
    sim = reranker.cal_similarity("私募基金", "公募基金")
    print(sim)
