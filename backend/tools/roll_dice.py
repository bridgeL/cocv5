import random
import re
from pydantic import BaseModel, Field
from tool import Tool


class RollDiceInput(BaseModel):
    """掷骰输入参数"""
    expression: str = Field(
        ...,
        description="骰子表达式，格式如 '2d6+2', '1d20', '3d8-1' 等"
    )


class RollDiceTool(Tool):
    """掷骰工具 - 解析骰子表达式并执行掷骰"""

    name = "roll_dice"
    desc = "根据骰子表达式进行掷骰，支持格式如 2d6+2, 1d20, 3d8-1 等"
    input_schema = RollDiceInput

    async def run(self, expression: str) -> dict:
        """
        解析骰子表达式并执行掷骰

        表达式格式:
        - NdM: N 个 M 面骰子 (如 2d6 = 两个6面骰)
        - NdM+X: 加上修正值 (如 2d6+2)
        - NdM-X: 减去修正值 (如 1d20-1)
        """
        # 解析表达式
        dice_count, dice_sides, modifier = self._parse_expression(expression.strip())

        # 执行掷骰
        rolls = [random.randint(1, dice_sides) for _ in range(dice_count)]

        # 计算总和
        total = sum(rolls) + modifier

        return {
            "expression": expression,
            "rolls": rolls,
            "modifier": modifier,
            "total": total,
        }

    def _parse_expression(self, expression: str) -> tuple[int, int, int]:
        """
        解析骰子表达式

        Returns:
            (骰子数量, 骰子面数, 修正值)

        Raises:
            ValueError: 表达式格式无效
        """
        # 支持格式: NdM, NdM+X, NdM-X (N,M,X 为正整数)
        pattern = r'^(\d+)d(\d+)(?:([+-])(\d+))?$'
        match = re.match(pattern, expression.lower())

        if not match:
            raise ValueError(
                f"无效的骰子表达式: {expression}. "
                "支持的格式如: 2d6, 1d20, 3d8+2, 2d6-1"
            )

        dice_count = int(match.group(1))
        dice_sides = int(match.group(2))
        modifier = 0

        if match.group(3) and match.group(4):
            modifier_value = int(match.group(4))
            if match.group(3) == '+':
                modifier = modifier_value
            else:
                modifier = -modifier_value

        # 验证参数
        if dice_count < 1:
            raise ValueError("骰子数量必须至少为 1")
        if dice_sides < 2:
            raise ValueError("骰子面数必须至少为 2")
        if dice_count > 100:
            raise ValueError("骰子数量不能超过 100")
        if dice_sides > 1000:
            raise ValueError("骰子面数不能超过 1000")

        return dice_count, dice_sides, modifier