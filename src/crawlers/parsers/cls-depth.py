"""财联社深度文章解析器

API: https://www.cls.cn/v3/depth/home/assembled/1000
深度文章板块，包含更详细的财经分析
"""

from typing import List, Dict, Any
from httpx import Response, AsyncClient
from datetime import datetime

from ...models import Article, SourceType


async def parse(response: Response, source_config: Dict[str, Any], client: AsyncClient = None, limit: int = 20) -> List[Article]:
    """解析财联社深度文章响应

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
        url = "https://www.cls.cn/v3/depth/home/assembled/1000"
        resp = await client.get(url, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        depth_list = data.get("data", {}).get("depth_list", [])[:limit]

        for item in depth_list:
            item_id = item.get("id")
            title = item.get("title") or item.get("brief")
            share_url = item.get("shareurl")
            ctime = item.get("ctime")

            if not item_id or not title:
                continue

            # 必须有发布时间才添加
            if not ctime:
                continue

            try:
                publish_time = datetime.fromtimestamp(int(ctime))
            except (ValueError, TypeError):
                continue  # 时间解析失败，跳过

            url = share_url or f"https://www.cls.cn/detail/{item_id}"

            article = Article(
                title=title,
                url=url,
                source=SourceType.CLS_DEPTH,
                publish_time=publish_time
            )
            articles.append(article)

    except Exception as e:
        print(f"[CLSDepth] Error: {e}")

    return articles


async def fetch_content(url: str, client: AsyncClient) -> str:
    """获取文章正文内容"""
    try:
        response = await client.get(url, timeout=15)
        response.raise_for_status()

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.text, "html.parser")

        content_div = soup.find("div", class_="content") or \
                      soup.find("div", class_="article-content") or \
                      soup.find("article")

        if content_div:
            paragraphs = content_div.find_all("p")
            if paragraphs:
                return "\n\n".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))

        return "无法提取文章内容"
    except Exception as e:
        return f"获取内容失败: {e}"
