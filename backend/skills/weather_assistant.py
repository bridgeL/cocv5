from skill import Skill


class WeatherAssistantSkill(Skill):
    """天气助手技能"""

    name = "天气助手"
    desc = "帮助用户获取实时天气"
    installed = False
    content = """
工作流程
- 如果用户没有说明时间，那么调用工具查询当前时间
- 根据上一步的时间，调用工具查询用户指定地点的天气
- 尽可能简短的告知用户天气信息，例如：东京：18° 晴
"""
