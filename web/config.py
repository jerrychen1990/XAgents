#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@Time    :   2023/12/14 15:50:57
@Author  :   ChenHao
@Contact :   jerrychen1990@gmail.com
'''

DEFAULT_MODEL = "GLM"
DEFAULT_KB = "guizhoumaotai"
DEFAULT_TEMPERATURE = 0.01
DEFAULT_TOP_K = 3
DEFAULT_EXPAND_LEN = 2000
DEFAULT_FORWARD_RATE = 0.5

DEFAULT_VS_TYPE = "FAISS"
DEFAULT_EMBD_MODEL = "ZhipuEmbedding"
DEFAULT_DISTANCE_STRATEGY = "MAX_INNER_PRODUCT"

DEFAULT_SPLITTER = "BaseSplitter"
DEFAULT_CUTTER = r"\n"
DEFAULT_PARSE_TABLE = False
DEFAULT_MIN_LEN = 5
DEFAULT_MAX_LEN = 150

DEFAULT_KB_PROMPT_TEMPLATE = '''
有如下的年报信息：

"""
{context}
"""

使用上述年报信息，回答下方问题，你所需要的全部内容都在年报信息中。
如果没有找到相关信息，请告诉我”没有相关信息“

问题：
"""
{question}
"""'''
