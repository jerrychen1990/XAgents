#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@Time    :   2023/12/08 14:30:41
@Author  :   ChenHao
@Contact :   jerrychen1990@gmail.com
'''


from abc import abstractmethod
from chunk import Chunk
from typing import List
from snippets import getlog
from xagents.config import *
logger = getlog(XAGENT_ENV, __file__)


class AbastractLoader:
    @abstractmethod
    def load(self, file_path: str) -> List[Chunk]:
        raise NotImplementedError


class PDFLoader(AbastractLoader):
    def __init__(self, max_page=None):
        self.max_page = max_page

    def load(self, file_path: str) -> str:
        import PyPDF2
        with open(file_path, "rb") as f:
            pdf_reader = PyPDF2.PdfReader(f)
            logger.debug(f"got {len(pdf_reader.pages)} pages")
            pages = pdf_reader.pages
            if self.max_page:
                pages = pages[:self.max_page]
            rs = ""
            for page in pages:
                rs += page.extract_text()

        return rs


if __name__ == "__main__":
    pass
