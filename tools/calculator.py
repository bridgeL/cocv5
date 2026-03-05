from pydantic import BaseModel
from tool import Tool


# 定义工具输入参数模型
class CalculatorInput(BaseModel):
    expression: str


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
