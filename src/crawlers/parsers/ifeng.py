"""凤凰网解析器

从首页 HTML 中提取 hotNews 数据
"""

from typing import List, Dict, Any
from httpx import Response, AsyncClient
from datetime import datetime
import re
import json

from ...models import Article, SourceType


async def parse(response: Response, source_config: Dict[str, Any], client: AsyncClient = None, limit: int = 20) -> List[Article]:
    """解析凤凰网响应

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
        url = "https://www.ifeng.com/"
        resp = await client.get(url, timeout=30)
        resp.raise_for_status()
        html = resp.text

        # 从 HTML 中提取 allData 变量
        regex = r"var\s+allData\s*=\s*(\{[\s\S]*?\});"
        match = re.search(regex, html)

        if match:
            try:
                all_data = json.loads(match.group(1))
                hot_news = all_data.get("hotNews1", [])[:limit]

                for item in hot_news:
                    title = item.get("title")
                    url = item.get("url")
                    news_time = item.get("newsTime")

                    if not title or not url:
                        continue

                    # 必须有发布时间才添加
                    if not news_time:
                        continue

                    # 解析时间
                    publish_time = _parse_time(news_time)
                    if not publish_time:
                        continue  # 时间解析失败，跳过

                    article = Article(
                        title=title,
                        url=url,
                        source=SourceType.IFENG,
                        publish_time=publish_time
                    )
                    articles.append(article)

            except json.JSONDecodeError as e:
                print(f"[Ifeng] JSON decode error: {e}")

    except Exception as e:
        print(f"[Ifeng] Error: {e}")

    return articles


def _parse_time(time_str: str) -> datetime | None:
    """解析时间字符串

    Args:
        time_str: 时间字符串

    Returns:
        datetime 对象，解析失败返回 None
    """
    # 尝试多种格式
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y%m%d%H%M%S",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(time_str, fmt)
        except ValueError:
            continue

    return None


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

        # 凤凰网正文选择器
        content_div = soup.find("div", class_="main_content") or \
                      soup.find("div", class_="article-content") or \
                      soup.find("article")

        if content_div:
            paragraphs = content_div.find_all("p")
            if paragraphs:
                return "\n\n".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))

        return "无法提取文章内容"
    except Exception as e:
        return f"获取内容失败: {e}"
