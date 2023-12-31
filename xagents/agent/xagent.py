#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@Time    :   2023/12/07 17:57:13
@Author  :   ChenHao
@Contact :   jerrychen1990@gmail.com
'''


from typing import Generator, List

from xagents.agent.core import AbstractAgent, AgentResp
from xagents.config import DEFAULT_KB_PROMPT_TEMPLATE
from xagents.kb.common import RecalledChunk
from xagents.kb.service import get_knowledge_base
from xagents.model.service import get_llm_model
from xagents.memory import BaseMemory
from xagents.tool.service import invoke_tool_call
from xagents.tool.core import BaseTool, ToolCall
from xagents.util import get_log


logger = get_log(__name__)


class XAgent(AbstractAgent):

    def __init__(self, name: str,
                 llm_config: dict,
                 memory_config: dict,
                 tools: List[BaseTool] = [],
                 kb_name: str = None,
                 kb_prompt_template: str = DEFAULT_KB_PROMPT_TEMPLATE) -> None:
        super().__init__(name=name)
        self.llm_model = get_llm_model(llm_config)
        self.memory = BaseMemory(**memory_config)
        if kb_name:
            self.kb = get_knowledge_base(kb_name)
        else:
            self.kb = None
        self.kb_prompt_template = kb_prompt_template
        self.tools = tools

    def search_kb(self, query: str, **kwargs) -> List[RecalledChunk]:
        if not self.kb:
            logger.warning('No knowledge base found! Will return empty recall chunks')
            return []
        chunks = self.kb.search(query=query, **kwargs)
        return chunks

    def use_tool(self, tool_call: ToolCall):
        resp = invoke_tool_call(tool_call)
        return resp

    def chat(self, message: str, stream=True, do_remember=True,
             use_kb=False, top_k=3, score_threshold=None, temperature=0.01,
             do_split_query=False, fake_chat=False, file_names: List[str] = None,
             do_expand=False, expand_len: int = 500, forward_rate: float = 0.5, rerank_config: dict = dict(),
             **kwargs) -> AgentResp:
        if use_kb:
            chunks = self.search_kb(query=message, top_k=top_k, score_threshold=score_threshold, do_split_query=do_split_query,
                                    do_expand=do_expand, expand_len=expand_len, forward_rate=forward_rate, file_names=file_names, rerank_config=rerank_config)
            context = "\n".join(f"{idx+1}." + c.to_plain_text() for idx, c in enumerate(chunks))
            # logger.debug(f"{context=}")
            prompt = self.kb_prompt_template.format(question=message, context=context)
        else:
            prompt = message
            chunks = None

        if fake_chat:
            fake_resp = "这是MOCK的回答信息,如果需要真实回答,请设置fake_chat=False"
            model_resp = (e for e in fake_resp) if stream else fake_resp
            tool_call = None
        else:
            tool_call, model_resp = self.llm_model.generate(prompt=prompt, history=self.memory.to_llm_history(), tools=self.tools,
                                                            temperature=temperature, stream=stream, **kwargs)
            # 调用tool
            if tool_call:
                logger.debug(f"calling tool:{tool_call.name}")
                self.use_tool(tool_call)
                history = self.memory.to_llm_history() + [dict(role="user", content=prompt)]
                model_resp = self.llm_model.observe(tool_call, tools=self.tools,history=history,
                                                    stream=stream, temperature=temperature, **kwargs)            

        def _remember_callback(resp_str):
            if do_remember:
                self.remember("user", message)
                self.remember("assistant", resp_str)

        def _add_remember_callback(gen: Generator) -> Generator:
            acc = []
            for ele in gen:
                acc.append(ele)
                yield ele
            _remember_callback("".join(acc))

        if stream:
            model_message = _add_remember_callback(model_resp)
        else:
            model_message = model_resp
            _remember_callback(model_message)

        resp = AgentResp(content=model_message, references=chunks, tool_call=tool_call)
        return resp

    def remember(self, role: str, message: str):
        logger.info(f"remembering {role=}, {message=}")
        self.memory.remember(role, message)

    def clear_memory(self):
        logger.info("clearing memory")
        self.memory.clear()


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
