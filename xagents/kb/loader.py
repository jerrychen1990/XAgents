#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@Time    :   2023/12/08 14:30:41
@Author  :   ChenHao
@Contact :   jerrychen1990@gmail.com
'''


from abc import abstractmethod
from typing import List
from snippets import getlog
from xagents.config import *
logger = getlog(XAGENT_ENV, __file__)


class AbastractLoader:
    @abstractmethod
    def load(self, file_path: str) -> List[str]:
        raise NotImplementedError


class PDFLoader(AbastractLoader):
    def __init__(self, max_page=None):
        self.max_page = max_page

    def load(self, file_path: str) -> List[str]:
        import PyPDF2
        text_pages = []
        with open(file_path, "rb") as f:
            pdf_reader = PyPDF2.PdfReader(f)
            logger.debug(f"got {len(pdf_reader.pages)} pages")
            pages = pdf_reader.pages
            if self.max_page:
                pages = pages[:self.max_page]
            for page in pages:
                text_pages.append(page.extract_text())
        return text_pages


_EXT2LOADER = {
    "pdf": PDFLoader
}


def get_loader_cls(file_path: str):
    ext = os.path.splitext(file_path)[-1].lower().replace(".", "")
    loader = _EXT2LOADER[ext]
    return loader


if __name__ == "__main__":
    loader = PDFLoader()
    file_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "../data/raw/贵州茅台2022年报-4.pdf")
    text_pages = loader.load(file_path)
    print(text_pages)
