#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@Time    :   2023/12/07 17:57:13
@Author  :   ChenHao
@Contact :   jerrychen1990@gmail.com
'''


from xagents.agent.core import AbstractAgent
from xagents.model import get_llm_model


class XAgent(AbstractAgent):

    def __init__(self, name, llm_config: dict) -> None:
        super().__init__(name=name)
        self.llm_model = get_llm_model(llm_config)
        self.memory = []

    def chat(self, message: str, stream=True) -> str:
        return self.llm_model.generate(prompt=message, history=self.memory, stream=stream)


if __name__ == "__main__":
    llm_config = dict(model_cls="GLM", name="glm", version="chatglm_turbo")
    agent = XAgent(name="xagent", llm_config=llm_config)
    resp = agent.chat("你好", stream=False)
    print(resp)
