import asyncio
from llm_client import llm
from memory import Memory
from agent import Agent
from tools.current_time import CurrentTimeTool
from tools.weather import WeatherTool
from skills.weather_assistant import WeatherAssistantSkill


# 创建工具实例（无参数初始化）
tools = [
    CurrentTimeTool(),  # 无参数工具
    WeatherTool(),  # 天气查询工具
]

# 创建技能
skills = [
    WeatherAssistantSkill(),
]

# 初始化组件

memory = Memory(session_id="demo_session", db_path="memory.db")
agent = Agent(
    tools=tools,
    skills=skills,
    memory=memory,
    prompt="你是一个专业、友好的AI助手，请用中文回答问题。",
    llm=llm,
)


async def main():
    # 模拟对话
    await agent.chat("告诉我上海天气、北京天气")


if __name__ == "__main__":
    asyncio.run(main())
