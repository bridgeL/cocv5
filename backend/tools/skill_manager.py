from pydantic import BaseModel, Field
from typing import Literal
from tool import Tool
from agent import Agent


class SkillManagerInput(BaseModel):
    """技能管理输入参数"""
    mode: Literal["install", "uninstall"] = Field(
        ...,
        description="操作模式：install 启用技能，uninstall 禁用技能"
    )
    skill_name: str = Field(
        ...,
        description="要操作的技能名称"
    )


class SkillManagerTool(Tool):
    """技能管理工具 - 动态启用或禁用 Agent 的技能"""

    name = "skill_manager"
    desc = "管理 Agent 加载的技能，可以启用(install)或禁用(uninstall)指定技能"
    input_schema = SkillManagerInput

    def __init__(self, agent: Agent = None):
        """初始化工具，可选传入 agent 实例，也可后续设置"""
        super().__init__()
        self.agent = agent

    def set_agent(self, agent: Agent):
        """设置 agent 实例（用于延迟注入）"""
        self.agent = agent

    async def run(self, mode: str, skill_name: str) -> dict:
        """
        修改指定技能的 installed 状态

        Args:
            mode: "install" 或 "uninstall"
            skill_name: 技能名称

        Returns:
            操作结果
        """
        # 检查 agent 是否已设置
        if self.agent is None:
            return {
                "success": False,
                "error": "SkillManagerTool 未设置 agent 实例"
            }

        # 在 agent.skills 中查找对应名称的技能
        target_skill = None
        for skill in self.agent.skills:
            if skill.name == skill_name:
                target_skill = skill
                break

        if target_skill is None:
            available_skills = [s.name for s in self.agent.skills]
            return {
                "success": False,
                "error": f"未找到名为 '{skill_name}' 的技能",
                "available_skills": available_skills
            }

        # 根据 mode 修改 installed 状态
        if mode == "install":
            if target_skill.installed:
                return {
                    "success": True,
                    "message": f"技能 '{skill_name}' 已经是启用状态",
                    "skill_name": skill_name,
                    "installed": True
                }
            target_skill.installed = True
            return {
                "success": True,
                "message": f"成功启用技能 '{skill_name}'",
                "skill_name": skill_name,
                "installed": True
            }
        elif mode == "uninstall":
            if not target_skill.installed:
                return {
                    "success": True,
                    "message": f"技能 '{skill_name}' 已经是禁用状态",
                    "skill_name": skill_name,
                    "installed": False
                }
            target_skill.installed = False
            return {
                "success": True,
                "message": f"成功禁用技能 '{skill_name}'",
                "skill_name": skill_name,
                "installed": False
            }
        else:
            return {
                "success": False,
                "error": f"无效的模式 '{mode}'，只能是 'install' 或 'uninstall'"
            }
