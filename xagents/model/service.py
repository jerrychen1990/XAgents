#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@Time    :   2023/12/12 15:50:25
@Author  :   ChenHao
@Contact :   jerrychen1990@gmail.com
'''
from xagents.model import list_embd_models as le


def list_embd_models():
    return le()


if __name__ == "__main__":
    print(list_embd_models())
