import json
from typing import Any
from fastapi import WebSocket
from llm_client import LLMClient
from memory import Memory
from tool import Tool
from skill import Skill


class Agent:
    def __init__(
        self,
        tools: list[Tool],
        skills: list[Skill],
        memory: Memory,
        prompt: str,
        llm: LLMClient,
        websocket: WebSocket | None = None,
    ):
        self.tools = tools
        self.skills = skills
        self.memory = memory
        self.prompt = prompt
        self.llm = llm
        self.websocket = websocket

    async def _send_ws_message(self, msg_type: str, data: dict):
        """通过 WebSocket 发送消息（如果已配置）"""
        if self.websocket:
            await self.websocket.send_text(json.dumps({"type": msg_type, **data}))

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
        通过 WebSocket 发送各类消息事件
        返回完整响应文本
        """
        # 发送 received 消息，表示本轮 chat 开始
        await self._send_ws_message("received", {"message": query})

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
        full_response = ""

        while True:
            # 每次调用获取独立的流结果对象，避免并发冲突
            stream_gen, stream_result = await self.llm.astream(messages, tools)

            # 流式发送 chunk 消息
            async for chunk in stream_gen:
                await self._send_ws_message("chunk", {"content": chunk})

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
            # 发送 tool_before 消息
            tool_calls_info = []
            for tc in tool_calls:
                func = tc["function"]
                tool_calls_info.append({
                    "id": tc["id"],
                    "name": func["name"],
                    "arguments": func["arguments"],
                })
            await self._send_ws_message("tool_before", {"tool_calls": tool_calls_info})

            # 将助手消息（含工具调用）加入内存
            self.memory.add_assistant_message(
                content=full_response,
                tool_calls=tool_calls,
            )

            # 执行工具并添加结果到内存
            tool_results = []
            for tc in tool_calls:
                tool_call_id = tc["id"]
                func_name = tc["function"]["name"]
                func_args = tc["function"]["arguments"]

                result = await self._execute_tool(func_name, func_args)
                self.memory.add_tool_result(tool_call_id, result)
                tool_results.append({
                    "id": tool_call_id,
                    "name": func_name,
                    "result": result,
                })

            # 发送 tool_after 消息
            await self._send_ws_message("tool_after", {"results": tool_results})

            # 重新构建消息并调用 LLM
            messages = [{"role": "system", "content": system_prompt}]
            messages.extend(self.memory.get_messages())

        # 发送 complete 消息，表示本轮 chat 结束
        await self._send_ws_message("complete", {"response": full_response})

        return full_response

    async def _execute_tool(self, func_name: str, func_args: str) -> dict:
        """执行工具并返回dict结果，从本地 tools 列表中查找"""
        # 解析参数
        try:
            args = json.loads(func_args) if func_args else None
        except json.JSONDecodeError:
            return {"error": "参数解析失败", "func_name": func_name, "args": func_args}

        # 从 tools 列表中查找工具
        tool = None
        for t in self.tools:
            if t.name == func_name:
                tool = t
                break

        if tool is None:
            return {"error": "未知工具", "func_name": func_name}

        # 校验参数
        if tool.input_schema is None:
            # 无参数工具，args 必须为 None 或空 dict
            if args is not None and args != {}:
                return {"error": "工具不需要参数", "func_name": func_name, "args": args}
            args = {}
        else:
            # 有参数工具，校验 args 是否符合 schema
            try:
                if args is None:
                    args = {}
                validated = tool.input_schema(**args)
                args = validated.model_dump()
            except Exception as e:
                return {"error": "参数校验失败", "func_name": func_name, "message": str(e)}

        # 执行工具
        try:
            result = await tool.run(**args)
            # 确保返回的是dict
            if not isinstance(result, dict):
                return {"error": "工具返回类型错误", "func_name": func_name, "message": "工具必须返回dict类型"}
            return result
        except Exception as e:
            return {"error": "工具执行错误", "func_name": func_name, "message": str(e)}
