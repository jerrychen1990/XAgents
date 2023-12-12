#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@Time    :   2023/12/11 14:28:24
@Author  :   ChenHao
@Contact :   jerrychen1990@gmail.com
'''
import logging
from snippets import getlog_detail
from xagents.config import XAGENT_ENV, LOG_DIR


def get_log(name: str):
    logger_level = logging.INFO if XAGENT_ENV == "prod" else logging.DEBUG
    fmt_type = "simple" if XAGENT_ENV == "prod" else "detail"

    logger = getlog_detail(name=name, format_type=fmt_type, level=logger_level, do_file=True, log_dir=LOG_DIR)
    return logger


DEFAULT_LOG = get_log("default")


def format_prompt(template: str, **kwargs):
    for k, v in kwargs:
        template = template.replace("{k}", str(v))
    return template
