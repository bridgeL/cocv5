"""
WebSocket 连接管理模块
处理客户端连接、session 管理、消息收发
"""

import json
import uuid
from typing import Callable, Awaitable
from fastapi import WebSocket, WebSocketDisconnect

# 处理器类型别名
MessageHandler = Callable[[dict], Awaitable[None]]


class WebSocketConnection:
    """管理单个 WebSocket 连接，只负责消息收发，不涉及业务逻辑"""

    def __init__(self, websocket: WebSocket):
        self.websocket = websocket
        self.client = f"{websocket.client.host}:{websocket.client.port}"
        # 生成唯一的 session_id
        self.session_id = str(uuid.uuid4())[:8]
        # 用户ID（由客户端提供）
        self.user_id: str | None = None
        self.nickname: str | None = None
        # 按消息类型注册处理器 {msg_type: handler}
        self._handlers: dict[str, MessageHandler] = {}

    def on(self, msg_type: str, handler: MessageHandler):
        """注册指定消息类型的处理器

        Args:
            msg_type: 消息类型
            handler: 异步函数，接收 data 参数
        """
        self._handlers[msg_type] = handler

    async def send(self, msg_type: str, data: dict):
        """发送消息到客户端"""
        try:
            message = {"type": msg_type, **data}
            print(f"[WS Send] {msg_type}: {data}")
            await self.websocket.send_text(json.dumps(message))
        except WebSocketDisconnect:
            raise
        except Exception:
            raise WebSocketDisconnect(code=1006)

    async def handle(self):
        """处理 WebSocket 连接生命周期"""
        print(f"[+] WebSocket 客户端连接: {self.client}, session_id: {self.session_id}")

        try:
            # 发送 session_init 给客户端，等待用户认证
            await self.send("session_init", {"session_id": self.session_id})

            while True:
                # 接收消息
                text = await self.websocket.receive_text()

                # 解析消息
                try:
                    data = json.loads(text)
                    msg_type = data.get("type", "unknown")
                except json.JSONDecodeError:
                    data = {"type": "raw", "data": text}
                    msg_type = "raw"

                print(f"[WS Receive] {msg_type}: {data}")

                # 内置处理 ping/pong 心跳
                if msg_type == "ping":
                    await self.send("pong", {})
                    continue

                # 内置处理用户认证
                if msg_type == "user_auth":
                    await self._handle_user_auth(data)
                    continue

                # 内置处理历史消息加载
                if msg_type == "load_history":
                    await self._handle_load_history(data)
                    continue

                # 查找并调用对应类型的处理器
                handler = self._handlers.get(msg_type)
                if handler:
                    await handler(data)
                else:
                    # 未注册处理器，回复 unknown
                    await self.send("unknown", {"received": data})

        except WebSocketDisconnect:
            print(f"[-] 客户端断开: {self.client} (session: {self.session_id}, user: {self.user_id})")
        except Exception as e:
            print(f"[!] 与 {self.client} 通信时出错: {e}")

    async def _handle_user_auth(self, data: dict):
        """处理用户认证消息"""
        self.user_id = data.get("user_id")
        self.nickname = data.get("nickname", "匿名用户")

        if self.user_id:
            print(f"[+] 用户认证成功: {self.nickname} ({self.user_id})")
            await self.send("user_auth_success", {
                "session_id": self.session_id,
                "user_id": self.user_id,
                "nickname": self.nickname
            })
        else:
            print(f"[!] 用户认证失败: 缺少 user_id")
            await self.send("user_auth_failed", {"error": "缺少 user_id"})

    async def _handle_load_history(self, data: dict):
        """处理加载历史消息请求

        将历史消息中的 think 和 report 从原始 content 中切分出来，
        发送结构化的历史消息数据。
        """
        if not self.user_id:
            await self.send("error", {"error": "未认证用户无法加载历史消息"})
            return

        limit = data.get("limit", 20)
        print(f"[+] 加载历史消息: user={self.user_id}, limit={limit}")

        try:
            # 临时创建 Memory 实例查询历史
            from memory import Memory
            memory = Memory(session_id=self.session_id, user_id=self.user_id)
            messages = memory.get_recent_rounds(limit)

            # 处理并发送结构化的历史消息
            formatted_messages = self._format_history_messages(messages)
            await self.send("history_messages", {"messages": formatted_messages})

            print(f"[+] 历史消息发送完成: {len(formatted_messages)} 条")
        except Exception as e:
            print(f"[!] 加载历史消息失败: {e}")
            await self.send("error", {"error": f"加载历史消息失败: {str(e)}"})

    def _format_history_messages(self, messages: list[dict]) -> list[dict]:
        """将原始历史消息格式化为结构化数据，切分 think 和 report"""
        import re

        # 收集 tool 结果用于关联
        tool_results = {}
        for msg in messages:
            if msg.get("role") == "tool" and msg.get("tool_call_id"):
                tool_results[msg["tool_call_id"]] = msg.get("content", "")

        formatted = []
        for msg in messages:
            role = msg.get("role")

            if role == "user":
                formatted.append({
                    "role": "user",
                    "content": msg.get("content", "")
                })

            elif role == "assistant":
                content = msg.get("content", "")

                # 解析 think 标签（处理未闭合的情况）
                think = ""
                think_match = re.search(r"<think>(.*?)</think>", content, re.DOTALL)
                if think_match:
                    think = think_match.group(1).strip()
                elif "<think>" in content:
                    # think 标签未闭合，提取从 <think> 开始到字符串结尾（或到 <report> 之前）
                    think_start = content.index("<think>") + len("<think>")
                    think_end = content.find("<report>", think_start)
                    if think_end == -1:
                        think = content[think_start:].strip()
                    else:
                        think = content[think_start:think_end].strip()

                # 解析 report 标签（处理未闭合的情况）
                report = ""
                report_match = re.search(r"<report>(.*?)</report>", content, re.DOTALL)
                if report_match:
                    report = report_match.group(1).strip()
                elif "<report>" in content:
                    # report 标签未闭合，提取从 <report> 开始到字符串结尾
                    report_start = content.index("<report>") + len("<report>")
                    report = content[report_start:].strip()

                # 移除 report 中可能嵌套的 think 标签及其内容
                if report:
                    report = re.sub(r"<think>.*?</think>", "", report, flags=re.DOTALL).strip()

                # 如果没有 think 也没有 report，整个内容作为 report
                if not think and not report:
                    report = content.strip()

                # 处理 tool_calls
                tool_calls = msg.get("tool_calls", [])
                formatted_tool_calls = []
                if tool_calls:
                    for tc in tool_calls:
                        func = tc.get("function", {})
                        tc_id = tc.get("id", "")
                        formatted_tool_calls.append({
                            "id": tc_id,
                            "name": func.get("name", ""),
                            "arguments": func.get("arguments", ""),
                            "result": tool_results.get(tc_id, "")
                        })

                formatted.append({
                    "role": "assistant",
                    "think": think,
                    "report": report,
                    "tool_calls": formatted_tool_calls if formatted_tool_calls else None
                })

            # tool 消息已在 assistant 处理时关联，跳过

        return formatted
