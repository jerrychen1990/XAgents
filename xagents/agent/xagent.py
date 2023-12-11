#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@Time    :   2023/12/07 17:57:13
@Author  :   ChenHao
@Contact :   jerrychen1990@gmail.com
'''


from xagents.agent.core import AbstractAgent
from xagents.model import get_llm_model
from xagents.memory import BaseMemory
from xagents.util import get_log

logger = get_log(__name__)

class XAgent(AbstractAgent):

    def __init__(self, name: str,
                 llm_config: dict,
                 memory_config: dict) -> None:
        super().__init__(name=name)
        self.llm_model = get_llm_model(llm_config)
        self.memory = BaseMemory(**memory_config)

    def chat(self, message: str, stream=True, do_remember=True) -> str:
        resp = self.llm_model.generate(prompt=message, history=self.memory.to_llm_history(), stream=stream)
        if stream:
            acc = []
            for ele in resp:
                acc.append(ele)
                yield ele
            resp = "".join(acc)
        if do_remember:
            self.remember("user", message)
            self.remember("assistant", resp)

    def remember(self, role: str, message: str):
        logger.info(f"remembering {role=}, {message=}")
        self.memory.remember(role, message)


if __name__ == "__main__":
    llm_config = dict(model_cls="GLM", name="glm", version="chatglm_turbo")
    memory_config = dict(size=10)
    agent = XAgent(name="xagent", llm_config=llm_config, memory_config=memory_config)
    resp = agent.chat("推荐三首歌", stream=True)
    for item in resp:
        print(item, end="")
    resp = agent.chat("其中第二首是谁唱的？", stream=True)
    for item in resp:
        print(item, end="")
