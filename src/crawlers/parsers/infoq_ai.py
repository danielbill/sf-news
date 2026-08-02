"""InfoQ 中文站解析器

URL: https://www.infoq.cn/
列表页文章链接：a[href*="/article/"]；无时间元素，需从详情页获取。
需过滤推广链接（aicon.infoq.cn、qcon.infoq.cn 等会议链接）。
"""

from typing import List, Dict, Any
from httpx import Response, AsyncClient
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

from ...models import Article, SourceType

BASE_URL = "https://www.infoq.cn"
LIST_URL = "https://www.infoq.cn/"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

# 推广/会议域名前缀，需过滤
_PROMO_HOST_PREFIXES = (
    "aicon.infoq.cn",
    "qcon.infoq.cn",
    "geek.infoq.cn",
    "live.infoq.cn",
    "summit.infoq.cn",
    "form.infoq.cn",
)

# 详情页时间补全的最大请求数
_MAX_DETAIL_FETCHES = 30


async def parse(response: Response, source_config: Dict[str, Any], client: AsyncClient = None, limit: int = 20) -> List[Article]:
    """解析 InfoQ 列表页

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

        # 收集 a[href*="/article/"] 的文章链接
        candidates = []
        for a in soup.find_all("a", href=True):
            href = a.get("href", "")
            if "/article/" not in href:
                continue
            # 过滤推广链接
            if _is_promo(href):
                continue
            title = a.get_text(strip=True)
            if not title or len(title) < 10:
                continue
            url = _absolute_url(href)
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)
            candidates.append((title, url))
            if len(candidates) >= min(limit * 3, _MAX_DETAIL_FETCHES):
                break

        # 列表页无时间，需从详情页补全 publish_time
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
                    source=SourceType.INFOQ_AI,
                    publish_time=publish_time,
                ))
            except Exception as e:
                print(f"[infoq-ai] Error fetching detail {url}: {e}")
                continue

    except Exception as e:
        print(f"[infoq-ai] Error: {e}")

    return articles


def _is_promo(href: str) -> bool:
    """判断是否为推广/会议链接"""
    if not href:
        return False
    low = href.lower()
    for prefix in _PROMO_HOST_PREFIXES:
        if prefix in low:
            return True
    # 形如 https://www.infoq.cn/article/... 的是正文，其他子域一律当推广过滤
    return False


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
            t = _parse_iso_time(raw) or _parse_relative_time(raw)
            if t:
                return t

        # 3) 常见 class
        for cls in ("article-time", "publish-time", "date", "time"):
            el = soup.find(class_=cls)
            if el:
                raw = el.get_text(strip=True)
                t = _parse_iso_time(raw) or _parse_relative_time(raw)
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

        # 5) 正则兜底匹配 ISO 时间
        import re
        m = re.search(r"20\d{2}-\d{2}-\d{2}[ T]\d{2}:\d{2}", resp.text)
        if m:
            t = _parse_iso_time(m.group(0))
            if t:
                return t
    except Exception as e:
        print(f"[infoq-ai] Error parsing time from {url}: {e}")

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


def _parse_relative_time(time_str: str) -> datetime | None:
    """解析相对时间字符串（如 '3小时前'、'30分钟前'、'2天前'）

    与 36kr.py 的同名函数保持一致的语义。
    """
    if not time_str:
        return None
    now = datetime.now()
    s = time_str.strip().lower()
    try:
        if "分钟前" in s:
            return now - timedelta(minutes=int(s.replace("分钟前", "").strip()))
        if "小时前" in s:
            return now - timedelta(hours=int(s.replace("小时前", "").strip()))
        if "天前" in s:
            return now - timedelta(days=int(s.replace("天前", "").strip()))
        if "刚刚" in s or "just now" in s:
            return now
    except (ValueError, AttributeError):
        return None
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

        # InfoQ 详情页正文容器
        content_div = soup.find("div", class_="article-content") or \
                      soup.find("div", class_="article-typo") or \
                      soup.find("div", class_="article-preview-wrap") or \
                      soup.find("article")

        if content_div:
            paragraphs = content_div.find_all("p")
            if paragraphs:
                texts = [p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)]
                if texts:
                    return "\n\n".join(texts)

        return "无法提取文章内容"
    except Exception as e:
        return f"获取内容失败: {e}"
