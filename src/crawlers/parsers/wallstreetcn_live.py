"""华尔街见闻快讯解析器

API: https://api-one.wallstcn.com/apiv1/content/lives
"""

from typing import List, Dict, Any
from httpx import Response, AsyncClient
from datetime import datetime

from ...models import Article, SourceType


async def parse(response: Response, source_config: Dict[str, Any], client: AsyncClient = None) -> List[Article]:
    """解析华尔街见闻快讯响应

    Args:
        response: HTTP 响应对象
        source_config: 新闻源配置
        client: HTTP 客户端

    Returns:
        文章列表
    """
    if client is None:
        import httpx
        client = httpx.AsyncClient()

    articles = []

    try:
        url = "https://api-one.wallstcn.com/apiv1/content/lives?channel=global-channel&limit=30"
        resp = await client.get(url, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        # items 是一个 list
        items = data.get("data", {}).get("items", [])

        print(f"[WallstreetcnLive] 返回 {len(items)} 条")
        for i, item in enumerate(items[:5]):
            title = item.get("title") or item.get("content_text") or item.get("content_short")
            uri = item.get("uri")
            display_time = item.get("display_time")
            print(f"  [{i}] title={title[:40]}..., uri={uri}, time={display_time}")

        for item in items:
            title = item.get("title") or item.get("content_text") or item.get("content_short")
            uri = item.get("uri")
            display_time = item.get("display_time")

            if not title or not uri:
                continue

            timestamp = datetime.now()
            if display_time:
                try:
                    timestamp = datetime.fromtimestamp(int(display_time))
                except (ValueError, TypeError):
                    pass

            article = Article(
                title=title,
                url=uri,
                source=SourceType.WALLSTREETCN_LIVE,
                timestamp=timestamp
            )
            articles.append(article)

    except Exception as e:
        print(f"[WallstreetcnLive] Error: {e}")

    return articles


async def fetch_content(url: str, client: AsyncClient) -> str:
    """获取文章正文内容"""
    try:
        response = await client.get(url, timeout=15)
        response.raise_for_status()

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.text, "html.parser")

        content_div = soup.find("div", class_="article-content") or \
                      soup.find("div", class_="content") or \
                      soup.find("article")

        if content_div:
            paragraphs = content_div.find_all("p")
            if paragraphs:
                return "\n\n".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))

        return "无法提取文章内容"
    except Exception as e:
        return f"获取内容失败: {e}"
