"""获取商品价格工具"""

import time
import random
from mcp.types import Tool
from pydantic import BaseModel, Field


# 商品价格配置
PRODUCT_PRICE_MAP = {
    "苹果": [10, 20, 40],
    "香蕉": [1, 2, 3]
}


class ProductParams(BaseModel):
    """商品参数"""
    product_name: str = Field(description='商品名称，如"苹果"、"香蕉"')


def get_product_price(params: ProductParams) -> int:
    """获取商品的单价

    Args:
        params: ProductParams 包含 product_name 字段

    Returns:
        对应商品的价格：苹果返回10/20/40元，香蕉返回1/2/3元
    """
    # 假设这是一个耗时任务
    time.sleep(5)

    product_name = params.product_name
    if product_name not in PRODUCT_PRICE_MAP:
        raise ValueError(f"不支持的商品：{product_name}，支持的商品：{list(PRODUCT_PRICE_MAP.keys())}")

    return random.choice(PRODUCT_PRICE_MAP[product_name])


# MCP Tool实例
tool = Tool(
    name="get_product_price",
    description='获取商品的单价，苹果返回10/20/40元，香蕉返回1/2/3元',
    inputSchema=ProductParams.model_json_schema()
)
