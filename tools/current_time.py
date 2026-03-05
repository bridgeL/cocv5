from tool import Tool


class CurrentTimeTool(Tool):
    """获取当前时间工具（无参数示例）"""

    name = "current_time"
    desc = "获取当前系统时间"
    input_schema = None  # 无参数

    def __init__(self):
        super().__init__()

    async def run(self) -> str:
        """获取当前时间"""
        from datetime import datetime

        return f"当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
