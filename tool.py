from pydantic import BaseModel
from typing import Any


class Tool:
    """工具基类，子类需定义 name, desc 类属性，并重写 run 方法

    input_schema 为可选类属性：
    - 定义为 type[BaseModel] 表示工具有参数
    - 定义为 None 表示工具无参数
    """

    # 子类必须定义的类属性
    name: str = ""
    desc: str = ""
    input_schema: type[BaseModel] | None = None

    def __init__(self):
        """无参数初始化，子类可重写"""
        # 验证子类是否正确实现了必要的属性
        if not self.name:
            raise NotImplementedError(f"{self.__class__.__name__} 必须定义 name 类属性")
        if not self.desc:
            raise NotImplementedError(f"{self.__class__.__name__} 必须定义 desc 类属性")
        # input_schema 可以为 None，表示工具无参数

    async def run(self, **kwargs) -> str:
        """执行工具，子类必须重写此方法"""
        raise NotImplementedError(f"{self.__class__.__name__} 必须实现 run 方法")

    def to_openai_format(self) -> dict[str, Any]:
        """转换为OpenAI工具格式"""
        if self.input_schema is not None:
            parameters = self.input_schema.model_json_schema()
        else:
            # 无参数工具，返回空对象
            parameters = {"type": "object", "properties": {}}
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.desc,
                "parameters": parameters,
            },
        }
