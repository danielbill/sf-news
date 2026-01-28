"""参考消息解析器

API: https://china.cankaoxiaoxi.com/json/channel/{channel}/list.json
"""

from typing import List, Dict, Any
from httpx import Response, AsyncClient
from bs4 import BeautifulSoup
from datetime import datetime

from ...models import Article, SourceType


# 参考消息频道
CHANNELS = ["zhongguo", "guandian", "gj"]
BASE_URL = "https://china.cankaoxiaoxi.com/json/channel/{}/list.json"


async def parse(response: Response, source_config: Dict[str, Any], client: AsyncClient = None) -> List[Article]:
    """解析参考消息响应

    Args:
        response: HTTP 响应对象（注意：参考消息需要多频道抓取，此参数保留接口兼容）
        source_config: 新闻源配置
        client: HTTP 客户端（用于抓取多频道和正文）

    Returns:
        文章列表
    """
    if client is None:
        # 如果没有提供 client，创建一个临时的（不推荐）
        import httpx
        client = httpx.AsyncClient()

    articles = []

    # 抓取所有频道
    for channel in CHANNELS:
        try:
            url = BASE_URL.format(channel)
            channel_response = await client.get(url)
            channel_response.raise_for_status()
            data = channel_response.json()

            for item in data.get("list", []):
                article_data = item["data"]
                article = Article(
                    title=article_data["title"],
                    url=article_data["url"],
                    source=SourceType.CANKAOXIAOXI,
                    timestamp=_parse_timestamp(article_data.get("publishTime"))
                )
                articles.append(article)

        except Exception as e:
            print(f"Error fetching {channel}: {e}")
            continue

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
        soup = BeautifulSoup(response.text, "html.parser")

        # 参考消息的文章正文通常在 .article-content 或类似容器中
        content_div = soup.find("div", class_="article-content") or soup.find("div", class_="content")
        if content_div:
            # 提取段落文本
            paragraphs = content_div.find_all("p")
            if paragraphs:
                return "\n\n".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))

        # 如果找不到特定容器，尝试获取主要内容区域
        body = soup.find("body")
        if body:
            paragraphs = body.find_all("p")
            if paragraphs:
                return "\n\n".join(p.get_text(strip=True) for p in paragraphs[:20] if p.get_text(strip=True))

        return "无法提取文章内容"
    except Exception as e:
        return f"获取内容失败: {e}"


def _parse_timestamp(timestamp_str: str) -> datetime:
    """解析时间戳"""
    if not timestamp_str:
        return datetime.now()
    # 参考消息时间格式: "2025-01-28 10:00:00"
    try:
        return datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return datetime.now()
