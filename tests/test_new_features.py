"""测试新功能：去重、URL 缓存、通用爬虫"""

import pytest
from datetime import datetime, date
from simhash import Simhash

from src.models import Article, SourceType
from src.crawlers.dedup import TextDeduplicator
from src.crawlers.url_cache import URLCache, url_cache


class TestURLCache:
    """测试 URL 缓存"""

    def setup_method(self):
        """每个测试前清空缓存"""
        url_cache.clear()

    def test_singleton(self):
        """测试单例模式"""
        cache1 = URLCache()
        cache2 = URLCache()
        assert cache1 is cache2

    def test_add_and_exists(self):
        """测试添加和检查"""
        url_cache.add("https://example.com/1")
        assert url_cache.exists("https://example.com/1") is True
        assert url_cache.exists("https://example.com/2") is False

    def test_add_batch(self):
        """测试批量添加"""
        urls = ["https://example.com/1", "https://example.com/2"]
        url_cache.add_batch(urls)
        assert url_cache.exists("https://example.com/1") is True
        assert url_cache.exists("https://example.com/2") is True

    def test_count(self):
        """测试计数"""
        assert url_cache.count == 0
        url_cache.add("https://example.com/1")
        assert url_cache.count == 1
        url_cache.add("https://example.com/2")
        assert url_cache.count == 2

    def test_clear(self):
        """测试清空"""
        url_cache.add("https://example.com/1")
        assert url_cache.count == 1
        url_cache.clear()
        assert url_cache.count == 0


class TestTextDeduplicator:
    """测试文本去重器"""

    def test_filter_by_date(self):
        """测试时间过滤"""
        from datetime import timedelta

        deduper = TextDeduplicator()
        today = date.today()
        yesterday = today - timedelta(days=1)

        articles = [
            Article(
                title="今天的新闻",
                url="https://example.com/1",
                source=SourceType.CANKAOXIAOXI,
                timestamp=datetime.combine(today, datetime.min.time())
            ),
            Article(
                title="昨天的新闻",
                url="https://example.com/2",
                source=SourceType.CANKAOXIAOXI,
                timestamp=datetime.combine(yesterday, datetime.min.time())
            ),
        ]

        filtered = deduper._filter_by_date(articles)
        assert len(filtered) == 1
        assert filtered[0].title == "今天的新闻"

    def test_simhash_computation(self):
        """测试 SimHash 计算"""
        deduper = TextDeduplicator()

        hash1 = deduper._compute_simhash("马斯克宣布新计划")
        hash2 = deduper._compute_simhash("马斯克宣布新计划")  # 完全相同
        hash3 = deduper._compute_simhash("马斯克发布新计划")  # 略有不同
        hash4 = deduper._compute_simhash("某科技公司发布新品")  # 完全不同

        assert isinstance(hash1, Simhash)
        # 相同文本汉明距离为 0
        assert hash1.distance(hash2) == 0
        # 相似文本汉明距离较小
        assert hash1.distance(hash3) < hash1.distance(hash4)

    def test_filter_by_similarity(self):
        """测试标题相似度过滤"""
        deduper = TextDeduplicator()

        articles = [
            Article(
                title="马斯克宣布新计划",
                url="https://example.com/1",
                source=SourceType.CANKAOXIAOXI,
                timestamp=datetime.now()
            ),
            Article(
                title="马斯克宣布新计划",  # 完全相同的标题
                url="https://example.com/2",
                source=SourceType.CANKAOXIAOXI,
                timestamp=datetime.now()
            ),
            Article(
                title="某科技公司发布新品",
                url="https://example.com/3",
                source=SourceType.CANKAOXIAOXI,
                timestamp=datetime.now()
            ),
        ]

        filtered = deduper._filter_by_batch_similarity(articles)
        # 相似标题只保留一个
        assert len(filtered) == 2
        titles = [a.title for a in filtered]
        assert "马斯克宣布新计划" in titles
        assert "某科技公司发布新品" in titles


class TestUniversalCrawler:
    """测试通用爬虫"""

    def test_keywords_loaded(self):
        """测试关键词加载"""
        from src.crawlers.universal import UniversalCrawler
        from src.config.models import NewsSource

        source = NewsSource(
            id="cankaoxiaoxi",
            name="参考消息",
            type="official",
            enabled=True,
            url="https://example.com"
        )

        crawler = UniversalCrawler(source)
        keywords = crawler.keywords
        assert isinstance(keywords, list)
        assert len(keywords) > 0


class TestParserInterface:
    """测试解析器接口"""

    @pytest.mark.asyncio
    async def test_cankaoxiaoxi_parser_import(self):
        """测试参考消息解析器可导入"""
        from src.crawlers.parsers import cankaoxiaoxi

        assert hasattr(cankaoxiaoxi, "parse")
        assert hasattr(cankaoxiaoxi, "fetch_content")

    def test_base_parser_tools(self):
        """测试解析器基类工具"""
        from src.crawlers.parsers.base import get_features

        features = get_features("马斯克宣布特斯拉新计划", top_k=5)
        assert isinstance(features, list)
        # 应该返回关键词列表
        if features:
            assert isinstance(features[0], tuple) or isinstance(features[0], str)
