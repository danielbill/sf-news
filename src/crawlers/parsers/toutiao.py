"""今日头条解析器

API: https://www.toutiao.com/hot-event/hot-board/
"""

from typing import List, Dict, Any
from httpx import Response, AsyncClient
from datetime import datetime

from ...models import Article, SourceType


async def parse(response: Response, source_config: Dict[str, Any], client: AsyncClient = None, limit: int = 20) -> List[Article]:
    """解析今日头条热榜响应

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
        url = "https://www.toutiao.com/hot-event/hot-board/?origin=toutiao_pc"
        resp = await client.get(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        # 获取热榜数据
        hot_items = data.get("data", [])[:limit]

        for item in hot_items:
            cluster_id = item.get("ClusterIdStr")
            title = item.get("Title")
            label_uri = item.get("LabelUri", {}).get("url")

            if not cluster_id or not title:
                continue

            # 今日头条没有提供发布时间字段，跳过（不允许使用 datetime.now()）
            # 如果需要今日头条，需要去详情页抓取时间
            continue

            article = Article(
                title=title,
                url=f"https://www.toutiao.com/trending/{cluster_id}/",
                source=SourceType.TOUTIAO,
                publish_time=datetime.now()  # 占位，实际会被 continue 跳过
            )
            articles.append(article)

    except Exception as e:
        print(f"[Toutiao] Error: {e}")

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

        # 今日头条正文选择器
        content_div = soup.find("div", class_="article-content") or \
                      soup.find("div", class_="syl-article-base") or \
                      soup.find("article")

        if content_div:
            paragraphs = content_div.find_all("p")
            if paragraphs:
                return "\n\n".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))

        return "无法提取文章内容"
    except Exception as e:
        return f"获取内容失败: {e}"
