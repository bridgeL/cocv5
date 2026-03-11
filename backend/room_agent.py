"""
房间KP Agent模块
每个房间有一个独立的KP Agent，负责处理房间内玩家的发言
"""

import uuid
import json
from typing import Callable, Awaitable
from agent import Agent
from memory import Memory
from llm_client import LLMClient
from tool import Tool
from skill import Skill


class RoomAgent:
    """
    房间KP Agent
    扮演克苏鲁的呼唤（CoC）跑团主持人的角色
    """

    def __init__(
        self,
        room_id: str,
        tools: list[Tool],
        skills: list[Skill],
        llm: LLMClient,
        broadcast_callback: Callable[[str, dict], Awaitable[None]],
        db_path: str = "memory.db"
    ):
        self.room_id = room_id
        self.session_id = f"kp_{str(uuid.uuid4())[:8]}"
        self.broadcast_callback = broadcast_callback

        # 创建Memory实例（使用特殊的session_id作为KP标识）
        self.memory = Memory(session_id=self.session_id, db_path=db_path)

        # KP系统提示词
        kp_prompt = """你是克苏鲁的呼唤（Call of Cthulhu, CoC）TRPG的主持人（Keeper, KP）。

你的职责：
1. 引导玩家进行游戏，描述场景、NPC和事件
2. 根据玩家的行动做出响应，推动故事发展
3. 在需要时要求玩家进行技能检定或属性检定
4. 营造悬疑、恐怖的氛围，符合洛夫克拉夫特式的风格
5. 保持中立，不要代替玩家做决定

你收到的消息格式：
【玩家昵称：发言内容】

回复要求：
1. 使用中文回复
2. 保持角色扮演的一致性
3. 不要泄露剧情秘密，让玩家自己探索
4. 可以主动引入剧情元素推动故事发展"""

        # 创建Agent实例
        self.agent = Agent(
            tools=tools,
            skills=skills,
            memory=self.memory,
            prompt=kp_prompt,
            llm=llm,
            websocket=None  # 不使用websocket，通过回调函数广播
        )

        # 替换Agent的发送方法为我们的广播回调
        self.agent._send_ws_message = self._send_message

    async def _send_message(self, msg_type: str, data: dict):
        """
        发送消息给房间内所有成员
        包装消息，标记为来自KP
        """
        # 所有聊天相关消息都添加KP标识和room_id
        chat_message_types = [
            "think_start", "think_chunk", "think_end",
            "report_start", "report_chunk", "report_end",
            "tool_before", "tool_after", "complete", "error"
        ]
        if msg_type in chat_message_types:
            await self.broadcast_callback(msg_type, {
                **data,
                "is_kp": True,
                "nickname": "KP",
                "room_id": self.room_id
            })

    async def handle_player_message(self, nickname: str, content: str):
        """
        处理玩家发言

        Args:
            nickname: 玩家昵称
            content: 发言内容
        """
        # 格式化消息：【昵称：内容】
        formatted_message = f"【{nickname}：{content}】"
        print(f"[RoomAgent {self.room_id}] 收到消息: {formatted_message}")

        # 调用Agent处理
        try:
            await self.agent.chat(formatted_message)
        except Exception as e:
            print(f"[!] RoomAgent处理消息失败: {e}")
            # 发送错误消息
            await self.broadcast_callback("error", {
                "error": f"KP处理消息失败: {str(e)}",
                "is_kp": True,
                "room_id": self.room_id
            })

    def get_session_id(self) -> str:
        """获取KP的session_id"""
        return self.session_id

    def get_recent_messages(self, limit: int = 20) -> list[dict]:
        """获取最近的消息历史"""
        return self.memory.get_recent_rounds(limit)


class RoomAgentManager:
    """
    RoomAgent管理器
    管理所有房间的KP Agent实例
    """

    def __init__(self):
        self.agents: dict[str, RoomAgent] = {}  # room_id -> RoomAgent
        self.tools: list[Tool] = []
        self.skills: list[Skill] = []
        self.llm: LLMClient | None = None

    def initialize(self, tools: list[Tool], skills: list[Skill], llm: LLMClient):
        """初始化管理器，设置工具和技能"""
        self.tools = tools
        self.skills = skills
        self.llm = llm

    async def create_agent(
        self,
        room_id: str,
        broadcast_callback: Callable[[str, dict], Awaitable[None]],
        db_path: str = "memory.db"
    ) -> RoomAgent:
        """
        为房间创建KP Agent

        Args:
            room_id: 房间ID
            broadcast_callback: 广播回调函数
            db_path: 数据库路径

        Returns:
            RoomAgent实例
        """
        if not self.llm:
            raise RuntimeError("RoomAgentManager未初始化，请先调用initialize")

        agent = RoomAgent(
            room_id=room_id,
            tools=self.tools,
            skills=self.skills,
            llm=self.llm,
            broadcast_callback=broadcast_callback,
            db_path=db_path
        )

        self.agents[room_id] = agent
        print(f"[RoomAgentManager] 为房间 {room_id} 创建KP Agent: {agent.get_session_id()}")
        return agent

    def get_agent(self, room_id: str) -> RoomAgent | None:
        """获取房间的KP Agent"""
        return self.agents.get(room_id)

    def remove_agent(self, room_id: str):
        """移除房间的KP Agent"""
        if room_id in self.agents:
            del self.agents[room_id]
            print(f"[RoomAgentManager] 移除房间 {room_id} 的KP Agent")

    async def handle_player_message(self, room_id: str, nickname: str, content: str):
        """
        处理玩家发言

        Args:
            room_id: 房间ID
            nickname: 玩家昵称
            content: 发言内容
        """
        agent = self.agents.get(room_id)
        if agent:
            await agent.handle_player_message(nickname, content)
        else:
            print(f"[!] 房间 {room_id} 没有KP Agent")


# 全局RoomAgentManager实例
room_agent_manager = RoomAgentManager()
