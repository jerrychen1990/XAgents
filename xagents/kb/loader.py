#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@Time    :   2023/12/08 14:30:41
@Author  :   ChenHao
@Contact :   jerrychen1990@gmail.com
'''


from abc import abstractmethod
from typing import List
from xagents.config import *
from xagents.kb.common import Chunk, ContentType
from xagents.util import DEFAULT_LOG
logger = DEFAULT_LOG


class AbastractLoader:
    @abstractmethod
    def load(self, file_path: str) -> List[Chunk]:
        raise NotImplementedError


class PDFLoader(AbastractLoader):
    def __init__(self, max_page=None):
        self.max_page = max_page

    def load(self, file_path: str) -> List[Chunk]:
        import PyPDF2
        chunks = []
        with open(file_path, "rb") as f:
            pdf_reader = PyPDF2.PdfReader(f)
            logger.debug(f"got {len(pdf_reader.pages)} pages")
            pages = pdf_reader.pages
            if self.max_page:
                pages = pages[:self.max_page]
            for idx, page in enumerate(pages):
                chunks.append(Chunk(page=page, page_idx=idx+1, content_type=ContentType.TEXT))
        return chunks

