
from zhipuai import ZhipuAI
client = ZhipuAI(api_key="3aeba2365174e850ba45417a16252a09.6gYmkzwLybkub5EW")


# 定义一个查询车票信息的tool
def query_train_info(date, departure, destination):
    msg = f"这是一张从{departure}到{destination}的火车票，出发日期是{date}"
    order_num = "test_order"
    price = 500
    return dict(order_num=order_num, price=price, msg=msg)

def calculator(expression):
    rs = eval(expression)
    return dict(result=rs)


# 定义tool的信息
tools = [
    {
        "type": "function",
        "function": {
            "name": "query_train_info",
            "description": "根据用户提供的信息，查询对应的车次",
            "parameters": {
                "type": "object",
                "properties": {
                    "departure": {
                        "type": "string",
                        "description": "出发城市或车站",
                    },
                    "destination": {
                        "type": "string",
                        "description": "目的地城市或车站",
                    },
                    "date": {
                        "type": "string",
                        "description": "要查询的车次日期",
                    },
                },
                "required": ["departure", "destination", "date"],
            },
        }
    }
]

tools =  [{'type': 'function', 'function': {'name': 'calculator', 'description': '计算器', 'parameters': {'type': 'object', 'properties': {'expression': {'type': 'string', 'desciption': '数学表达式，可以通过python来执行的'}}, 'required': ['expression']}}}]


funcs = [query_train_info, calculator]
name2func = {e.__name__: e for e in funcs}
# 执行func的函数


def call_func(func):
    func_name = func.name
    func_kwargs = eval(func.arguments)
    python_func = name2func.get(func_name)
    if python_func:
        return str(python_func(**func_kwargs))
    return ""


if __name__ == "__main__":

    # 第一轮提问题
    messages = [
        {
            "role": "user",
            "content": "现在有3个苹果，吃掉两个还有几个？"
        }
    ]

    response = client.chat.completions.create(
        model="chatglm3_beta",  # 填写需要调用的模型名称
        messages=messages,
        tools=tools,
        tool_choice="auto",
    )
    resp_message = response.choices[0].message
    print(resp_message)

    # 判断是否有function call
    if resp_message.tool_calls:
        tool_call = resp_message.tool_calls[0]
        call_id = tool_call.id
        func = tool_call.function
        func_resp = call_func(func=func)
        print(f"get response {func_resp} from {func}")

        func_message = dict(role="tool", content=func_resp, toll_call_id=call_id)
        messages.append(func_message)
        print(messages)
        response = client.chat.completions.create(
            model="chatglm3_beta",  # 填写需要调用的模型名称
            messages=messages,
            tools=tools,
            tool_choice="auto",
        )
        resp_message = response.choices[0].message
        print("final response")
        print(resp_message.content)

    