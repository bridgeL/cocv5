"""Agent核心逻辑模块

实现自主决策的Agent系统，支持MCP工具调用和流式响应
"""

import asyncio
import json
import os
from typing import Any
from openai import AsyncOpenAI
from memory import get_memory
from config import OPENAI_API_KEY, OPENAI_BASE_URL, MODEL_NAME
from fastapi import FastAPI, WebSocket, WebSocketDisconnect


# 初始化 OpenAI 客户端
ai_client = AsyncOpenAI(
    base_url=OPENAI_BASE_URL,
    api_key=OPENAI_API_KEY
)


# 系统提示词
SYSTEM_PROMPT = """你是一个 helpful 的助手，可以根据用户需求调用工具来获取信息。

当用户询问苹果数量或价格时，请使用相应的工具获取信息。
用户说"苹果多少钱"时需要获取价格，说"有多少苹果"时需要获取数量。
"""


class Agent:
    """Agent类

    处理用户对话，自主决策是否调用工具，支持流式响应
    """

    def __init__(self, websocket: WebSocket):
        """
        Args:
            websocket: WebSocket连接对象，需支持send方法
        """
        self.ws = websocket
        self.memory = get_memory()

    async def chat(self, message: str, session_id: str) -> None:
        """处理用户对话

        Args:
            message: 用户消息
            session_id: 会话ID
        """
        # 1. 发送 received 确认
        await self._send({"type": "received"})

        # 2. 初始化会话（如果是新会话）
        if not self.memory.has_session(session_id):
            self.memory.add_system_message(session_id, SYSTEM_PROMPT)

        # 3. 添加用户消息到记忆
        self.memory.add_user_message(session_id, message)

        # 4. 进入对话循环（可能涉及多轮工具调用）
        await self._chat_loop(session_id)

    async def _chat_loop(self, session_id: str) -> None:
        """对话主循环，处理可能的工具调用和多轮对话

        Args:
            session_id: 会话ID
        """
        max_iterations = 5  # 防止无限循环

        try:
            for iteration in range(max_iterations):
                # 获取当前记忆
                messages = self.memory.get_messages(session_id)
                print(messages)

                # 调用OpenAI API（启用工具）
                stream = await ai_client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=messages,
                    tools=[],
                    stream=True
                )

                # 处理流式响应
                result = await self._handle_stream(stream, session_id)

                if result["type"] == "message":
                    # 纯文本响应，对话结束
                    # 添加assistant消息到记忆
                    self.memory.add_assistant_message(session_id, content=result["content"])
                    # 发送 complete 标记
                    await self._send({"type": "complete"})
                    return

                elif result["type"] == "tool_calls":
                    # 需要调用工具
                    tool_calls = result["tool_calls"]

                    # 添加assistant消息（包含tool_calls）到记忆
                    self.memory.add_assistant_message(
                        session_id,
                        content=result.get("content"),
                        tool_calls=tool_calls
                    )

                    # 执行工具调用
                    await self._execute_tools(tool_calls, session_id)

                    # 继续循环，让AI处理工具结果
                    continue

            # 达到最大迭代次数，强制结束
            await self._send({"type": "complete"})

        except ConnectionError:
            # WebSocket连接已关闭，退出循环
            print(f"[Agent] 连接已关闭，停止对话循环 (session: {session_id})")

    async def _handle_stream(self, stream: Any, session_id: str) -> dict[str, Any]:
        """处理流式响应

        Args:
            stream: OpenAI流式响应
            session_id: 会话ID

        Returns:
            {"type": "message", "content": str} 或
            {"type": "tool_calls", "tool_calls": [...], "content": str|None}
        """
        content_parts: list[str] = []
        tool_calls_data: dict[int, dict[str, Any]] = {}
        is_tool_call = False

        # 发送 msg_start
        await self._send({"type": "msg_start"})

        async for chunk in stream:
            delta = chunk.choices[0].delta

            # 处理普通内容
            if delta.content:
                content_parts.append(delta.content)
                # 立即发送chunk
                await self._send({"type": "msg_chunk", "content": delta.content})

            # 处理工具调用
            if delta.tool_calls:
                is_tool_call = True
                for tc in delta.tool_calls:
                    index = tc.index
                    if index not in tool_calls_data:
                        tool_calls_data[index] = {
                            "id": "",
                            "type": "function",
                            "function": {"name": "", "arguments": ""}
                        }

                    # 累积tool_call数据
                    if tc.id:
                        tool_calls_data[index]["id"] = tc.id
                    if tc.function:
                        if tc.function.name:
                            tool_calls_data[index]["function"]["name"] += tc.function.name
                        if tc.function.arguments:
                            tool_calls_data[index]["function"]["arguments"] += tc.function.arguments

        # 发送 msg_end
        await self._send({"type": "msg_end"})

        if is_tool_call:
            # 整理tool_calls
            tool_calls = [tool_calls_data[i] for i in sorted(tool_calls_data.keys())]
            return {
                "type": "tool_calls",
                "tool_calls": tool_calls,
                "content": "".join(content_parts) if content_parts else None
            }
        else:
            return {
                "type": "message",
                "content": "".join(content_parts)
            }

    async def _execute_tools(self, tool_calls: list[dict], session_id: str) -> None:
        """执行工具调用

        Args:
            tool_calls: 工具调用列表
            session_id: 会话ID
        """
        # 发送 tool_start
        await self._send({"type": "tool_start", "tool_calls": tool_calls})

        results: list[dict[str, Any]] = []

        for tc in tool_calls:
            function_name = tc["function"]["name"]
            tool_call_id = tc["id"]

            try:
                # 解析参数
                arguments = json.loads(tc["function"]["arguments"]) if tc["function"]["arguments"] else {}

                # # 调用对应的工具函数
                # if function_name in TOOL_MAP:
                #     func = TOOL_MAP[function_name]
                #     # 执行工具（同步函数用run_in_executor包装）
                #     loop = asyncio.get_event_loop()
                #     result = await loop.run_in_executor(None, func)

                #     # 转换结果为字符串
                #     if isinstance(result, (dict, list)):
                #         result_str = json.dumps(result, ensure_ascii=False)
                #     else:
                #         result_str = str(result)

                #     results.append({
                #         "tool_call_id": tool_call_id,
                #         "name": function_name,
                #         "result": result_str,
                #         "status": "success"
                #     })

                #     # 添加到记忆
                #     self.memory.add_tool_result(session_id, tool_call_id, result_str, function_name)

                # else:
                #     error_msg = f"未知工具: {function_name}"
                #     results.append({
                #         "tool_call_id": tool_call_id,
                #         "name": function_name,
                #         "result": error_msg,
                #         "status": "error"
                #     })
                #     self.memory.add_tool_result(session_id, tool_call_id, error_msg, function_name)

            except Exception as e:
                error_msg = f"工具调用失败: {str(e)}"
                results.append({
                    "tool_call_id": tool_call_id,
                    "name": function_name,
                    "result": error_msg,
                    "status": "error"
                })
                self.memory.add_tool_result(session_id, tool_call_id, error_msg, function_name)

        # 发送 tool_end（包含结果）
        await self._send({"type": "tool_end", "results": results})

    async def _send(self, data: dict[str, Any]) -> None:
        """发送消息到WebSocket

        Args:
            data: 要发送的数据

        Raises:
            ConnectionError: 当WebSocket连接已关闭时
        """
        try:
            print(f"[Agent] 发送消息: {data}")
            print(self.ws)
            await self.ws.send_text(json.dumps(data))
        except Exception as e:
            print(f"[Agent] WebSocket发送失败: {e}")
            # 抛出连接错误，让上层知道连接已断开
            raise ConnectionError(f"WebSocket连接已关闭: {e}") from e


def create_agent(websocket: Any) -> Agent:
    """创建Agent实例

    Args:
        websocket: WebSocket连接对象

    Returns:
        Agent实例
    """
    return Agent(websocket)
