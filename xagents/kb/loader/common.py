#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@Time    :   2023/12/11 16:40:25
@Author  :   ChenHao
@Contact :   jerrychen1990@gmail.com
'''


from abc import abstractmethod
from typing import List
from xagents.config import *
from xagents.kb.common import Chunk
from xagents.util import DEFAULT_LOG
logger = DEFAULT_LOG


class AbastractLoader:
    @abstractmethod
    def load(self, file_path: str) -> List[Chunk]:
        raise NotImplementedError
