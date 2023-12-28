#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@Time    :   2023/12/27 19:58:16
@Author  :   ChenHao
@Contact :   jerrychen1990@gmail.com
'''


from xagents.model.core import LLM
from agit.backend.openai_bk import call_llm_api
from xagents.util import get_log

logger = get_log(__name__)


class GPT(LLM):
    def __init__(self, name: str, version: str, proxy="zhipu"):
        super().__init__(name, version)
        self.proxy = proxy

    @classmethod
    def list_versions(cls):
        return ["gpt-4"]
        # models = list_models(keyword="gpt", proxy=self.proxy)
        # model_names = sorted([e.id for e in models])
        # return model_names

    def generate(self, prompt, history=[], system=None, stream=True, temperature=0.01, **kwargs):
        resp = call_llm_api(prompt=prompt, history=history, model=self.version, proxy=self.proxy,
                            temperature=temperature, system=system, stream=stream, logger=logger, **kwargs)
        return resp


if __name__ == "__main__":
    gpt = GPT(name="gpt", version="gpt-4")
    # print(gpt.list_versions())
    resp = gpt.generate(prompt="你是谁", system="把我的话翻译成英语")
    for item in resp:
        print(item, end="")
