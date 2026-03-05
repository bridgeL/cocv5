import json
import asyncio
from pydantic import BaseModel
from typing import Any
from llm_client import llm, LLMClient
from memory import Memory
from tool import Tool
from skill import Skill
from tools.search import SearchTool
from tools.calculator import CalculatorTool
from tools.current_time import CurrentTimeTool
from tools.weather import WeatherTool


class Agent:
    def __init__(
        self,
        tools: list[Tool],
        skills: list[Skill],
        memory: Memory,
        prompt: str,
        llm: LLMClient,
    ):
        self.tools = tools
        self.skills = skills
        self.memory = memory
        self.prompt = prompt
        self.llm = llm

    def build_system_prompt(self) -> str:
        """构建完整的系统提示词"""
        sections = []

        # 1. 基础角色设定
        sections.append("# 角色设定")
        sections.append(self.prompt)

        # 2. 技能说明
        if self.skills:
            sections.append("\n# 你的技能")
            for skill in self.skills:
                sections.append(skill.to_prompt_section())

        # 3. 工具说明
        if self.tools:
            sections.append("\n# 可用工具")
            sections.append("你可以使用以下工具来完成任务，请根据需要调用：")
            for tool in self.tools:
                sections.append(f"\n- {tool.name}: {tool.desc}")

        # 4. 通用约束
        sections.append("\n# 重要约束")
        sections.append(
            """
1. 请根据用户的请求，结合你的技能和可用工具来回答问题
2. 如果需要使用工具，请直接调用，不要询问用户确认
3. 如果工具返回结果，请基于结果给出完整回答
"""
        )

        return "\n".join(sections)

    def build_tools_for_llm(self) -> list[dict[str, Any]]:
        """构建OpenAI格式的工具列表"""
        return [tool.to_openai_format() for tool in self.tools]

    async def chat(self, query: str) -> str:
        """
        与Agent对话
        返回完整响应文本
        """
        # 1. 将用户消息加入内存
        self.memory.add_user_message(query)

        # 2. 构建系统提示词
        system_prompt = self.build_system_prompt()

        # 3. 构建完整消息列表
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(self.memory.get_messages())

        # 4. 构建工具参数
        tools = self.build_tools_for_llm()

        # 5. 流式调用LLM（支持多轮工具调用，直到AI不再调用工具）
        print("=" * 50)
        print(f"用户: {query}")
        print("-" * 50)
        print("助手: ", end="", flush=True)

        full_response = ""

        while True:
            # 每次调用获取独立的流结果对象，避免并发冲突
            stream_gen, stream_result = await self.llm.astream(messages, tools)

            async for chunk in stream_gen:
                print(chunk, end="", flush=True)

            print()  # 换行

            # 从独立结果对象获取完整响应和工具调用
            full_response = stream_result.full_response
            tool_calls = stream_result.tool_calls

            # 检查是否有工具调用
            if not tool_calls:
                # 没有工具调用，将助手响应加入内存并结束
                self.memory.add_assistant_message(
                    content=full_response,
                    tool_calls=None,
                )
                break

            # 有工具调用，需要执行工具并继续对话
            print(f"\n[工具调用] {len(tool_calls)} 个")
            for tc in tool_calls:
                func = tc["function"]
                print(f"  - {func['name']}: {func['arguments']}")

            # 将助手消息（含工具调用）加入内存
            self.memory.add_assistant_message(
                content=full_response,
                tool_calls=tool_calls,
            )

            # 执行工具并添加结果到内存
            for tc in tool_calls:
                tool_call_id = tc["id"]
                func_name = tc["function"]["name"]
                func_args = tc["function"]["arguments"]

                result = await self._execute_tool(func_name, func_args)
                self.memory.add_tool_result(tool_call_id, result)

            # 重新构建消息并调用 LLM
            print("助手: ", end="", flush=True)
            messages = [{"role": "system", "content": system_prompt}]
            messages.extend(self.memory.get_messages())

        return full_response

    async def _execute_tool(self, func_name: str, func_args: str) -> str:
        """执行工具并返回结果，从本地 tools 列表中查找"""
        # 解析参数
        try:
            args = json.loads(func_args) if func_args else None
        except json.JSONDecodeError:
            return f"[错误] 工具参数解析失败: {func_args}"

        # 从 tools 列表中查找工具
        tool = None
        for t in self.tools:
            if t.name == func_name:
                tool = t
                break

        if tool is None:
            return f"[错误] 未知工具: {func_name}"

        # 校验参数
        if tool.input_schema is None:
            # 无参数工具，args 必须为 None 或空 dict
            if args is not None and args != {}:
                return f"[错误] 工具 '{func_name}' 不需要参数，但传入了: {args}"
            args = {}
        else:
            # 有参数工具，校验 args 是否符合 schema
            try:
                if args is None:
                    args = {}
                validated = tool.input_schema(**args)
                args = validated.model_dump()
            except Exception as e:
                return f"[错误] 工具 '{func_name}' 参数校验失败: {str(e)}"

        # 执行工具
        try:
            result = await tool.run(**args)
            return str(result)
        except Exception as e:
            return f"[工具执行错误] {func_name}: {str(e)}"


# ==================== 使用示例 ====================

# 创建工具实例（无参数初始化）
tools = [
    SearchTool(),
    CalculatorTool(),
    CurrentTimeTool(),  # 无参数工具
    WeatherTool(),  # 天气查询工具
]

# 创建技能
skills = [
    Skill(
        name="天气助手",
        desc="帮助用户获取实时天气",
        content="""
工作流程
- 如果用户没有说明时间，那么调用工具查询当前时间
- 根据上一步的时间，调用工具查询用户指定地点的天气
- 尽可能简短的告知用户天气信息，例如：东京：18° 晴
""",
    )
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
    # print()
    # await agent.chat("帮我分析data.csv的内容")


if __name__ == "__main__":
    asyncio.run(main())
