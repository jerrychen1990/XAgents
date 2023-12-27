from typing import Union
from pydantic import BaseModel
from flask import Flask, jsonify, request
from flasgger import Swagger
from xagents.kb.service import *
from xagents.util import get_log

logger = get_log(__name__)


class Response(BaseModel):
    code: int
    msg: str
    data: Union[dict, list]


app = Flask(__name__)
swagger = Swagger(app)


@app.route('/health', methods=['GET'])
def health():
    return jsonify(dict(status="OK"))


@app.route('/get_knowledge_base_list', methods=['GET'])
def get_knowledge_base_list():
    """列出所有知识库的名称
    ---
    responses:
      200:
        description: 知识库名称的列表
        examples:
          rgb: ['kb1', 'k2b']
    """
    knowledge_bases = list_knowledge_base_names()
    resp = Response(code=200, msg="OK", data=knowledge_bases)
    return jsonify(resp.model_dump())


@app.route('/knowledge_base_detail', methods=['POST'])
def knowledge_base_detail():
    """查询给定知识库的详细情况
    ---
    responses:
      200:
        description: 知识库名称的列表
        examples:
          rgb: ['kb1', 'k2b']
    """
    knowledge_base_name = request.get_json()["knowledge_base_name"]
    logger.info(f"get knowledge base detail with: {knowledge_base_name}")
    kb = get_knowledge_base(knowledge_base_name)

    resp = Response(code=200, msg="OK", data=kb.list_kb_file_info())
    return jsonify(resp.model_dump())


if __name__ == '__main__':
    # 启动 Flask 应用，默认在 0.0.0.0:5000 上运行
    app.run(port=5000, debug=True)
