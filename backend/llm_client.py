from openai import AsyncOpenAI
from typing import Any
from config import MODEL_API_KEY, MODEL_URL, MODEL_NAME


class LLMStreamResult:
    """LLM流式调用结果对象，每个调用独立，避免并发冲突"""

    def __init__(self):
        self.full_response: str = ""
        self.tool_calls: list[dict[str, Any]] = []


class LLMClient:
    def __init__(self, url: str, api_key: str, model_name: str):
        self.client = AsyncOpenAI(base_url=url, api_key=api_key)
        self.model_name = model_name

    async def astream(self, messages, tools):
        """
        异步流式调用LLM
        返回 (chunk_generator, result) 元组，result 包含完整的响应和工具调用
        每个调用返回独立的 result 对象，避免多个 Agent 并发使用时的数据冲突
        """
        result = LLMStreamResult()
        tool_calls_data: dict[int, dict] = {}

        stream = await self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            tools=tools,
            stream=True,
        )

        async def generator():
            async for chunk in stream:
                delta = chunk.choices[0].delta

                if delta.content:
                    content_chunk = delta.content
                    result.full_response += content_chunk
                    yield content_chunk

                if delta.tool_calls:
                    for tc in delta.tool_calls:
                        index = tc.index

                        if index not in tool_calls_data:
                            tool_calls_data[index] = {
                                "id": "",
                                "type": "function",
                                "function": {"name": "", "arguments": ""},
                            }

                        if tc.id:
                            tool_calls_data[index]["id"] = tc.id
                        if tc.function:
                            f = tool_calls_data[index]["function"]
                            if tc.function.name:
                                f["name"] += tc.function.name
                            if tc.function.arguments:
                                f["arguments"] += tc.function.arguments

            # 流结束后，整理 tool_calls 到结果对象
            result.tool_calls = [
                tool_calls_data[i] for i in sorted(tool_calls_data.keys())
            ]

        return generator(), result


llm = LLMClient(MODEL_URL, MODEL_API_KEY, MODEL_NAME)
