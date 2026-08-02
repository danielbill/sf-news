"""MIT Technology Review AI 解析器

URL: https://www.technologyreview.com/topic/artificial-intelligence/
静态 HTML，文章标题位于 h2/h3 内的 a 标签，链接形如 /2026/07/xxx 或 /topic/xxx。
时间需从详情页或 meta 标签获取。
"""

from typing import List, Dict, Any
from httpx import Response, AsyncClient
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

from ...models import Article, SourceType

BASE_URL = "https://www.technologyreview.com"
LIST_URL = "https://www.technologyreview.com/topic/artificial-intelligence/"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

# 详情页时间补全的最大请求数
_MAX_DETAIL_FETCHES = 30


async def parse(response: Response, source_config: Dict[str, Any], client: AsyncClient = None, limit: int = 20) -> List[Article]:
    """解析 MIT Tech Review AI 列表页

    Args:
        response: HTTP 响应对象（被忽略，解析器自行抓取列表页）
        source_config: 新闻源配置
        client: HTTP 客户端
        limit: 抓取条数上限

    Returns:
        文章列表
    """
    if client is None:
        import httpx
        client = httpx.AsyncClient()

    articles: List[Article] = []
    seen_urls = set()

    try:
        resp = await client.get(LIST_URL, headers=HEADERS, timeout=30)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")

        # 标题在 h2/h3 内的 a 标签
        candidates = []
        for heading in soup.find_all(["h2", "h3"]):
            a = heading.find("a", href=True)
            if not a:
                continue
            title = a.get_text(strip=True)
            href = a.get("href", "")
            if not title or len(title) < 10:
                continue
            url = _absolute_url(href)
            if not url or url in seen_urls:
                continue
            # 仅保留指向文章详情的链接（排除 topic/、author/、# 锚点等）
            if not _is_article_url(url):
                continue
            seen_urls.add(url)
            candidates.append((title, url))
            if len(candidates) >= min(limit * 3, _MAX_DETAIL_FETCHES):
                break

        # 时间需从详情页或 meta 获取
        for title, url in candidates:
            if len(articles) >= limit:
                break
            try:
                publish_time = await _fetch_publish_time(url, client)
                if not publish_time:
                    continue  # 时间缺失/解析失败则跳过
                articles.append(Article(
                    title=title,
                    url=url,
                    source=SourceType.MIT_TECH_REVIEW_AI,
                    publish_time=publish_time,
                ))
            except Exception as e:
                print(f"[mit-tech-review-ai] Error fetching detail {url}: {e}")
                continue

    except Exception as e:
        print(f"[mit-tech-review-ai] Error: {e}")

    return articles


def _is_article_url(url: str) -> bool:
    """判断是否为文章详情 URL（排除 topic、author 等聚合页）"""
    from urllib.parse import urlparse
    path = urlparse(url).path.lower()
    if path.rstrip("/") == "":
        return False
    # 排除聚合/导航类页面
    for seg in ("/topic/", "/author/", "/series/", "/newsletter/", "/tag/"):
        if path.startswith(seg):
            return False
    # 形如 /2026/07/xxx 的文章链接
    import re
    if re.match(r"/\d{4}/\d{2}/", path):
        return True
    # 兜底：只要不是明显聚合页且路径长度合理
    return len(path) > 1


async def _fetch_publish_time(url: str, client: AsyncClient) -> datetime | None:
    """从详情页或 meta 提取发布时间"""
    try:
        resp = await client.get(url, headers=HEADERS, timeout=15)
        if resp.status_code >= 400:
            return None
        soup = BeautifulSoup(resp.text, "html.parser")

        # 1) meta 标签
        for prop in ("article:published_time", "og:published_time", "datePublished"):
            meta = soup.find("meta", property=prop) or soup.find("meta", attrs={"name": prop})
            if meta and meta.get("content"):
                t = _parse_iso_time(meta["content"])
                if t:
                    return t

        # 2) time[datetime]
        time_el = soup.find("time", attrs={"datetime": True})
        if time_el:
            t = _parse_iso_time(time_el["datetime"])
            if t:
                return t
        time_el = soup.find("time")
        if time_el:
            raw = time_el.get_text(strip=True)
            t = _parse_iso_time(raw) or _parse_readable_date(raw)
            if t:
                return t

        # 3) 常见 class
        for cls in ("date", "published-date", "entry-date", "post-date"):
            el = soup.find(class_=cls)
            if el:
                raw = el.get_text(strip=True)
                t = _parse_iso_time(raw) or _parse_readable_date(raw)
                if t:
                    return t

        # 4) JSON-LD
        import json
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string or "{}")
                if isinstance(data, list):
                    data = data[0] if data else {}
                date_str = data.get("datePublished") if isinstance(data, dict) else None
                if date_str:
                    t = _parse_iso_time(date_str)
                    if t:
                        return t
            except (json.JSONDecodeError, TypeError, IndexError):
                continue

        # 5) 正则兜底
        import re
        m = re.search(r"20\d{2}-\d{2}-\d{2}[ T]\d{2}:\d{2}", resp.text)
        if m:
            t = _parse_iso_time(m.group(0))
            if t:
                return t
    except Exception as e:
        print(f"[mit-tech-review-ai] Error parsing time from {url}: {e}")

    return None


def _absolute_url(href: str) -> str:
    """将相对路径补全为完整 URL"""
    if not href:
        return ""
    if href.startswith("http://") or href.startswith("https://"):
        return href
    if href.startswith("//"):
        return "https:" + href
    if href.startswith("/"):
        return BASE_URL + href
    return BASE_URL + "/" + href


def _parse_iso_time(time_str: str) -> datetime | None:
    """解析 ISO 8601 时间字符串"""
    if not time_str:
        return None
    s = time_str.strip()
    try:
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        return datetime.fromisoformat(s)
    except (ValueError, TypeError):
        return None


def _parse_readable_date(time_str: str) -> datetime | None:
    """解析人类可读日期（如 'July 31, 2026'、'Jul 31, 2026'）

    时间解析失败返回 None。
    """
    if not time_str:
        return None
    s = time_str.strip()
    for fmt in (
        "%B %d, %Y", "%b %d, %Y",
        "%B %d, %Y %H:%M", "%b %d, %Y %H:%M",
        "%Y-%m-%d", "%Y-%m-%d %H:%M:%S",
        "%d %B %Y", "%d %b %Y",
    ):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


async def fetch_content(url: str, client: AsyncClient) -> str:
    """获取文章正文内容

    Args:
        url: 文章 URL
        client: HTTP 客户端

    Returns:
        正文内容（段落以空行连接）
    """
    try:
        response = await client.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # 优先 article 区域，其次常见正文 class
        container = soup.find("article") or \
                    soup.find("div", class_="article__body") or \
                    soup.find("div", class_="article-body") or \
                    soup.find("div", class_="entry-content") or \
                    soup.find("main")

        if container:
            paragraphs = container.find_all("p")
            if paragraphs:
                texts = [p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)]
                if texts:
                    return "\n\n".join(texts)

        return "无法提取文章内容"
    except Exception as e:
        return f"获取内容失败: {e}"
