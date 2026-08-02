"""VentureBeat AI 解析器

URL: https://venturebeat.com/category/ai/
列表页结构：article 标签内的 a 标签含标题与相对链接，time[datetime] 含 ISO 时间。
"""

from typing import List, Dict, Any
from httpx import Response, AsyncClient
from datetime import datetime, timezone
from bs4 import BeautifulSoup

from ...models import Article, SourceType

BASE_URL = "https://venturebeat.com"
LIST_URL = "https://venturebeat.com/category/ai/"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

# 图片/视频 credit 前缀，正文过滤
_CREDIT_PREFIXES = ("image credit:", "credit:", "photo:")


async def parse(response: Response, source_config: Dict[str, Any], client: AsyncClient = None, limit: int = 20) -> List[Article]:
    """解析 VentureBeat AI 列表页

    Args:
        response: HTTP 响应对象（多数情况下被忽略，解析器自行抓取列表页）
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
        items = soup.find_all("article")

        for item in items:
            if len(articles) >= limit:
                break
            try:
                article = _parse_list_item(item)
                if article and article.url not in seen_urls:
                    seen_urls.add(article.url)
                    articles.append(article)
            except Exception as e:
                print(f"[venturebeat-ai] Error parsing item: {e}")
                continue

    except Exception as e:
        print(f"[venturebeat-ai] Error: {e}")

    return articles


def _parse_list_item(item) -> Article | None:
    """解析单个 article 元素为 Article 对象"""
    # 标题+链接：article 内的 a 标签，取第一个指向文章详情的链接
    link = None
    for a in item.find_all("a", href=True):
        href = a.get("href", "")
        if href and not href.startswith("#") and "/category/" not in href:
            link = a
            break

    if not link:
        return None

    title = link.get_text(strip=True)
    href = link.get("href", "")

    # 标题过短则跳过
    if not title or len(title) < 10:
        return None

    # 相对路径补全为完整 URL
    url = _absolute_url(href)
    if not url:
        return None

    # 时间：time[datetime]，ISO 格式（如 2026-07-31T21:19:09.820Z）
    time_el = item.find("time")
    publish_time = None
    if time_el:
        datetime_attr = time_el.get("datetime") or time_el.get_text(strip=True)
        publish_time = _parse_iso_time(datetime_attr)

    # 时间解析失败则跳过该文章（不使用 now 替代）
    if not publish_time:
        return None

    return Article(
        title=title,
        url=url,
        source=SourceType.VENTUREBEAT_AI,
        publish_time=publish_time,
    )


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
    """解析 ISO 8601 时间字符串

    支持形如 2026-07-31T21:19:09.820Z 或带偏移的格式。
    """
    if not time_str:
        return None
    s = time_str.strip()
    try:
        # datetime.fromisoformat 在 3.11+ 支持 Z 后缀，兼容处理
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        return datetime.fromisoformat(s)
    except (ValueError, TypeError):
        pass

    # 兜底：尝试常见格式
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(s[:len(fmt) + 3], fmt)
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

        # 详情页正文在 article 标签内
        article = soup.find("article")
        container = article or soup

        paragraphs = container.find_all("p")
        if not paragraphs:
            return "无法提取文章内容"

        texts = []
        for p in paragraphs:
            text = p.get_text(strip=True)
            if not text:
                continue
            # 过滤图片/视频 credit
            low = text.lower()
            if any(low.startswith(prefix) for prefix in _CREDIT_PREFIXES):
                continue
            texts.append(text)

        if not texts:
            return "无法提取文章内容"
        return "\n\n".join(texts)
    except Exception as e:
        return f"获取内容失败: {e}"
