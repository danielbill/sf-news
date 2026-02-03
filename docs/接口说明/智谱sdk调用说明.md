基础使用示例
​
简单对话
from openai import OpenAI

client = OpenAI(
    api_key="your-zhipuai-api-key",
    base_url="https://open.bigmodel.cn/api/paas/v4/"
)

completion = client.chat.completions.create(
    model="glm-4.7",
    messages=[
        {"role": "system", "content": "你是一个聪明且富有创造力的小说作家"},
        {"role": "user", "content": "请你作为童话故事大王，写一篇短篇童话故事"}
    ],
    top_p=0.7,
    temperature=0.9
)

print(completion.choices[0].message.content)
​
流式响应
stream = client.chat.completions.create(
    model="glm-4.7",
    messages=[
        {"role": "user", "content": "写一首关于人工智能的诗"}
    ],
    stream=True,
    temperature=0.8
)

for chunk in stream:
    if chunk.choices[0].delta.content is not None:
        print(chunk.choices[0].delta.content, end="", flush=True)

print()  # 换行
​
多轮对话
class ChatBot:
    def __init__(self, api_key: str):
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://open.bigmodel.cn/api/paas/v4/"
        )
        self.conversation = [
            {"role": "system", "content": "你是一个有用的 AI 助手"}
        ]
    
    def chat(self, user_input: str) -> str:
        # 添加用户消息
        self.conversation.append({"role": "user", "content": user_input})
        
        # 调用 API
        response = self.client.chat.completions.create(
            model="glm-4.7",
            messages=self.conversation,
            temperature=1.0
        )
        
        # 获取 AI 回复
        ai_response = response.choices[0].message.content
        
        # 添加到对话历史
        self.conversation.append({"role": "assistant", "content": ai_response})
        
        return ai_response
    
    def clear_history(self):
        """清除对话历史，保留系统提示"""
        self.conversation = self.conversation[:1]

# 使用示例
bot = ChatBot("your-api-key")
print(bot.chat("你好，请介绍一下自己"))
print(bot.chat("你能帮我写代码吗？"))
print(bot.chat("写一个 Python 的快速排序算法"))
​
高级功能
​
推理（thinking）
在思考模式下，GLM-4.7 可以解决复杂的推理问题，包括数学、科学和逻辑问题。
import os
from openai import OpenAI
        
client = OpenAI(api_key='your-api-key', base_url='https://open.bigmodel.cn/api/paas/v4')
response = client.chat.completions.create(
        model='glm-4.7',
        messages=[
            {"role": "system", "content": "you are a helpful assistant"},
            {"role": "user", "content": "what is the revolution of llm?"}
        ],
        stream=True,
        extra_body={
            "thinking": {
                "type": "enabled",
            },
        }
    )
for chunk in response:
    if chunk.choices[0].delta.reasoning_content:
        print(chunk.choices[0].delta.reasoning_content, end='')
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end='')
​
函数调用 (Function Calling)
import json

def get_weather(location: str) -> str:
    """获取指定地点的天气信息"""
    # 这里应该调用真实的天气 API
    return f"{location} 的天气：晴天，温度 25°C"

# 定义函数描述
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "获取指定地点的天气信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "地点名称，例如：北京、上海"
                    }
                },
                "required": ["location"]
            }
        }
    }
]

# 调用带函数的对话
response = client.chat.completions.create(
    model="glm-4.7",
    messages=[
        {"role": "user", "content": "北京今天天气怎么样？"}
    ],
    tools=tools,
    tool_choice="auto"
)

# 处理函数调用
message = response.choices[0].message
if message.tool_calls:
    for tool_call in message.tool_calls:
        if tool_call.function.name == "get_weather":
            args = json.loads(tool_call.function.arguments)
            result = get_weather(args["location"])
            print(f"函数调用结果: {result}")
​
图像理解
import base64
from PIL import Image
import io

def encode_image(image_path: str) -> str:
    """将图像编码为 base64 字符串"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

# 图像理解示例
image_base64 = encode_image("path/to/your/image.jpg")

response = client.chat.completions.create(
    model="glm-4.6v",
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "请描述这张图片的内容"
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{image_base64}"
                    }
                }
            ]
        }
    ],
    temperature=0.7
)

print(response.choices[0].message.content)
​
参数配置
​
常用参数说明
参数	类型	默认值	说明
model	string	必填	要使用的模型名称
messages	array	必填	对话消息列表
temperature	float	0.6	控制输出的随机性 (0-1)
top_p	float	0.95	核采样参数 (0-1)
max_tokens	integer	-	最大输出 token 数
stream	boolean	false	是否使用流式输出
stop	string/array	-	停止生成的标记
注意：temperature 参数的区间为 (0,1)，do_sample = False (temperature = 0) 在 OpenAI 调用中并不适用。
​