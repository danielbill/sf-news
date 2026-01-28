"""解析器模块

每个解析器文件对应一个新闻源，文件名 = news_sources.yaml 中的 source.id

解析器标准接口：
    async def parse(response: httpx.Response, source_config: dict) -> List[Article]

示例：
    # parsers/cankaoxiaoxi.py
    async def parse(response, source_config):
        # 解析逻辑
        return [Article(...)]
"""

from .base import get_features, parse_html, parse_json

__all__ = [
    "get_features",
    "parse_html",
    "parse_json",
]
