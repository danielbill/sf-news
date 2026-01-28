"""财联社电报解析器

API: https://www.cls.cn/nodeapi/updateTelegraphList
"""

from typing import List, Dict, Any
from httpx import Response, AsyncClient
from datetime import datetime

from ...models import Article, SourceType


async def parse(response: Response, source_config: Dict[str, Any], client: AsyncClient = None) -> List[Article]:
    """解析财联社电报响应

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
        url = "https://www.cls.cn/nodeapi/updateTelegraphList"
        resp = await client.get(url, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        telegraph_list = data.get("data", {}).get("roll_data", [])

        for item in telegraph_list:
            # 过滤广告
            if item.get("is_ad"):
                continue

            item_id = item.get("id")
            title = item.get("title") or item.get("brief")
            share_url = item.get("shareurl")
            ctime = item.get("ctime")

            if not item_id or not title:
                continue

            timestamp = datetime.now()
            if ctime:
                try:
                    timestamp = datetime.fromtimestamp(int(ctime))
                except (ValueError, TypeError):
                    pass

            url = share_url or f"https://www.cls.cn/detail/{item_id}"

            article = Article(
                title=title,
                url=url,
                source=SourceType.CLS_TELEGRAPH,
                timestamp=timestamp
            )
            articles.append(article)

    except Exception as e:
        print(f"[CLSTelegraph] Error: {e}")

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
                      soup.find("div", class_="telegraph-content")

        if content_div:
            paragraphs = content_div.find_all("p")
            if paragraphs:
                return "\n\n".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))

        return "无法提取文章内容"
    except Exception as e:
        return f"获取内容失败: {e}"
