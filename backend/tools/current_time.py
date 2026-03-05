import asyncio
from datetime import datetime
from tool import Tool


class CurrentTimeTool(Tool):
    """获取当前时间工具（无参数示例）"""

    name = "current_time"
    desc = "获取当前系统时间"
    input_schema = None  # 无参数

    async def run(self) -> dict:
        """获取当前时间"""
        await asyncio.sleep(3)  # 模拟网络延迟 3 秒
        now = datetime.now()
        return {
            "datetime": now.strftime('%Y-%m-%d %H:%M:%S'),
            "date": now.strftime('%Y-%m-%d'),
            "time": now.strftime('%H:%M:%S'),
            "timestamp": int(now.timestamp()),
        }
