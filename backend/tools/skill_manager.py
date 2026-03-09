from pydantic import BaseModel, Field
from tool import Tool
from skill import Skill


class SkillManagerInput(BaseModel):
    """技能管理输入参数"""
    skill_name: str = Field(
        ...,
        description="要获取的技能名称"
    )


class SkillManagerTool(Tool):
    """技能管理工具 - 获取指定技能的完整内容"""

    name = "skill_manager"
    desc = "根据技能名称获取该技能的完整能力和工作流程信息，用于在使用某个技能前先加载了解该技能"
    input_schema = SkillManagerInput

    def __init__(self, skills: list[Skill]):
        """初始化工具，传入技能列表

        Args:
            skills: Agent 加载的所有技能列表
        """
        super().__init__()
        self.skills = skills

    async def run(self, skill_name: str) -> dict:
        """
        根据技能名称返回该技能的完整内容

        Args:
            skill_name: 技能名称

        Returns:
            技能的完整信息（name, desc, content）
        """
        # 在传入的技能列表中查找
        target_skill = None
        for skill in self.skills:
            if skill.name == skill_name:
                target_skill = skill
                break

        if target_skill is None:
            available_skills = [s.name for s in self.skills]
            return {
                "success": False,
                "error": f"未找到名为 '{skill_name}' 的技能",
                "available_skills": available_skills
            }

        return {
            "success": True,
            "skill": {
                "name": target_skill.name,
                "desc": target_skill.desc,
                "content": target_skill.content
            }
        }
