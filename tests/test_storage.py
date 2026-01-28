"""测试存储模块"""

import pytest

from src.storage import TimelineDB
from src.models import Article, SourceType
from datetime import datetime


class TestTimelineDB:
    """测试 TimelineDB"""

    def test_init_db(self, test_db):
        """测试数据库初始化"""
        # 数据库应该已初始化
        assert test_db.db_path.exists()

    def test_insert_article(self, test_db, sample_article):
        """测试插入文章"""
        test_db.insert_article(sample_article)
        retrieved = test_db.get_article(sample_article.id)
        assert retrieved is not None
        assert retrieved["title"] == sample_article.title

    def test_article_exists(self, test_db, sample_article):
        """测试文章存在性检查"""
        assert not test_db.article_exists(sample_article.url)
        test_db.insert_article(sample_article)
        assert test_db.article_exists(sample_article.url)

    def test_list_articles(self, test_db, sample_article):
        """测试列出文章"""
        test_db.insert_article(sample_article)
        articles = test_db.list_articles(limit=10)
        assert len(articles) >= 1
        assert articles[0]["title"] == sample_article.title

    def test_get_nonexistent_article(self, test_db):
        """测试获取不存在的文章"""
        result = test_db.get_article("nonexistent-id")
        assert result is None
