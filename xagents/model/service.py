#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@Time    :   2023/12/12 15:50:25
@Author  :   ChenHao
@Contact :   jerrychen1990@gmail.com
'''
import copy
from typing import List
from xagents.model.core import LLM, EMBD, Reranker
from xagents.model.zhipu import GLM, ZhipuEmbedding, ZhipuReranker


_LLM_MODELS = [GLM]
_LLM_MODELS_DICT = {model.__name__: model for model in _LLM_MODELS}


_EMBD_MODELS = [ZhipuEmbedding]
_EMBD_MODELS_DICT = {model.__name__: model for model in _EMBD_MODELS}

_RERANK_MODELS = [ZhipuReranker]
_RERANK_MODELS_DICT = {model.__name__: model for model in _RERANK_MODELS}


def list_llm_models() -> List[str]:
    return [e.__name__ for e in _LLM_MODELS]


def list_embd_models() -> List[str]:
    return [e.__name__ for e in _EMBD_MODELS]


def list_llm_versions(llm_model: str) -> List[str]:
    model_cls = _LLM_MODELS_DICT[llm_model]
    return model_cls.list_versions()


def get_llm_model(config: dict) -> LLM:
    tmp_config = copy.copy(config)
    model_cls = tmp_config.pop("model_cls")
    model_cls = _LLM_MODELS_DICT[model_cls]
    return model_cls(**tmp_config)


def get_embd_model(config: dict) -> EMBD:
    tmp_config = copy.copy(config)
    model_cls = tmp_config.pop("model_cls")
    model_cls = _EMBD_MODELS_DICT[model_cls]
    return model_cls(**tmp_config)

def get_rerank_model(config:dict)->Reranker:
    if not config:
        return None
    tmp_config = copy.copy(config)
    model_cls = tmp_config.pop("model_cls")
    model_cls = _RERANK_MODELS_DICT[model_cls]
    return model_cls(**tmp_config)
    


if __name__ == "__main__":
    # config = dict(model_cls="GLM", name="glm", version="chatglm_turbo")
    # model = get_llm_model(config)
    # resp = model.generate(prompt="你好", stream=False)
    # print(resp)
    rerank_config = dict(model_cls="ZhipuReranker", url="http://36.103.177.140:8000/get_rel_score")
    rerank_model = get_rerank_model(rerank_config)
    score = rerank_model.cal_similarity("你好","你滚")
    print(score)
    
    
