"""参考消息爬虫"""

from typing import List
from datetime import datetime
import httpx
from bs4 import BeautifulSoup

from .base import BaseCrawler
from ..models import Article, SourceType


class CankaoxiaoxiCrawler(BaseCrawler):
    """参考消息爬虫

    API: https://china.cankaoxiaoxi.com/json/channel/{channel}/list.json
    """

    channels = ["zhongguo", "guandian", "gj"]
    base_url = "https://china.cankaoxiaoxi.com/json/channel/{}/list.json"

    async def fetch(self) -> List[Article]:
        """抓取参考消息文章"""
        articles = []

        for channel in self.channels:
            try:
                response = await self.client.get(self.base_url.format(channel))
                response.raise_for_status()
                data = response.json()

                for item in data.get("list", []):
                    article_data = item["data"]
                    article = Article(
                        title=article_data["title"],
                        url=article_data["url"],
                        source=SourceType.CANKAOXIAOXI,
                        timestamp=self._parse_timestamp(article_data.get("publishTime"))
                    )
                    articles.append(article)

            except Exception as e:
                print(f"Error fetching {channel}: {e}")
                continue

        # 过滤关键词
        filtered = self.filter_keywords(articles)

        # 获取文章正文内容
        for article in filtered:
            try:
                content = await self._fetch_content(article.url)
                article.content = content
            except Exception as e:
                print(f"Error fetching content for {article.url}: {e}")
                article.content = None

        return filtered

    async def _fetch_content(self, url: str) -> str:
        """获取文章正文内容"""
        try:
            response = await self.client.get(url, timeout=15)
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

    def _parse_timestamp(self, timestamp_str: str) -> datetime:
        """解析时间戳"""
        if not timestamp_str:
            return datetime.now()
        # 参考消息时间格式: "2025-01-28 10:00:00"
        try:
            return datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return datetime.now()
