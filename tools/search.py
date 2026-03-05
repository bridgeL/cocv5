from pydantic import BaseModel
from tool import Tool


# 定义工具输入参数模型
class SearchInput(BaseModel):
    query: str
    limit: int = 10


class SearchTool(Tool):
    """搜索工具"""

    name = "search"
    desc = "搜索互联网获取信息"
    input_schema = SearchInput

    def __init__(self):
        super().__init__()

    async def run(self, query: str, limit: int = 10) -> str:
        """执行搜索"""
        # 这里可以接入实际的搜索 API
        return f"[搜索结果] 查询 '{query}' 的前 {limit} 条模拟结果"
