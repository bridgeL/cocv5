class Skill:
    """技能类，定义Agent的专业能力

    子类必须定义以下类属性:
        name: str - 技能名称
        desc: str - 技能描述
        content: str - 技能详细内容/工作流程

    示例:
        class MySkill(Skill):
            name = "我的技能"
            desc = "这是一个示例技能"
            content = "工作流程..."
    """

    name: str = ""
    desc: str = ""
    content: str = ""

    def __init__(self):
        """无参数初始化，验证子类是否正确实现了必要的属性"""
        if not self.name:
            raise NotImplementedError(f"{self.__class__.__name__} 必须定义 name 类属性")
        if not self.desc:
            raise NotImplementedError(f"{self.__class__.__name__} 必须定义 desc 类属性")
        if not self.content:
            raise NotImplementedError(f"{self.__class__.__name__} 必须定义 content 类属性")

    def to_prompt_section(self) -> str:
        """转换为提示词段落"""
        return f"""
## {self.name}
- 描述: {self.desc}
- 能力详情:
{self.content}
"""
