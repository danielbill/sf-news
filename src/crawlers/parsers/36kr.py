"""36氪解析器

API: https://www.36kr.com/newsflashes
"""

from typing import List, Dict, Any
from httpx import Response, AsyncClient
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

from ...models import Article, SourceType


async def parse(response: Response, source_config: Dict[str, Any], client: AsyncClient = None, limit: int = 20) -> List[Article]:
    """解析36氪快讯响应

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
        url = "https://www.36kr.com/newsflashes"
        resp = await client.get(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }, timeout=30)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")
        items = soup.select(".newsflash-item")[:limit]

        for item in items:
            try:
                # 获取标题和链接
                title_el = item.select_one("a.item-title")
                if not title_el:
                    continue

                title = title_el.get_text(strip=True)
                url_path = title_el.get("href")

                if not title or not url_path:
                    continue

                # 获取相对时间
                time_el = item.select_one(".time")
                relative_time = time_el.get_text(strip=True) if time_el else ""

                # 解析相对时间（如 "3小时前"）
                publish_time = _parse_relative_time(relative_time)

                # 必须有有效的发布时间才添加
                if not publish_time:
                    continue

                article = Article(
                    title=title,
                    url=f"https://www.36kr.com{url_path}",
                    source=SourceType.KR36,
                    publish_time=publish_time
                )
                articles.append(article)

            except Exception as e:
                print(f"[36kr] Error parsing item: {e}")
                continue

    except Exception as e:
        print(f"[36kr] Error: {e}")

    return articles


def _parse_relative_time(time_str: str) -> datetime | None:
    """解析相对时间字符串

    Args:
        time_str: 相对时间字符串（如 "3小时前"、"30分钟前"）

    Returns:
        datetime 对象，解析失败返回 None
    """
    if not time_str:
        return None

    now = datetime.now()
    time_str = time_str.strip().lower()

    try:
        if "分钟前" in time_str:
            minutes = int(time_str.replace("分钟前", "").strip())
            return now - timedelta(minutes=minutes)
        elif "小时前" in time_str:
            hours = int(time_str.replace("小时前", "").strip())
            return now - timedelta(hours=hours)
        elif "天前" in time_str:
            days = int(time_str.replace("天前", "").strip())
            return now - timedelta(days=days)
    except (ValueError, AttributeError):
        pass

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

        soup = BeautifulSoup(response.text, "html.parser")

        # 36氪快讯正文选择器
        content_div = soup.find("div", class_="newsflash-detail-content") or \
                      soup.find("div", class_="article-content")

        if content_div:
            paragraphs = content_div.find_all("p")
            if paragraphs:
                return "\n\n".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))

        return "无法提取文章内容"
    except Exception as e:
        return f"获取内容失败: {e}"
