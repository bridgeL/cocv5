import asyncio
import json
from openai import AsyncOpenAI


class LLMClient:
    def __init__(self, url: str, api_key: str, model_name: str):
        # 初始化 OpenAI 客户端
        self.client = AsyncOpenAI(base_url=url, api_key=api_key)
        self.model_name = model_name

    async def send(self, raw_messages, raw_tools) -> None:
        print(f"[send to ai] {raw_messages} {raw_tools}")

        # 调用OpenAI API（启用工具）
        stream = await self.client.chat.completions.create(
            model=self.model_name,
            messages=raw_messages,
            tools=raw_tools,
            stream=True,
        )

        # 收集完整响应用于判断是否是工具调用
        msg_data = []
        tool_calls_data = {}
        is_tool_call = False

        async for chunk in stream:
            delta = chunk.choices[0].delta

            # 处理普通内容
            if delta.content:
                msg_data.append(delta.content)
                print(f"[msg chunk] {delta.content}")
                # 流式回调
                await self.on_msg_chunk(delta.content)

            # 处理工具调用
            if delta.tool_calls:
                is_tool_call = True
                for tc in delta.tool_calls:
                    index = tc.index

                    # 创建模板
                    if index not in tool_calls_data:
                        tool_calls_data[index] = {
                            "id": "",
                            "type": "function",
                            "function": {"name": "", "arguments": ""},
                        }

                    # 累积tool_call数据
                    if tc.id:
                        tool_calls_data[index]["id"] = tc.id
                    if tc.function:
                        f = tool_calls_data[index]["function"]
                        if tc.function.name:
                            f["name"] += tc.function.name
                        if tc.function.arguments:
                            f["arguments"] += tc.function.arguments

        if msg_data:
            msg = "".join(msg_data)
            print(f"[ai reply] {msg}")

        # 如果是工具调用，处理完整的工具调用结果
        if is_tool_call:
            tool_calls = [[i] for i in sorted(tool_calls_data.keys())]
            print(f"[tool calls] {tool_calls}")
            await self.on_tool_calls(tool_calls)

    async def on_msg_chunk(self, chunk: str):
        """流式消息块回调"""

    async def on_tool_calls(self, tool_calls: list[dict]):
        """工具调用回调"""

    async def chat(self, messages: list, msg):
        messages.append({"role": "user", "content": msg})

        import tools.get_product_cnt
        import tools.get_product_price
        from tools.utils import convert_tool_to_openai_function

        all_tools = [tools.get_product_cnt.tool, tools.get_product_price.tool]
        await self.send(
            messages, [convert_tool_to_openai_function(tool) for tool in all_tools]
        )
