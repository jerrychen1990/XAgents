#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@Time    :   2024/01/04 14:04:02
@Author  :   ChenHao
@Contact :   jerrychen1990@gmail.com
'''

from typing import List
from xagents.tool.core import BaseTool, Parameter


class CalculatorTool(BaseTool):
    
    @property
    def parameters(self)->List[Parameter]:
        return [Parameter(name="expression", type="string", desctiption="数学表达式，可以通过python来执行的", required=True)]
                

    def execute(self, expression) -> str:
        try:
            rs = eval(expression)
        except Exception as e:
            rs = "执行失败"
        return dict(result=rs)
    
calculator = CalculatorTool(name="calculator", description="计算器")
            
            
if __name__ == "__main__":
    calculator = CalculatorTool(name="calculator", description="根据提供的数学表达式，用python解释器来执行，得到计算结果")
    print(calculator.parameters)
    rs = calculator.execute("(351345-54351)/54351")
    print(rs)
    
    
    
    
        
