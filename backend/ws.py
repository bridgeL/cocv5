"""
WebSocket 连接管理模块
处理客户端连接、session 管理、消息收发
"""

import json
import uuid
from typing import Callable, Awaitable
from fastapi import WebSocket, WebSocketDisconnect


class WebSocketConnection:
    """管理单个 WebSocket 连接，只负责消息收发，不涉及业务逻辑"""

    def __init__(self, websocket: WebSocket):
        self.websocket = websocket
        self.client = f"{websocket.client.host}:{websocket.client.port}"
        # 生成唯一的 session_id
        self.session_id = str(uuid.uuid4())[:8]
        # 消息处理器（由外部注入）
        self._message_handler: Callable[[str, dict], Awaitable[None]] | None = None

    def set_message_handler(self, handler: Callable[[str, dict], Awaitable[None]]):
        """设置消息处理器

        Args:
            handler: 异步函数，接收 (msg_type, data) 参数
        """
        self._message_handler = handler

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
            # 发送 session_id 给客户端
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

                # 调用外部处理器处理消息
                if self._message_handler:
                    await self._message_handler(msg_type, data)

        except WebSocketDisconnect:
            print(f"[-] 客户端断开: {self.client} (session: {self.session_id})")
        except Exception as e:
            print(f"[!] 与 {self.client} 通信时出错: {e}")
