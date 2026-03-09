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
from skills.weather_assistant import WeatherAssistantSkill
from skills.react_reasoning import ReActSkill
from skills.coc_character_generator import CoCCharacterGeneratorSkill


def create_agent(websocket: WebSocket, memory: Memory) -> Agent:
    """创建配置好的 Agent 实例

    Args:
        websocket: WebSocket 连接，用于发送消息到客户端
        memory: 记忆实例，用于存储会话历史

    Returns:
        配置好的 Agent 实例
    """
    # 创建技能管理工具（延迟设置 agent）
    skill_manager_tool = SkillManagerTool()

    tools = [
        CurrentTimeTool(),
        WeatherTool(),
        RollDiceTool(),
        SkillCheckTool(),
        skill_manager_tool,
    ]
    skills = [
        WeatherAssistantSkill(),
        ReActSkill(),
        CoCCharacterGeneratorSkill(),
    ]
    agent = Agent(
        tools=tools,
        skills=skills,
        memory=memory,
        prompt="你是一个专业、友好的AI助手，请用中文回答问题。",
        llm=llm,
        websocket=websocket,
    )

    # 为技能管理工具设置 agent 实例
    skill_manager_tool.set_agent(agent)

    return agent


# 创建 FastAPI 应用
app = FastAPI(title="WebSocket Demo HTTP Server")

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
    """
    await websocket.accept()

    # 创建连接（自动生成 session_id）
    conn = WebSocketConnection(websocket)

    # 创建资源
    memory = Memory(session_id=conn.session_id, db_path="memory.db")
    agent = create_agent(websocket, memory)

    # 注册 agent_chat 处理器
    async def handle_agent_chat(data: dict):
        user_message = data.get("message", "")
        print(
            f"[🤖] 收到来自 {conn.client} 的Agent提问 (session: {conn.session_id}): {user_message}"
        )
        try:
            await agent.chat(user_message)
            print(f"[✓] Agent 回复完成: {conn.client} (session: {conn.session_id})")
        except Exception as e:
            error_msg = f"Agent 调用失败: {str(e)}"
            print(f"[!] {error_msg}")
            await conn.send("error", {"error": error_msg})

    conn.on("agent_chat", handle_agent_chat)
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
