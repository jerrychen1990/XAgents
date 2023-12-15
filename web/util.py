#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@Time    :   2023/12/15 14:50:21
@Author  :   ChenHao
@Contact :   jerrychen1990@gmail.com
'''


def get_default_idx(options, default_value):
    try:
        return options.index(default_value)
    except Exception:
        return 0
