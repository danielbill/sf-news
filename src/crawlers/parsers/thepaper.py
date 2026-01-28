"""澎湃新闻解析器

API: https://cache.thepaper.cn/contentapi/wwwIndex/rightSidebar
"""

from typing import List, Dict, Any
from httpx import Response, AsyncClient
from datetime import datetime

from ...models import Article, SourceType


async def parse(response: Response, source_config: Dict[str, Any], client: AsyncClient = None) -> List[Article]:
    """解析澎湃新闻响应

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
        url = "https://cache.thepaper.cn/contentapi/wwwIndex/rightSidebar"
        resp = await client.get(url, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        # 获取热门新闻列表
        hot_news = data.get("data", {}).get("hotNews", [])

        for item in hot_news:
            cont_id = item.get("contId")
            title = item.get("name")
            pub_time_long = item.get("pubTimeLong")

            if not cont_id or not title:
                continue

            # 解析时间戳（毫秒）
            timestamp = datetime.now()
            if pub_time_long:
                try:
                    timestamp = datetime.fromtimestamp(int(pub_time_long) / 1000)
                except (ValueError, TypeError):
                    pass

            article = Article(
                title=title,
                url=f"https://www.thepaper.cn/newsDetail_forward_{cont_id}",
                source=SourceType.THEPAPER,
                timestamp=timestamp
            )
            articles.append(article)

    except Exception as e:
        print(f"[Thapaper] Error: {e}")

    return articles


async def fetch_content(url: str, client: AsyncClient) -> str:
    """获取文章正文内容

    Args:
        url: 文章 URL
        client: HTTP 客户端

    Returns:
        正文内容
    """
    try:
        response = await client.get(url, timeout=15)
        response.raise_for_status()

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.text, "html.parser")

        # 澎湃新闻正文选择器
        content_div = soup.find("div", class_="index_article__content") or \
                      soup.find("div", class_="news_txt") or \
                      soup.find("article")

        if content_div:
            paragraphs = content_div.find_all("p")
            if paragraphs:
                return "\n\n".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))

        return "无法提取文章内容"
    except Exception as e:
        return f"获取内容失败: {e}"
