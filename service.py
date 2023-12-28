#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@Time    :   2023/12/28 10:59:55
@Author  :   ChenHao
@Contact :   jerrychen1990@gmail.com
'''
from typing import Union
from fastapi import FastAPI
from pydantic import BaseModel, Field

from xagents.kb.service import get_knowledge_base, list_knowledge_base_names
from xagents.util import get_log
logger = get_log(__name__)


app = FastAPI()


class Response(BaseModel):
    code: int = Field(description="返回码,200为正常返回", default=200)
    msg: str = Field(description="返回消息", default="success")
    data: Union[dict, list, BaseModel] = Field(description="返回数据", default={})

    class Config:
        schema_extra = {
            "example": {
                "code": 200,
                "msg": "success",
            }
        }


@app.get("/health")
def health() -> Response:
    resp = Response(data={"status": "OK"})
    return resp


@app.get('/get_knowledge_base_list',
         tags=["knowledge_base"],
         summary="列出所有知识库名称")
def get_knowledge_base_list() -> Response:
    knowledge_bases = list_knowledge_base_names()
    resp = Response(data=knowledge_bases)
    return resp


@app.post('/knowledge_base_detail', tags=["knowledge_base"], summary="获取知识库详情")
def knowledge_base_detail(knowledge_base_name: str) -> Response:

    logger.info(f"get knowledge base detail with: {knowledge_base_name}")
    kb = get_knowledge_base(knowledge_base_name)
    kb_file_info = kb.list_kb_file_info()
    # TODO 转化成现有接口的格式

    resp = Response(code=200, msg="OK", data=kb_file_info)
    return resp
