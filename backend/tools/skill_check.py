import random
from pydantic import BaseModel, Field
from tool import Tool


class SkillCheckInput(BaseModel):
    """技能检定输入参数"""
    target: int = Field(
        ...,
        ge=1,
        le=100,
        description="目标值，范围1-100"
    )


class SkillCheckTool(Tool):
    """技能检定工具 - 掷骰1d100并与目标值对比"""

    name = "skill_check"
    desc = "进行技能检定，掷骰1d100并与目标值对比，返回结果和评价"
    input_schema = SkillCheckInput

    async def run(self, target: int) -> dict:
        """
        执行技能检定

        检定规则：
        - result = 100: 大失败
        - result = 1: 大成功
        - result > target: 失败
        - target >= result > target/2: 成功
        - target/2 >= result > target/5: 较难成功
        - target/5 >= result: 极难成功
        """
        # 掷骰 1d100
        result = random.randint(1, 100)

        # 判定结果
        evaluation = self._evaluate(result, target)

        return {
            "result": result,
            "target": target,
            "evaluation": evaluation,
        }

    def _evaluate(self, result: int, target: int) -> str:
        """根据结果和目标值返回评价"""
        if result == 100:
            return "大失败"
        if result == 1:
            return "大成功"
        if result > target:
            return "失败"
        if result > target / 2:
            return "成功"
        if result > target / 5:
            return "较难成功"
        return "极难成功"