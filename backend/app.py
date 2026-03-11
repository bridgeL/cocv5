from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from memory import Memory
from ws import WebSocketConnection
from llm_client import llm
from agent import Agent
from tools.current_time import CurrentTimeTool
from tools.weather import WeatherTool
from tools.roll_dice import RollDiceTool
from tools.skill_check import SkillCheckTool
from tools.skill_manager import SkillManagerTool
from tools.coc_character_attributes import CoCCharacterAttributesTool
from skills.weather_assistant import WeatherAssistantSkill
from skills.react_reasoning import ReActSkill
from skills.coc_character_generator import CoCCharacterGeneratorSkill
from skills.skill_loader import SkillLoaderSkill
from room_manager import room_manager
from room_agent import room_agent_manager


def create_agent(websocket: WebSocket, memory: Memory) -> Agent:
    """创建配置好的 Agent 实例

    Args:
        websocket: WebSocket 连接，用于发送消息到客户端
        memory: 记忆实例，用于存储会话历史

    Returns:
        配置好的 Agent 实例
    """
    # 先创建 skills 列表
    skills = [
        WeatherAssistantSkill(),
        ReActSkill(),
        CoCCharacterGeneratorSkill(),
        SkillLoaderSkill(),
    ]

    # 创建 tools，skill_manager 需要传入 skills
    tools = [
        CurrentTimeTool(),
        WeatherTool(),
        RollDiceTool(),
        SkillCheckTool(),
        SkillManagerTool(skills),
        CoCCharacterAttributesTool(),
    ]
    agent = Agent(
        tools=tools,
        skills=skills,
        memory=memory,
        prompt="你是一个专业、友好的AI助手，请用中文回答问题。",
        llm=llm,
        websocket=websocket,
    )

    return agent


# 初始化 RoomAgentManager（在应用启动时调用）
def init_room_agent_manager():
    """初始化RoomAgentManager，设置工具和技能"""
    skills = [
        WeatherAssistantSkill(),
        ReActSkill(),
        CoCCharacterGeneratorSkill(),
        SkillLoaderSkill(),
    ]
    tools = [
        CurrentTimeTool(),
        WeatherTool(),
        RollDiceTool(),
        SkillCheckTool(),
        SkillManagerTool(skills),
        CoCCharacterAttributesTool(),
    ]
    room_agent_manager.initialize(tools=tools, skills=skills, llm=llm)
    print("[✓] RoomAgentManager 初始化完成")


# 创建 FastAPI 应用
app = FastAPI(title="WebSocket Demo HTTP Server")

# 初始化 RoomAgentManager
init_room_agent_manager()

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_class=HTMLResponse)
async def get_index():
    """返回 index.html 页面"""
    with open("index.html", "r", encoding="utf-8") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket 连接处理器
    - 每个连接生成独立的 session_id
    - 创建独立的 Memory 和 Agent
    - 处理 ping/pong 心跳
    - 处理 Agent 对话
    - 支持用户认证（user_id + nickname）
    """
    await websocket.accept()

    # 创建连接（自动生成 session_id）
    conn = WebSocketConnection(websocket)

    # 延迟初始化资源（等待用户认证）
    memory: Memory | None = None
    agent: Agent | None = None

    def ensure_initialized():
        """确保资源已初始化（延迟初始化，等待用户认证）"""
        nonlocal memory, agent
        if memory is None:
            # 使用 user_id 创建 Memory（如果已认证）
            memory = Memory(
                session_id=conn.session_id,
                user_id=conn.user_id,
                db_path="memory.db"
            )
            agent = create_agent(websocket, memory)
            print(f"[✓] 资源初始化完成: session={conn.session_id}, user={conn.user_id}")

    # 注册 agent_chat 处理器
    async def handle_agent_chat(data: dict):
        # 确保资源已初始化
        ensure_initialized()

        user_message = data.get("message", "")
        user_info = f"{conn.nickname}({conn.user_id})" if conn.user_id else conn.client
        print(
            f"[🤖] 收到来自 {user_info} 的Agent提问 (session: {conn.session_id}): {user_message}"
        )
        try:
            await agent.chat(user_message)
            print(f"[✓] Agent 回复完成: {user_info} (session: {conn.session_id})")
        except Exception as e:
            error_msg = f"Agent 调用失败: {str(e)}"
            print(f"[!] {error_msg}")
            await conn.send("error", {"error": error_msg})

    conn.on("agent_chat", handle_agent_chat)

    # ===== 房间相关消息处理器 =====

    async def handle_list_rooms(data: dict):
        """获取房间列表"""
        if not conn.user_id:
            await conn.send("room_error", {"error": "请先登录"})
            return

        tab = data.get("tab", "hall")
        rooms = room_manager.get_room_list(conn.user_id, tab)
        await conn.send("rooms_list", {"rooms": rooms, "tab": tab})

    async def handle_create_room(data: dict):
        """创建房间"""
        if not conn.user_id:
            await conn.send("room_error", {"error": "请先登录"})
            return

        name = data.get("name", "").strip()
        password = data.get("password")

        if not name:
            await conn.send("room_error", {"error": "房间名称不能为空"})
            return

        try:
            room = await room_manager.create_room(
                name=name,
                owner_id=conn.user_id,
                nickname=conn.nickname,
                password=password,
                ws_connection=conn
            )

            # 创建KP Agent
            async def broadcast_to_room(msg_type: str, msg_data: dict):
                await room_manager.broadcast_to_room(room["id"], msg_type, msg_data)

            agent = await room_agent_manager.create_agent(
                room_id=room["id"],
                broadcast_callback=broadcast_to_room
            )

            # 保存KP session_id到房间
            from memory import RoomMemory
            room_memory = RoomMemory()
            room_memory.set_kp_session(room["id"], agent.get_session_id())

            # 获取成员列表
            members = room_manager.get_room_members(room["id"])

            await conn.send("room_created", {"room": room, "members": members})
            print(f"[✓] 创建房间成功: {room['id']} ({name}) by {conn.nickname}")
        except Exception as e:
            await conn.send("room_error", {"error": f"创建房间失败: {str(e)}"})

    async def handle_join_room(data: dict):
        """加入房间"""
        if not conn.user_id:
            await conn.send("room_error", {"error": "请先登录"})
            return

        room_id = data.get("room_id")
        password = data.get("password")

        if not room_id:
            await conn.send("room_error", {"error": "房间ID不能为空", "room_id": room_id})
            return

        try:
            result = await room_manager.join_room(
                room_id=room_id,
                user_id=conn.user_id,
                nickname=conn.nickname,
                password=password,
                ws_connection=conn
            )

            # 检查房间是否已有KP Agent，如果没有则创建
            if not room_agent_manager.get_agent(room_id):
                async def broadcast_to_room(msg_type: str, msg_data: dict):
                    await room_manager.broadcast_to_room(room_id, msg_type, msg_data)

                agent = await room_agent_manager.create_agent(
                    room_id=room_id,
                    broadcast_callback=broadcast_to_room
                )
                from memory import RoomMemory
                room_memory = RoomMemory()
                room_memory.set_kp_session(room_id, agent.get_session_id())
                print(f"[✓] 为房间 {room_id} 创建KP Agent")

            await conn.send("room_joined", result)
            print(f"[✓] 加入房间成功: {conn.nickname} -> {room_id}")
        except ValueError as e:
            await conn.send("room_error", {"error": str(e), "room_id": room_id})
        except Exception as e:
            await conn.send("room_error", {"error": f"加入房间失败: {str(e)}", "room_id": room_id})

    async def handle_leave_room(data: dict):
        """离开房间"""
        if not conn.user_id:
            await conn.send("room_error", {"error": "请先登录"})
            return

        room_id = data.get("room_id")
        if not room_id:
            await conn.send("room_error", {"error": "房间ID不能为空", "room_id": room_id})
            return

        success = await room_manager.leave_room(room_id, conn.user_id)
        if success:
            await conn.send("room_left", {"room_id": room_id})
            print(f"[✓] 离开房间成功: {conn.nickname} -> {room_id}")
        else:
            await conn.send("room_error", {"error": "离开房间失败", "room_id": room_id})

    async def handle_close_room(data: dict):
        """关闭房间（仅房主）"""
        if not conn.user_id:
            await conn.send("room_error", {"error": "请先登录"})
            return

        room_id = data.get("room_id")
        if not room_id:
            await conn.send("room_error", {"error": "房间ID不能为空", "room_id": room_id})
            return

        success = await room_manager.close_room(room_id, conn.user_id)
        if success:
            # 移除KP Agent
            room_agent_manager.remove_agent(room_id)
            await conn.send("room_closed", {"room_id": room_id})
            print(f"[✓] 关闭房间成功: {room_id} by {conn.nickname}")
        else:
            await conn.send("room_error", {"error": "关闭房间失败，可能不是房主", "room_id": room_id})

    async def handle_room_chat(data: dict):
        """房间内发言"""
        if not conn.user_id:
            await conn.send("room_error", {"error": "请先登录"})
            return

        room_id = data.get("room_id")
        content = data.get("content", "").strip()

        if not room_id:
            await conn.send("room_error", {"error": "房间ID不能为空", "room_id": room_id})
            return

        if not content:
            await conn.send("room_error", {"error": "消息内容不能为空", "room_id": room_id})
            return

        # 检查用户是否在房间中
        if not room_manager.is_user_in_room(conn.user_id, room_id):
            await conn.send("room_error", {"error": "您不在该房间中", "room_id": room_id})
            return

        # 保存消息到数据库
        room_manager.add_message(
            room_id=room_id,
            user_id=conn.user_id,
            role="user",
            content=content
        )

        # 广播消息给房间所有成员
        await room_manager.broadcast_to_room(room_id, "room_message", {
            "room_id": room_id,
            "user_id": conn.user_id,
            "nickname": conn.nickname,
            "content": content,
            "is_kp": False,
            "timestamp": str(int(__import__('time').time() * 1000))
        })

        # 发送给KP Agent处理
        await room_agent_manager.handle_player_message(room_id, conn.nickname, content)

        print(f"[🗨️] 房间消息: [{room_id}] {conn.nickname}: {content[:50]}...")

    async def handle_load_room_history(data: dict):
        """加载房间历史消息"""
        if not conn.user_id:
            await conn.send("room_error", {"error": "请先登录"})
            return

        room_id = data.get("room_id")
        if not room_id:
            await conn.send("room_error", {"error": "房间ID不能为空", "room_id": room_id})
            return

        # 检查用户是否在房间中
        if not room_manager.is_user_in_room(conn.user_id, room_id):
            await conn.send("room_error", {"error": "您不在该房间中", "room_id": room_id})
            return

        limit = data.get("limit", 20)
        messages = room_manager.get_room_messages(room_id, limit)

        await conn.send("room_history", {
            "room_id": room_id,
            "messages": messages
        })

    # 注册房间消息处理器
    conn.on("list_rooms", handle_list_rooms)
    conn.on("create_room", handle_create_room)
    conn.on("join_room", handle_join_room)
    conn.on("leave_room", handle_leave_room)
    conn.on("close_room", handle_close_room)
    conn.on("room_chat", handle_room_chat)
    conn.on("load_room_history", handle_load_room_history)

    await conn.handle()


def main():
    """主函数 - 启动 HTTP + WebSocket 服务 (统一端口 8080)"""
    print("🚀 服务器启动中...")
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8080,
        log_level="info",
        reload=True,
    )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 服务器已停止")
