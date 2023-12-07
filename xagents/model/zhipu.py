#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@Time    :   2023/12/07 17:47:22
@Author  :   ChenHao
@Contact :   jerrychen1990@gmail.com
'''

from xagents.model.core import LLM
from agit.backend.zhipuai_bk import call_llm_api


class GLM(LLM):
    def __init__(self, name: str, version: str, api_key=None):
        super().__init__(name, version)
        self.api_key = api_key

    def generate(self, prompt, history=[], system=None, stream=True):
        resp = call_llm_api(prompt=prompt, history=history, model=self.version,
                            system=system, stream=stream, api_key=self.api_key)
        return resp


if __name__ == "__main__":
    llm_model = GLM(name="glm", version="chatglm_turbo")
    resp = llm_model.generate("你好", stream=False)
    print(resp)
