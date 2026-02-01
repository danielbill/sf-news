"""华尔街见闻资讯流解析器

API: https://api-one.wallstcn.com/apiv1/content/information-flow
资讯流包含深度文章，软银投资 OpenAI 等重要新闻在这里
"""

from typing import List, Dict, Any
from httpx import Response, AsyncClient
from datetime import datetime

from ...models import Article, SourceType


async def parse(response: Response, source_config: Dict[str, Any], client: AsyncClient = None, limit: int = 20) -> List[Article]:
    """解析华尔街见闻资讯流响应

    Args:
        response: HTTP 响应对象
        source_config: 新闻源配置
        client: HTTP 客户端
        limit: 抓取的条数限制

    Returns:
        文章列表
    """
    if client is None:
        import httpx
        client = httpx.AsyncClient()

    articles = []

    try:
        url = source_config["url"]
        resp = await client.get(url, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        items = data.get("data", {}).get("items", [])

        for item in items:
            resource_type = item.get("resource_type")
            resource = item.get("resource", {})

            # 过滤广告和主题
            if resource_type in ("theme", "ad") or resource.get("type") == "live":
                continue

            title = resource.get("title") or resource.get("content_short")
            uri = resource.get("uri")
            display_time = resource.get("display_time")

            if not title or not uri:
                continue

            # 必须有发布时间才添加
            if not display_time:
                continue

            try:
                publish_time = datetime.fromtimestamp(int(display_time))
            except (ValueError, TypeError):
                continue  # 时间解析失败，跳过

            article = Article(
                title=title,
                url=uri,
                source=SourceType.WALLSTREETCN_NEWS,
                publish_time=publish_time
            )
            articles.append(article)

    except Exception as e:
        print(f"[WallstreetcnNews] Error: {e}")

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
