#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@Time    :   2023/12/07 18:40:00
@Author  :   ChenHao
@Contact :   jerrychen1990@gmail.com
'''
import os
from snippets import getlog, print_info

XAGENT_ENV = os.environ.get("XAGENT_ENV", "dev")

XAGENT_HOME = os.path.dirname(os.path.dirname(__file__))


KNOWLEDGE_BASE_DIR = os.environ.get("XAGENT_KNOWLEDGE_BASE_DIR", os.path.join(XAGENT_HOME, "knowledge_base"))
TEMP_DIR = os.environ.get("XAGENT_TEMP_DIR", os.path.join(XAGENT_HOME, "tmp"))
LOG_DIR = os.environ.get("XAGENT_LOG_DIR", os.path.join(XAGENT_HOME, "log"))


logger = getlog("dev", __file__)
print_info("current XAgent env", logger)
logger.info(f"{XAGENT_ENV=}")
logger.info(f"{KNOWLEDGE_BASE_DIR=}")
logger.info(f"{TEMP_DIR=}")
logger.info(f"{LOG_DIR=}")

print_info("", logger)
