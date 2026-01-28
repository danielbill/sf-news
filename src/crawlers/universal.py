"""通用爬虫 - 根据配置自动加载解析器

每个新闻源对应一个解析器模块：
    src/crawlers/parsers/{source_id}.py

解析器标准接口：
    async def parse(response: httpx.Response, source_config: dict, client: httpx.AsyncClient) -> List[Article]
"""

import importlib
from typing import List, Dict, Any
import httpx
from pathlib import Path

from ..models import Article, SourceType
from ..config import ConfigReader


# 源 ID 到解析器模块的映射（处理特殊命名）
PARSER_MODULE_MAP = {
    "36kr": "_36kr",
    "wallstreetcn-live": "wallstreetcn_live",
    "wallstreetcn-news": "wallstreetcn_news",
    "cls-telegraph": "cls_telegraph",
    "cls-depth": "cls_depth",
}


class UniversalCrawler:
    """通用爬虫 - 根据配置自动加载解析器"""

    def __init__(self, source_config: Any, config_dir: str = "config"):
        """初始化通用爬虫

        Args:
            source_config: 新闻源配置对象
            config_dir: 配置文件目录
        """
        self.source = source_config
        self.config_dir = config_dir
        self.client = httpx.AsyncClient(
            timeout=30,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        )

        # 加载关键词配置
        self._keywords = self._load_keywords()

    def _load_keywords(self) -> List[str]:
        """从配置文件加载关键词"""
        try:
            reader = ConfigReader(self.config_dir)
            config = reader.load_news_keywords_config()

            # 展平所有关键词
            all_keywords = set()

            # 人物关键词
            for person_keywords in config.get("people", {}).values():
                all_keywords.update(person_keywords)

            # 公司关键词
            for company_keywords in config.get("companies", {}).values():
                all_keywords.update(company_keywords)

            # 话题关键词
            for topic_group in config.get("topics", []):
                all_keywords.update(topic_group)

            return list(all_keywords)
        except Exception as e:
            print(f"Warning: Failed to load keywords config: {e}")
            return []

    @property
    def keywords(self) -> List[str]:
        """获取所有关键词（用于过滤）"""
        return self._keywords

    async def fetch(self) -> List[Article]:
        """抓取并解析文章

        Returns:
            文章列表（已过滤关键词）
        """
        # 1. 动态加载解析器
        parser = self._load_parser()

        # 2. 调用解析器获取文章
        articles = await parser.parse(
            response=None,  # 大多数解析器不需要此参数
            source_config=self._source_to_dict(),
            client=self.client
        )

        # 3. 设置文章来源
        for article in articles:
            article.source = SourceType(self.source.id)

        # 4. 关键词过滤
        filtered = self._filter_keywords(articles)

        # 5. 获取文章正文
        await self._fetch_contents(filtered)

        return filtered

    def _source_to_dict(self) -> Dict[str, Any]:
        """将配置对象转换为字典"""
        if hasattr(self.source, "dict"):
            return self.source.dict()
        elif hasattr(self.source, "model_dump"):
            return self.source.model_dump()
        else:
            return {"id": self.source.id, "name": self.source.name}

    def _load_parser(self):
        """动态加载解析器模块

        Returns:
            解析器模块
        """
        # 使用映射获取模块名
        module_id = PARSER_MODULE_MAP.get(self.source.id, self.source.id)
        module_name = f"src.crawlers.parsers.{module_id}"
        try:
            module = importlib.import_module(module_name)
            return module
        except ImportError as e:
            raise ImportError(f"解析器不存在: {module_name}. 请创建 src/crawlers/parsers/{module_id}.py") from e

    def _filter_keywords(self, articles: List[Article]) -> List[Article]:
        """根据关键词过滤文章"""
        filtered = []
        all_keywords = self.keywords

        for article in articles:
            # 检查标题和 URL
            text_to_check = f"{article.title} {article.url}".lower()
            if any(kw.lower() in text_to_check for kw in all_keywords):
                filtered.append(article)

        return filtered

    async def _fetch_contents(self, articles: List[Article]):
        """获取文章正文内容"""
        # 导入解析器的 fetch_content 函数
        try:
            parser = self._load_parser()
            fetch_func = getattr(parser, "fetch_content", None)

            if fetch_func:
                for article in articles:
                    try:
                        content = await fetch_func(article.url, self.client)
                        article.content = content
                    except Exception as e:
                        print(f"Error fetching content for {article.url}: {e}")
                        article.content = None
        except Exception as e:
            print(f"Error loading fetch_content: {e}")

    async def close(self):
        """关闭 HTTP 客户端"""
        await self.client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
