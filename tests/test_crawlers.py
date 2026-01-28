"""测试爬虫模块"""

import pytest
from datetime import datetime

from src.crawlers import CankaoxiaoxiCrawler
from src.models import SourceType


class TestBaseCrawler:
    """测试爬虫基类"""

    def test_keywords_loaded(self):
        """测试关键词配置已加载"""
        crawler = CankaoxiaoxiCrawler()
        keywords = crawler.keywords
        assert isinstance(keywords, list)
        assert len(keywords) > 0
        # 检查是否包含马斯克相关关键词
        assert any("马斯克" in kw for kw in keywords)

    def test_filter_keywords(self):
        """测试关键词过滤"""
        from src.models import Article

        crawler = CankaoxiaoxiCrawler()
        articles = [
            Article(
                title="马斯克宣布新计划",
                url="https://example.com/1",
                source=SourceType.CANKAOXIAOXI,
                timestamp=datetime.now()
            ),
            Article(
                title="某科技公司发布新品",
                url="https://example.com/2",
                source=SourceType.CANKAOXIAOXI,
                timestamp=datetime.now()
            ),
        ]

        filtered = crawler.filter_keywords(articles)
        assert len(filtered) == 1
        assert filtered[0].title == "马斯克宣布新计划"


class TestCankaoxiaoxiCrawler:
    """测试参考消息爬虫"""

    @pytest.mark.asyncio
    async def test_crawler_init(self):
        """测试爬虫初始化"""
        crawler = CankaoxiaoxiCrawler()
        assert crawler.channels == ["zhongguo", "guandian", "gj"]
        assert crawler.client is not None

    @pytest.mark.asyncio
    async def test_crawler_close(self):
        """测试爬虫关闭"""
        crawler = CankaoxiaoxiCrawler()
        await crawler.close()
        assert True  # 无异常即成功
