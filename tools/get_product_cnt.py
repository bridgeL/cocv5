"""获取商品数量工具"""

import time
import random
from mcp.types import Tool
from pydantic import BaseModel, Field


# 商品数量配置
PRODUCT_CNT_MAP = {
    "苹果": [1, 2, 3],
    "香蕉": [6, 7, 8]
}


class ProductParams(BaseModel):
    """商品参数"""
    product_name: str = Field(description='商品名称，如"苹果"、"香蕉"')


def get_product_cnt(params: ProductParams) -> int:
    """获取商品的数量

    Args:
        params: ProductParams 包含 product_name 字段

    Returns:
        对应商品的数量：苹果返回1/2/3，香蕉返回6/7/8
    """
    # 假设这是一个耗时任务
    time.sleep(5)

    product_name = params.product_name
    if product_name not in PRODUCT_CNT_MAP:
        raise ValueError(f"不支持的商品：{product_name}，支持的商品：{list(PRODUCT_CNT_MAP.keys())}")

    return random.choice(PRODUCT_CNT_MAP[product_name])


# MCP Tool实例
tool = Tool(
    name="get_product_cnt",
    description='获取商品的数量，苹果返回1/2/3，香蕉返回6/7/8',
    inputSchema=ProductParams.model_json_schema()
)
