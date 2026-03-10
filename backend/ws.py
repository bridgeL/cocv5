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
