class Skill:
    """技能基类，子类需定义 name, desc, content 类属性

    子类必须定义的类属性:
        name: str - 技能名称
        desc: str - 技能描述
        content: str - 技能详细内容/工作流程

    可选的类属性:
        installed: bool - 是否启用该技能，默认为 False
                         为 True 时加载完整信息到提示词
                         为 False 时只加载 name 和 desc

    示例:
        class MySkill(Skill):
            name = "我的技能"
            desc = "这是一个示例技能"
            content = "工作流程..."
            installed = True
    """

    # 子类必须定义的类属性
    name: str = ""
    desc: str = ""
    content: str = ""

    # 可选的类属性
    installed: bool = False

    def __init__(self):
        """无参数初始化，验证子类是否正确实现了必要的属性"""
        if not self.name:
            raise NotImplementedError(f"{self.__class__.__name__} 必须定义 name 类属性")
        if not self.desc:
            raise NotImplementedError(f"{self.__class__.__name__} 必须定义 desc 类属性")
        if not self.content:
            raise NotImplementedError(f"{self.__class__.__name__} 必须定义 content 类属性")

    def to_prompt_section(self) -> str:
        """转换为提示词段落

        如果 installed 为 True，返回完整的技能信息（包括 content）
        如果 installed 为 False，只返回 name 和 desc
        """
        if self.installed:
            return f"""
## {self.name}
- 描述: {self.desc}
- 能力详情:
{self.content}
"""
        else:
            return f"""
## {self.name}
- 描述: {self.desc}
"""