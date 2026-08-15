"""Spaceflight Now 解析器（标准 RSS 2.0，WordPress）

SpaceX 发射报道最细（助推器编号/回收方式），NASA 及美国商业航天全覆盖。
API: https://spaceflightnow.com/feed/
"""

from typing import List, Dict, Any
from httpx import Response, AsyncClient

from ...models import Article, SourceType
from .rss_helper import fetch_rss_articles, fetch_wp_content


async def parse(response: Response, source_config: Dict[str, Any], client: AsyncClient = None, limit: int = 20) -> List[Article]:
    """解析 Spaceflight Now RSS"""
    if client is None:
        import httpx
        client = httpx.AsyncClient()

    try:
        return await fetch_rss_articles(
            source_config["url"], client, SourceType.SPACEFLIGHTNOW, limit
        )
    except Exception as e:
        print(f"[SpaceflightNow] Error: {e}")
        return []


async def fetch_content(url: str, client: AsyncClient) -> str:
    """获取文章正文内容"""
    return await fetch_wp_content(url, client)
