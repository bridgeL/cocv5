import random
from pydantic import BaseModel, Field
from tool import Tool


class CoCCharacterAttributesInput(BaseModel):
    """CoC角色基础属性生成输入参数"""
    age_group: str = Field(
        default="adult",
        description="年龄段，默认为 adult（20-39岁），可选: young, adult, middle, old"
    )


class CoCCharacterAttributesTool(Tool):
    """CoC 7版角色基础属性生成工具 - 一键生成所有基础属性"""

    name = "coc_character_attributes"
    desc = "生成《克苏鲁的呼唤》第七版角色基础属性（STR/CON/DEX/APP/POW/SIZ/INT/EDU/Luck），自动计算全额值（×5）"
    input_schema = CoCCharacterAttributesInput

    async def run(self, age_group: str = "adult") -> dict:
        """
        生成 CoC 7版角色的所有基础属性

        属性生成规则:
        - STR/CON/DEX/APP/POW: 3d6 × 5
        - SIZ/INT/EDU: (2d6+6) × 5
        - Luck: 3d6 × 5

        Args:
            age_group: 年龄段，影响年龄调整（暂未实现，预留参数）

        Returns:
            包含所有基础属性的字典
        """
        # 生成基础属性（原始骰点 × 5）
        attributes = {
            "STR": self._roll_attribute("3d6"),
            "CON": self._roll_attribute("3d6"),
            "DEX": self._roll_attribute("3d6"),
            "APP": self._roll_attribute("3d6"),
            "POW": self._roll_attribute("3d6"),
            "SIZ": self._roll_attribute("2d6+6"),
            "INT": self._roll_attribute("2d6+6"),
            "EDU": self._roll_attribute("2d6+6"),
            "Luck": self._roll_attribute("3d6"),
        }

        # 计算派生属性
        derived = self._calculate_derived(attributes)

        return {
            "success": True,
            "age_group": age_group,
            "attributes": attributes,
            "derived": derived,
            # 便于AI读取的格式
            "summary": self._format_summary(attributes, derived),
        }

    def _roll_attribute(self, expression: str) -> dict:
        """根据表达式生成属性值"""
        if expression == "3d6":
            rolls = [random.randint(1, 6) for _ in range(3)]
            base = sum(rolls)
        elif expression == "2d6+6":
            rolls = [random.randint(1, 6) for _ in range(2)]
            base = sum(rolls) + 6
        else:
            raise ValueError(f"不支持的表达式: {expression}")

        return {
            "base": base,  # 原始骰点总和
            "full": base * 5,  # 全额值 (×5)
            "half": (base * 5) // 2,  # 半值
            "fifth": (base * 5) // 5,  # 五分之一值
            "rolls": rolls,  # 原始骰子结果
        }

    def _calculate_derived(self, attrs: dict) -> dict:
        """计算派生属性"""
        str_full = attrs["STR"]["full"]
        con_full = attrs["CON"]["full"]
        siz_full = attrs["SIZ"]["full"]
        dex_full = attrs["DEX"]["full"]
        pow_full = attrs["POW"]["full"]

        # HP = (CON + SIZ) / 10，向下取整
        hp = (con_full + siz_full) // 10

        # MP = POW / 5，向下取整
        mp = pow_full // 5

        # SAN = POW
        san = pow_full

        # MOV 计算
        if dex_full < siz_full and str_full < siz_full:
            mov = 7
        elif dex_full >= siz_full or str_full >= siz_full:
            mov = 8
        else:  # dex > siz and str > siz
            mov = 9

        # Build 和 DB 计算
        str_siz_sum = str_full + siz_full
        if str_siz_sum <= 64:
            build = -2
            db = "-2"
        elif str_siz_sum <= 84:
            build = -1
            db = "-1"
        elif str_siz_sum <= 124:
            build = 0
            db = "0"
        elif str_siz_sum <= 164:
            build = 1
            db = "+1d4"
        elif str_siz_sum <= 204:
            build = 2
            db = "+1d6"
        else:
            build = 3
            db = "+2d6"

        return {
            "HP": hp,
            "MP": mp,
            "SAN": san,
            "MOV": mov,
            "Build": build,
            "DB": db,
        }

    def _format_summary(self, attrs: dict, derived: dict) -> str:
        """生成便于AI读取的摘要"""
        lines = [
            "【调查员基础属性】",
            f"力量 STR: {attrs['STR']['full']}/{attrs['STR']['half']}/{attrs['STR']['fifth']}",
            f"体质 CON: {attrs['CON']['full']}/{attrs['CON']['half']}/{attrs['CON']['fifth']}",
            f"体型 SIZ: {attrs['SIZ']['full']}/{attrs['SIZ']['half']}/{attrs['SIZ']['fifth']}",
            f"敏捷 DEX: {attrs['DEX']['full']}/{attrs['DEX']['half']}/{attrs['DEX']['fifth']}",
            f"外貌 APP: {attrs['APP']['full']}/{attrs['APP']['half']}/{attrs['APP']['fifth']}",
            f"智力 INT: {attrs['INT']['full']}/{attrs['INT']['half']}/{attrs['INT']['fifth']}",
            f"意志 POW: {attrs['POW']['full']}/{attrs['POW']['half']}/{attrs['POW']['fifth']}",
            f"教育 EDU: {attrs['EDU']['full']}/{attrs['EDU']['half']}/{attrs['EDU']['fifth']}",
            f"幸运 Luck: {attrs['Luck']['full']}/{attrs['Luck']['half']}/{attrs['Luck']['fifth']}",
            "",
            "【派生属性】",
            f"HP: {derived['HP']} | MP: {derived['MP']} | SAN: {derived['SAN']}",
            f"MOV: {derived['MOV']} | Build: {derived['Build']} | DB: {derived['DB']}",
        ]
        return "\n".join(lines)
