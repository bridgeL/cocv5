import random
from pydantic import BaseModel
from tool import Tool


# 定义天气工具输入参数模型
class WeatherInput(BaseModel):
    city: str


class WeatherTool(Tool):
    """查询天气工具"""

    name = "weather"
    desc = "查询指定城市的天气信息"
    input_schema = WeatherInput

    def __init__(self):
        super().__init__()

    async def run(self, city: str) -> str:
        """查询天气（返回模拟数据）"""
        # 模拟天气数据
        weather_data = {
            "北京": {"temp": 22, "condition": "晴", "humidity": 45, "wind": "北风3级"},
            "上海": {"temp": 25, "condition": "多云", "humidity": 60, "wind": "东南风2级"},
            "广州": {"temp": 28, "condition": "小雨", "humidity": 75, "wind": "南风3级"},
            "深圳": {"temp": 29, "condition": "阴", "humidity": 70, "wind": "东风2级"},
            "杭州": {"temp": 24, "condition": "晴", "humidity": 55, "wind": "北风2级"},
            "成都": {"temp": 20, "condition": "阴", "humidity": 65, "wind": "静风"},
        }

        # 查找城市天气，如果不存在则生成随机模拟数据
        if city in weather_data:
            data = weather_data[city]
        else:
            conditions = ["晴", "多云", "阴", "小雨"]
            data = {
                "temp": random.randint(15, 32),
                "condition": random.choice(conditions),
                "humidity": random.randint(40, 80),
                "wind": random.choice(["北风2级", "南风2级", "东风1级", "静风"]),
            }

        return f"{city}: {data['temp']}°, {data['condition']}, 湿度{data['humidity']}%, {data['wind']}"
