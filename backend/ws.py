"""
WebSocket 连接管理模块
处理客户端连接、session 创建、agent 生命周期管理
"""

import json
import uuid
from fastapi import WebSocket, WebSocketDisconnect
from llm_client import llm
from memory import Memory
from agent import Agent
from tools.current_time import CurrentTimeTool
from tools.weather import WeatherTool
from skills.weather_assistant import WeatherAssistantSkill
from skills.react_reasoning import ReActSkill


class WebSocketConnection:
    """管理单个 WebSocket 连接及其关联的 Agent 和 Memory"""

    def __init__(self, websocket: WebSocket):
        self.websocket = websocket
        self.client = f"{websocket.client.host}:{websocket.client.port}"
        # 生成唯一的 session_id
        self.session_id = str(uuid.uuid4())[:8]
        # 为该连接创建独立的 Memory
        self.memory = Memory(session_id=self.session_id, db_path="memory.db")
        # 创建 Agent，传入 websocket 以便发送消息
        self.agent = self._create_agent()

    def _create_agent(self) -> Agent:
        """创建配置好的 Agent 实例"""
        tools = [
            CurrentTimeTool(),
            WeatherTool(),
        ]
        skills = [
            WeatherAssistantSkill(),
            ReActSkill(),
        ]
        return Agent(
            tools=tools,
            skills=skills,
            memory=self.memory,
            prompt="你是一个专业、友好的AI助手，请用中文回答问题。",
            llm=llm,
            websocket=self.websocket,
        )

    async def send(self, msg_type: str, data: dict):
        """发送消息到客户端"""
        message = {"type": msg_type, **data}
        await self.websocket.send_text(json.dumps(message))

    async def handle(self):
        """处理 WebSocket 连接生命周期"""
        print(f"[+] WebSocket 客户端连接: {self.client}, session_id: {self.session_id}")

        # 发送 session_id 给客户端
        await self.send("session_init", {"session_id": self.session_id})

        try:
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

                # 处理不同类型的消息
                await self._handle_message(msg_type, data)

        except WebSocketDisconnect:
            print(f"[-] 客户端断开: {self.client} (session: {self.session_id})")
        except Exception as e:
            print(f"[!] 与 {self.client} 通信时出错: {e}")
            await self.send("error", {"error": str(e)})

    async def _handle_message(self, msg_type: str, data: dict):
        """处理单条消息"""
        if msg_type == "ping":
            await self.send("pong", {
                "time": data.get("time", 0),
                "server_time": __import__('asyncio').get_event_loop().time(),
            })

        elif msg_type == "echo":
            await self.send("echo", {
                "message": data.get("message", ""),
                "timestamp": __import__('asyncio').get_event_loop().time(),
            })

        elif msg_type == "chat":
            # 旧版 chat，提示使用新版
            await self.send("chat_error", {"error": "请使用 agent_chat 消息类型"})

        elif msg_type == "agent_chat":
            user_message = data.get("message", "")
            print(f"[🤖] 收到来自 {self.client} 的Agent提问 (session: {self.session_id}): {user_message}")

            try:
                await self.agent.chat(user_message)
                print(f"[✓] Agent 回复完成: {self.client} (session: {self.session_id})")
            except Exception as e:
                error_msg = f"Agent 调用失败: {str(e)}"
                print(f"[!] {error_msg}")
                await self.send("error", {"error": error_msg})

        else:
            await self.send("unknown", {"received": data})


async def handle_websocket(websocket: WebSocket):
    """WebSocket 连接入口函数"""
    await websocket.accept()
    conn = WebSocketConnection(websocket)
    await conn.handle()
