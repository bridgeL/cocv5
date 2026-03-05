import asyncio
import json
import sqlite3
from datetime import datetime
from pydantic import BaseModel
from openai import AsyncOpenAI
from typing import AsyncGenerator, Dict, List, Any, Optional
from config import MODEL_API_KEY, MODEL_URL, MODEL_NAME


class Tool:
    """工具基类，子类需定义 name, desc 类属性，并重写 run 方法

    input_schema 为可选类属性：
    - 定义为 type[BaseModel] 表示工具有参数
    - 定义为 None 表示工具无参数
    """

    # 子类必须定义的类属性
    name: str = ""
    desc: str = ""
    input_schema: type[BaseModel] | None = None

    def __init__(self):
        """无参数初始化，子类可重写"""
        # 验证子类是否正确实现了必要的属性
        if not self.name:
            raise NotImplementedError(f"{self.__class__.__name__} 必须定义 name 类属性")
        if not self.desc:
            raise NotImplementedError(f"{self.__class__.__name__} 必须定义 desc 类属性")
        # input_schema 可以为 None，表示工具无参数

    async def run(self, **kwargs) -> str:
        """执行工具，子类必须重写此方法"""
        raise NotImplementedError(f"{self.__class__.__name__} 必须实现 run 方法")

    def to_openai_format(self) -> Dict[str, Any]:
        """转换为OpenAI工具格式"""
        if self.input_schema is not None:
            parameters = self.input_schema.model_json_schema()
        else:
            # 无参数工具，返回空对象
            parameters = {"type": "object", "properties": {}}
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.desc,
                "parameters": parameters,
            },
        }


class Memory:
    """内存类，存储对话历史到SQLite数据库"""

    def __init__(self, session_id: str, db_path: str = "memory.db"):
        self.session_id = session_id
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """初始化数据库表"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    tool_calls TEXT,
                    tool_call_id TEXT,
                    create_time TEXT NOT NULL
                )
            """)
            conn.commit()

    def _insert_message(
        self,
        role: str,
        content: str,
        tool_calls: Optional[List[Dict]] = None,
        tool_call_id: Optional[str] = None,
    ):
        """插入消息到数据库，实时保存"""
        create_time = int(datetime.now().timestamp() * 1000)
        tool_calls_json = json.dumps(tool_calls, ensure_ascii=False) if tool_calls else None

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO memory (session_id, role, content, tool_calls, tool_call_id, create_time)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (self.session_id, role, content, tool_calls_json, tool_call_id, create_time),
            )
            conn.commit()

    def add_user_message(self, content: str):
        """添加用户消息"""
        self._insert_message(role="user", content=content)

    def add_assistant_message(
        self, content: str, tool_calls: Optional[List[Dict]] = None
    ):
        """添加助手消息"""
        self._insert_message(role="assistant", content=content, tool_calls=tool_calls)

    def add_tool_result(self, tool_call_id: str, content: str):
        """添加工具执行结果"""
        self._insert_message(role="tool", content=content, tool_call_id=tool_call_id)

    def get_messages(self) -> List[Dict[str, Any]]:
        """获取所有历史消息"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT role, content, tool_calls, tool_call_id FROM memory
                WHERE session_id = ?
                ORDER BY id ASC
                """,
                (self.session_id,),
            )
            rows = cursor.fetchall()

        messages = []
        for role, content, tool_calls_json, tool_call_id in rows:
            msg: Dict[str, Any] = {"role": role, "content": content}
            if tool_calls_json:
                msg["tool_calls"] = json.loads(tool_calls_json)
            if tool_call_id:
                msg["tool_call_id"] = tool_call_id
            messages.append(msg)
        return messages

    def clear(self):
        """清空当前session的历史"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "DELETE FROM memory WHERE session_id = ?",
                (self.session_id,),
            )
            conn.commit()


class Skill:
    """技能类，定义Agent的专业能力"""

    def __init__(self, name: str, desc: str, content: str):
        self.name = name
        self.desc = desc
        self.content = content

    def to_prompt_section(self) -> str:
        """转换为提示词段落"""
        return f"""
## {self.name}
- 描述: {self.desc}
- 能力详情:
{self.content}
"""


class LLM:
    def __init__(self, url: str, api_key: str, model_name: str):
        self.client = AsyncOpenAI(base_url=url, api_key=api_key)
        self.model_name = model_name
        self.full_response: str = ""
        self.tool_calls: List[Dict[str, Any]] = []

    async def astream(self, messages, tools):
        """异步流式调用LLM"""
        self.full_response = ""
        self.tool_calls = []
        tool_calls_data: Dict[int, Dict] = {}

        stream = await self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            tools=tools,
            stream=True,
        )

        async for chunk in stream:
            delta = chunk.choices[0].delta

            if delta.content:
                content_chunk = delta.content
                self.full_response += content_chunk
                yield content_chunk

            if delta.tool_calls:
                for tc in delta.tool_calls:
                    index = tc.index

                    if index not in tool_calls_data:
                        tool_calls_data[index] = {
                            "id": "",
                            "type": "function",
                            "function": {"name": "", "arguments": ""},
                        }

                    if tc.id:
                        tool_calls_data[index]["id"] = tc.id
                    if tc.function:
                        f = tool_calls_data[index]["function"]
                        if tc.function.name:
                            f["name"] += tc.function.name
                        if tc.function.arguments:
                            f["arguments"] += tc.function.arguments

        self.tool_calls = [tool_calls_data[i] for i in sorted(tool_calls_data.keys())]


class Agent:
    def __init__(
        self,
        tools: List[Tool],
        skills: List[Skill],
        memory: Memory,
        prompt: str,
        llm: LLM,
    ):
        self.tools = tools
        self.skills = skills
        self.memory = memory
        self.prompt = prompt
        self.llm = llm

    def _build_system_prompt(self) -> str:
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

    def _build_tools_for_llm(self) -> List[Dict[str, Any]]:
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
        system_prompt = self._build_system_prompt()

        # 3. 构建完整消息列表
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(self.memory.get_messages())

        # 4. 构建工具参数
        tools = self._build_tools_for_llm()

        # 5. 流式调用LLM（支持多轮工具调用，直到AI不再调用工具）
        print("=" * 50)
        print(f"用户: {query}")
        print("-" * 50)
        print("助手: ", end="", flush=True)

        while True:
            async for chunk in self.llm.astream(messages, tools):
                print(chunk, end="", flush=True)

            print()  # 换行

            # 检查是否有工具调用
            if not self.llm.tool_calls:
                # 没有工具调用，将助手响应加入内存并结束
                self.memory.add_assistant_message(
                    content=self.llm.full_response,
                    tool_calls=None,
                )
                break

            # 有工具调用，需要执行工具并继续对话
            print(f"\n[工具调用] {len(self.llm.tool_calls)} 个")
            for tc in self.llm.tool_calls:
                func = tc["function"]
                print(f"  - {func['name']}: {func['arguments']}")

            # 将助手消息（含工具调用）加入内存
            self.memory.add_assistant_message(
                content=self.llm.full_response,
                tool_calls=self.llm.tool_calls,
            )

            # 执行工具并添加结果到内存
            for tc in self.llm.tool_calls:
                tool_call_id = tc["id"]
                func_name = tc["function"]["name"]
                func_args = tc["function"]["arguments"]

                result = await self._execute_tool(func_name, func_args)
                self.memory.add_tool_result(tool_call_id, result)

            # 重新构建消息并调用 LLM
            print("助手: ", end="", flush=True)
            messages = [{"role": "system", "content": system_prompt}]
            messages.extend(self.memory.get_messages())

        return self.llm.full_response

    async def _execute_tool(self, func_name: str, func_args: str) -> str:
        """执行工具并返回结果，从本地 tools 列表中查找"""
        # 解析参数
        try:
            args = json.loads(func_args)
        except json.JSONDecodeError:
            args = {}

        # 从 tools 列表中查找工具
        tool = None
        for t in self.tools:
            if t.name == func_name:
                tool = t
                break

        if tool is None:
            return f"[错误] 未知工具: {func_name}"

        # 执行工具
        try:
            result = await tool.run(**args)
            return str(result)
        except Exception as e:
            return f"[工具执行错误] {func_name}: {str(e)}"


# ==================== 使用示例 ====================


# 定义工具输入参数模型
class SearchInput(BaseModel):
    query: str
    limit: int = 10


class CalculatorInput(BaseModel):
    expression: str


# 定义具体工具类（继承模式）
class SearchTool(Tool):
    """搜索工具"""

    name = "search"
    desc = "搜索互联网获取信息"
    input_schema = SearchInput

    def __init__(self):
        super().__init__()

    async def run(self, query: str, limit: int = 10) -> str:
        """执行搜索"""
        # 这里可以接入实际的搜索 API
        return f"[搜索结果] 查询 '{query}' 的前 {limit} 条模拟结果"


class CalculatorTool(Tool):
    """计算器工具"""

    name = "calculator"
    desc = "计算数学表达式"
    input_schema = CalculatorInput

    def __init__(self):
        super().__init__()

    async def run(self, expression: str) -> str:
        """执行计算"""
        try:
            # 安全计算：只允许数字和基本运算符
            allowed_chars = set("0123456789+-*/.() ")
            if not all(c in allowed_chars for c in expression):
                return "[错误] 表达式包含非法字符"
            result = eval(expression)
            return f"{expression} = {result}"
        except Exception as e:
            return f"[计算错误] {str(e)}"


class CurrentTimeTool(Tool):
    """获取当前时间工具（无参数示例）"""

    name = "current_time"
    desc = "获取当前系统时间"
    input_schema = None  # 无参数

    def __init__(self):
        super().__init__()

    async def run(self) -> str:
        """获取当前时间"""
        from datetime import datetime
        return f"当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"


# 创建工具实例（无参数初始化）
tools = [
    SearchTool(),
    CalculatorTool(),
    CurrentTimeTool(),  # 无参数工具
]

# 创建技能
skills = [
    Skill(
        name="编程助手",
        desc="帮助用户解决编程问题",
        content="""
- 擅长Python、JavaScript等编程语言
- 能够解释代码、调试错误、优化性能
- 提供清晰的代码示例和解释
""",
    ),
    Skill(
        name="数据分析",
        desc="帮助分析数据",
        content="""
- 理解常见的数据格式（CSV、JSON等）
- 提供数据清洗、转换的建议
- 推荐合适的可视化方法
""",
    ),
]

# 初始化组件
llm = LLM(MODEL_URL, MODEL_API_KEY, MODEL_NAME)
memory = Memory(session_id="demo_session", db_path="memory.db")
agent = Agent(
    tools=tools,
    skills=skills,
    memory=memory,
    prompt="你是一个专业、友好的AI助手，擅长编程和数据分析。请用中文回答问题。",
    llm=llm,
)


async def main():
    # 模拟对话
    await agent.chat("告诉我当前时间和今日天气")
    print()
    await agent.chat("帮我分析data.csv的内容")


if __name__ == "__main__":
    asyncio.run(main())
