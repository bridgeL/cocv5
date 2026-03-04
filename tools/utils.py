"""工具公共工具函数"""

from mcp.types import Tool


def convert_tool_to_openai_function(tool: Tool) -> dict:
    """将MCP Tool转换为OpenAI function calling格式

    Args:
        tool: MCP Tool实例

    Returns:
        OpenAI function calling格式的字典
    """
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.inputSchema,
        },
    }


"""
tool_calls = [
    {
    "id": "",
    "type": "function",
    "function": {"name": "", "arguments": ""},
},
{
    "id": "",
    "type": "function",
    "function": {"name": "", "arguments": ""},
}
]
"""


async def execute_tool_calls(tools: list[Tool], tool_calls):
    # 检查工具中是否有该tool_call,如果有就调用，把结果放到
    pass
