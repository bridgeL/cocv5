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
