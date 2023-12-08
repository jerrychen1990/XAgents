#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@Time    :   2023/12/08 14:38:44
@Author  :   ChenHao
@Contact :   jerrychen1990@gmail.com
'''

from abc import abstractmethod
from typing import List
from snippets import getlog
from xagents.config import *
import re

logger = getlog(XAGENT_ENV, __file__)


class AbstractSplitter:
    @abstractmethod
    def split(self, text: str) -> List[str]:
        raise NotImplementedError


class BaseSplitter(AbstractSplitter):
    def _parse_text(self, text: str) -> str:
        text = text.strip()
        text = re.sub("\s+", " ", text)
        text = re.sub("\.+", "", text)
        return text

    def split(self, text: str, splitter="\n") -> List[str]:
        texts = re.split(splitter, text)
        texts = [(self._parse_text(t)) for t in texts]
        return [e for e in texts if e]


if __name__ == "__main__":
    spliter = BaseSplitter()
    texts = ["第一节  释义  ................................ ", " "]
    for text in texts:
        print(spliter._parse_text(text))
