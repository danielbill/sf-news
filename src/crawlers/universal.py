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
from ..config.reader import ConfigReader

# source.id → 解析器模块名 的映射
# 仅列出文件名因 Python 模块命名规范（不能以数字开头、不能含连字符）
# 而与 source.id 不一致的条目；其余 id 直接作为模块名使用。
_ID_TO_MODULE = {
    "36kr-ai": "kr36_ai",
    "venturebeat-ai": "venturebeat_ai",
    "mit-tech-review-ai": "mit_tech_review_ai",
    "infoq-ai": "infoq_ai",
}


class UniversalCrawler:
    """通用爬虫 - 根据配置自动加载解析器"""

    def __init__(self, source_config: Any, config_dir: str = "config", news_batch_limit: int = None):
        """初始化通用爬虫

        Args:
            source_config: 新闻源配置对象
            config_dir: 配置文件目录
            news_batch_limit: 每次抓取的条数限制（可选，默认从配置读取）
        """
        self.source = source_config
        self.config_dir = config_dir

        # 读取 limit 配置
        if news_batch_limit is None:
            try:
                reader = ConfigReader(config_dir)
                crawler_config = reader.load_crawler_config()
                news_batch_limit = crawler_config.strategy.news_batch_limit
            except Exception as e:
                print(f"Warning: Failed to load news_batch_limit: {e}")
                news_batch_limit = 20  # 默认值
        self.news_batch_limit = news_batch_limit

        # 使用连接池限制，防止连接泄漏
        self.client = httpx.AsyncClient(
            timeout=30,
            limits=httpx.Limits(
                max_connections=10,      # 最大连接数
                max_keepalive_connections=5,  # 保持活动的连接数
                keepalive_expiry=30.0,    # keepalive 过期时间
            ),
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        )

    async def fetch(self) -> List[Article]:
        """抓取并解析文章

        Returns:
            文章列表
        """
        # 1. 动态加载解析器
        parser = self._load_parser()

        # 2. 调用解析器获取文章
        articles = await parser.parse(
            response=None,  # 大多数解析器不需要此参数
            source_config=self._source_to_dict(),
            client=self.client,
            limit=self.news_batch_limit
        )

        # 3. 设置文章来源
        for article in articles:
            article.source = SourceType(self.source.id)

        # 4. 获取文章正文
        await self._fetch_contents(articles)

        return articles

    def _source_to_dict(self) -> Dict[str, Any]:
        """将配置对象转换为字典"""
        if hasattr(self.source, "dict"):
            result = self.source.dict()
        elif hasattr(self.source, "model_dump"):
            result = self.source.model_dump()
        else:
            result = {"id": self.source.id, "name": self.source.name}

        # 替换 URL 中的 {limit} 占位符
        if "url" in result and "{limit}" in result["url"]:
            result["url"] = result["url"].replace("{limit}", str(self.news_batch_limit))

        return result

    def _load_parser(self):
        """动态加载解析器模块

        Returns:
            解析器模块
        """
        # source.id 可能因为 Python 命名规范（连字符、数字开头）
        # 与实际模块文件名不一致，通过 _ID_TO_MODULE 做映射。
        module_suffix = _ID_TO_MODULE.get(self.source.id, self.source.id)
        module_name = f"src.crawlers.parsers.{module_suffix}"
        try:
            module = importlib.import_module(module_name)
            return module
        except ImportError as e:
            raise ImportError(f"解析器不存在: {module_name}. 请创建 src/crawlers/parsers/{module_suffix}.py") from e

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
