#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@Time    :   2023/12/19 13:40:56
@Author  :   ChenHao
@Contact :   jerrychen1990@gmail.com
'''

from typing import List, Dict


import requests
from snippets import *
from xagents.model import LLM, EMBD
from xagents.util import get_log

logger = get_log(__name__)

MOCK_ZETA = {'body': {'id': 'chatcmpl-UXqiZMi4rsDdjiwwjHH5CM', 'object': 'chat.completion', 'created': 1701744928, 'model': 'WindAlice-AIGC-70B-dev-20231017', 'choices': [{'index': 0, 'message': {
    'role': 'assistant', 'content': '您好！我是Wind Alice金融智能助手，有什么我可以帮助您的吗？\n\n'}, 'finish_reason': 'stop'}], 'usage': {'prompt_tokens': 16, 'total_tokens': 34, 'completion_tokens': 18}}}


def call_zeta_chat(messages: List[Dict], temperature=0.01, top_p=0.7, max_new_token=1024):
    return MOCK_ZETA
    url = "http://10.100.4.96/zeta-models/chat/zeta66b"
    data = dict(messages=messages, temperature=temperature, top_p=top_p, max_new_token=max_new_token)
    resp = requests.post(url, json=data)
    resp.raise_for_status()
    return resp.json()


def call_zeta_embedding(contents: List[str]):
    import numpy as np
    return np.random.random(size=(len(contents), 1024)).tolist()

    url = "http://10.100.4.96/zeta-models/embedding/zeta"
    data = dict(contents=contents)
    resp = requests.post(url, json=data)
    resp.raise_for_status()
    return resp.json()["embeddings"]


class ZetaEMBD(EMBD):

    def __init__(self,  batch_size=16, norm=True):
        self.batch_size = batch_size
        self.norm = norm

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        logger.info(f"embedding {len(texts)} with {self.batch_size=}")

        embeddings = []
        from tqdm import tqdm
        for idx, batch in tqdm(enumerate(batchify(texts, self.batch_size))):
            try:
                embds = call_zeta_embedding(contents=batch)
                embeddings.extend(embds)
                pct = idx*self.batch_size/len(texts)
                logger.info(f"{idx*self.batch_size}/{len(texts)} [{pct:2.2%}] embeddings done")
            except Exception as e:
                logger.error(f"embedding service error")
                logger.error(batch)

                raise e
        return embeddings

    def embed_query(self, text: str) -> List[float]:
        embedding = call_zeta_embedding(contents=[text])[0]
        return embedding

    @classmethod
    def get_dim(cls) -> int:
        return 1024


class ZetaLLM(LLM):
    @classmethod
    def list_versions(cls):
        return [
            "v1.0.0",
        ]

    def __init__(self, name="ZETA", version="v1.0.0"):
        super().__init__(name=name, version=version)

    def generate(self, prompt, history=[], stream=True,
                 temperature=0.01, **kwargs):
        messages = history + [dict(role="user", content=prompt)]
        response = call_zeta_chat(messages=messages,
                                  temperature=temperature, **kwargs)
        resp_message = response["body"]["choices"][0]["message"]["content"]
        return (e for e in resp_message) if stream else resp_message


if __name__ == "__main__":

    zeta_llm = ZetaLLM()
    resp = zeta_llm.generate("你好", stream=False)
    print(f"llm resp:{resp}")

    zeta_embd = ZetaEMBD()
    contents = ["万得", "金融"]
    embds = zeta_embd.embed_documents(texts=contents)
    print(f"embd num {len(embds)}")
    print(f"embd dim {len(embds[0])}")
