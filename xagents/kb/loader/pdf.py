#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@Time    :   2023/12/11 16:42:25
@Author  :   ChenHao
@Contact :   jerrychen1990@gmail.com
'''


from typing import List
from xagents.config import *
from xagents.kb.common import Chunk, ContentType
from xagents.kb.loader.common import AbastractLoader
from xagents.util import DEFAULT_LOG
logger = DEFAULT_LOG


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
                chunks.append(Chunk(content=page.extract_text(), page_idx=idx+1, content_type=ContentType.TEXT))
        return chunks


if __name__ == "__main__":
    from xagents.config import XAGENT_HOME
    loader = PDFLoader()
    file_path = os.path.join(XAGENT_HOME, "data/raw/贵州茅台2022年报-4.pdf")
    chunks = loader.load(file_path)

    print(len(chunks))
    print(chunks[0])
