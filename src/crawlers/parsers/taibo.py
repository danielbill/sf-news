"""泰伯网解析器（服务端渲染 HTML）

中国空天产业第一垂直媒体：商业航天（蓝箭/星网/千帆星座）、低空经济、
卫星互联网融资与发射动态，7x24 快讯分钟级更新。
站点无 RSS、无公开 JSON API，直接解析首页 HTML。

首页结构（实测 2026-08）：
- 7x24 快讯：<div class="newsflash"> 下每个 <li> 含
    <time class="timeago" datetime="2026-08-14 18:29:23"> 和
    <p class="title-text"><a href="/newsflashes/31747432">
- 热门文章：各榜单 <a href="/p/99607">（首页不带时间，需抓详情页取）

详情页（/p/ 和 /newsflashes/ 同构）：
- 时间 <div class="article-author-date"><span>2026-08-14 18:29</span>
- 正文 <div class="article-content">
"""

import re
from datetime import datetime
from typing import List, Dict, Any

from bs4 import BeautifulSoup
from httpx import Response, AsyncClient

from ...models import Article, SourceType

# 详情页时间格式：2026-08-14 18:29
_DT = re.compile(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}")
# /p/ 文章详情页抓取上限（每篇多一次请求，控制总量）
_MAX_DETAIL_FETCH = 10


async def parse(response: Response, source_config: Dict[str, Any], client: AsyncClient = None, limit: int = 20) -> List[Article]:
    """解析泰伯网首页"""
    if client is None:
        import httpx
        client = httpx.AsyncClient()

    articles: List[Article] = []
    seen_urls = set()

    try:
        url = source_config["url"]
        resp = await client.get(url, timeout=30)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")

        # 1) 7x24 快讯：首页自带发布时间，一次请求全拿到
        for li in soup.select("div.newsflash li"):
            time_el = li.select_one("time.timeago")
            link_el = li.select_one("p.title-text a")
            if time_el is None or link_el is None:
                continue

            href = link_el.get("href") or ""
            title = link_el.get_text(strip=True)
            dt_raw = time_el.get("datetime") or time_el.get_text(strip=True)
            if not href or not title:
                continue

            full_url = href if href.startswith("http") else f"https://www.taibo.cn{href}"
            if full_url in seen_urls:
                continue

            try:
                publish_time = datetime.strptime(dt_raw, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                continue

            seen_urls.add(full_url)
            articles.append(
                Article(
                    title=title,
                    url=full_url,
                    source=SourceType.TAIBO,
                    publish_time=publish_time,
                )
            )

        # 2) 热门文章 /p/xxx：首页无时间，逐篇抓详情页（限量）
        p_links = []
        for a in soup.find_all("a", href=re.compile(r"^/p/\d+$")):
            full_url = f"https://www.taibo.cn{a['href']}"
            if full_url not in seen_urls and full_url not in [p[0] for p in p_links]:
                title = a.get_text(strip=True)
                if title:  # 榜单里图片位等空链接跳过
                    p_links.append((full_url, title))

        detail_count = 0
        for full_url, title in p_links:
            if detail_count >= _MAX_DETAIL_FETCH or len(articles) >= limit:
                break

            try:
                detail = await client.get(full_url, timeout=20, follow_redirects=True)
                detail.raise_for_status()
            except Exception as e:
                print(f"[Taibo] 详情页获取失败 {full_url}: {e}")
                continue

            dsoup = BeautifulSoup(detail.text, "lxml")
            # 详情页标题更完整，优先用 h1
            h1 = dsoup.find("h1")
            if h1 and h1.get_text(strip=True):
                title = h1.get_text(strip=True)

            dt_raw = _extract_detail_time(dsoup)
            if not dt_raw:
                continue  # 拿不到源时间就跳过，不允许用当前时间顶替

            seen_urls.add(full_url)
            detail_count += 1
            articles.append(
                Article(
                    title=title,
                    url=full_url,
                    source=SourceType.TAIBO,
                    publish_time=dt_raw,
                )
            )

        # 按时间倒序，截断 limit
        articles.sort(key=lambda a: a.publish_time, reverse=True)
        articles = articles[:limit]
        print(f"[Taibo] 返回 {len(articles)} 条（快讯 + 热文）")

    except Exception as e:
        print(f"[Taibo] Error: {e}")

    return articles


def _extract_detail_time(soup: BeautifulSoup) -> datetime | None:
    """从详情页提取发布时间：.article-author-date span → '2026-08-14 18:29'"""
    el = soup.select_one(".article-author-date span") or soup.select_one(
        ".article-author-date"
    )
    if el is None:
        return None
    m = _DT.search(el.get_text())
    if not m:
        return None
    try:
        return datetime.strptime(m.group(0), "%Y-%m-%d %H:%M")
    except ValueError:
        return None


async def fetch_content(url: str, client: AsyncClient) -> str:
    """获取文章正文内容（/p/ 文章与 /newsflashes/ 快讯详情页同构）"""
    try:
        response = await client.get(url, timeout=20, follow_redirects=True)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "lxml")
        content_div = soup.find("div", class_="article-content") or soup.find(
            "div", class_="content"
        )

        if content_div:
            paragraphs = content_div.find_all("p")
            text = "\n\n".join(
                p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)
            )
            # 快讯详情可能无 <p> 包裹，直接取容器文本
            if not text:
                text = content_div.get_text("\n", strip=True)
            return text or "无法提取文章内容"

        return "无法提取文章内容"
    except Exception as e:
        return f"获取内容失败: {e}"
