"""RSS 2.0 通用解析助手

SpaceNews / Spaceflight Now 等国际航天媒体都是标准 RSS 2.0
（WordPress 生成），字段结构一致，用 lxml 提取即可，无需额外依赖。
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime

from lxml import etree
from httpx import AsyncClient

from ...models import Article


# 北京时间（项目与去重层的 target_date 都以北京日历日为准）
_CN_TZ = timezone(timedelta(hours=8))


def _to_beijing(dt: datetime) -> datetime:
    """带时区的 RSS 时间（多为 UTC）转成北京时间的朴素时间戳。

    不转的话，美国源晚上发的文章在 UTC 日历上还是"昨天"，
    会被去重层的时间过滤（按北京 date.today()）整批丢弃。
    转换的是同一时刻，只是对齐项目统一的本地时间表示。
    """
    if dt.tzinfo is not None:
        dt = dt.astimezone(_CN_TZ).replace(tzinfo=None)
    return dt


def parse_rss_items(xml_bytes: bytes) -> List[Dict[str, Any]]:
    """解析 RSS 2.0，返回 [{title, link, pub_date}] 原始条目列表。

    只提取爬虫需要的三个字段；解析失败的条目直接跳过。
    """
    items = []
    try:
        # RSS 2.0 的 channel/item 均在默认命名空间外，无需 ns 映射
        root = etree.fromstring(xml_bytes)
    except etree.XMLSyntaxError as e:
        print(f"[RSS] XML 解析失败: {e}")
        return items

    for item in root.findall(".//item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        pub_raw = (item.findtext("pubDate") or "").strip()

        if not title or not link or not pub_raw:
            continue

        try:
            # RFC 822 格式：Fri, 14 Aug 2026 22:26:00 +0000
            pub_date = _to_beijing(parsedate_to_datetime(pub_raw))
        except (TypeError, ValueError):
            continue

        items.append({"title": title, "link": link, "pub_date": pub_date})

    return items


async def fetch_rss_articles(
    url: str, client: AsyncClient, source, limit: int = 20
) -> List[Article]:
    """抓取 RSS 并转为 Article 列表（pub_date 是源数据，绝不用当前时间替代）。

    RSS 源是按时间倒序输出的，直接截断前 limit 条即为最新。
    """
    resp = await client.get(url, timeout=30)
    resp.raise_for_status()

    raw_items = parse_rss_items(resp.content)
    articles = []
    for raw in raw_items[:limit]:
        articles.append(
            Article(
                title=raw["title"],
                url=raw["link"],
                source=source,
                publish_time=raw["pub_date"],
            )
        )

    print(f"[RSS] {url} 返回 {len(raw_items)} 条，取 {len(articles)} 条")
    return articles


async def fetch_wp_content(url: str, client: AsyncClient) -> str:
    """提取 WordPress 站点正文（RSS 源基本都是 WP 站）。

    通用策略：article 标签或常见内容 class 下的 <p> 拼接。
    """
    try:
        response = await client.get(url, timeout=20, follow_redirects=True)
        response.raise_for_status()

        from bs4 import BeautifulSoup

        soup = BeautifulSoup(response.text, "html.parser")

        container = (
            soup.find("article")
            or soup.find("div", class_="entry-content")
            or soup.find("div", class_="article-content")
            or soup.find("div", class_="post-content")
            or soup.find("div", class_="content")
        )
        if container is None:
            return "无法提取文章内容"

        paragraphs = container.find_all("p")
        text = "\n\n".join(
            p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)
        )
        return text or "无法提取文章内容"
    except Exception as e:
        return f"获取内容失败: {e}"
