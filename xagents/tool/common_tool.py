#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@Time    :   2024/01/04 14:04:02
@Author  :   ChenHao
@Contact :   jerrychen1990@gmail.com
'''

from xagents.tool.core import BaseTool, Parameter

    
def exec_python(expression:str)->dict:
    try:
        rs = eval(expression)
    except Exception as e:
        rs = "执行失败"
    return dict(result=rs)
    
    
calculator = BaseTool(name="计算器", description="根据提供的数学表达式，用python解释器来执行，得到计算结果",
                      parameters=[Parameter(name="expression", type="string", desctiption="数学表达式，可以通过python来执行的", required=True)],
                      callable=exec_python)
            
            
if __name__ == "__main__":
    rs = calculator.execute("(351345-54351)/54351")
    print(rs)
    
    
    
    
        
