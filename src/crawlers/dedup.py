"""文本去重模块

实现三层去重策略：
1. 时间排重：只保留今天的文章
2. 内存/数据库排重：URL 已存在于内存缓存或今日 DB 则跳过
3. 标题相似度排重：使用 SimHash 检测相似标题
"""

from datetime import date, datetime
from typing import List
from simhash import Simhash
import jieba

from ..models import Article
from ..storage import TimelineDB
from ..tools import TitleCleaner
from .url_cache import url_cache


class TextDeduplicator:
    """文本去重器 - 三层去重策略"""

    # SimHash 汉明距离阈值（越大越宽松）
    # 对于20字的中文标题，汉明距离15表示前半部分相同
    SIMHASH_THRESHOLD = 15

    def __init__(self, target_date: date = None):
        """初始化去重器

        Args:
            target_date: 目标日期，默认为今天
        """
        self.target_date = target_date or date.today()
        self.db = TimelineDB(self.target_date)
        self.db.init_db()

        # 存储 SimHash 值，用于标题相似度去重
        self.seen_hashes: List[Simhash] = []

    def dedup(self, articles: List[Article]) -> List[Article]:
        """执行三层去重

        Args:
            articles: 待去重的文章列表

        Returns:
            去重后的文章列表
        """
        # 第一层：时间排重 - 只保留今天的文章
        today_articles = self._filter_by_date(articles)

        # 第二层：数据库排重 - URL 已存在则跳过
        url_unique = self._filter_by_db(today_articles)

        # 第三层：标题相似度排重 - SimHash
        deduped = self._filter_by_similarity(url_unique)

        return deduped

    def _filter_by_date(self, articles: List[Article]) -> List[Article]:
        """时间排重：只保留目标日期的文章"""
        return [
            a for a in articles
            if a.timestamp.date() == self.target_date
        ]

    def _filter_by_db(self, articles: List[Article]) -> List[Article]:
        """内存/数据库排重：
        1. 先检查内存缓存（快速，O(1)）
        2. 再检查数据库（持久化）
        """
        url_unique = []
        for article in articles:
            # 先检查内存缓存
            if url_cache.exists(article.url):
                continue

            # 再检查数据库
            if not self.db.article_exists(article.url):
                url_unique.append(article)

        # 将去重后的 URL 添加到内存缓存
        url_cache.add_batch([a.url for a in url_unique])

        return url_unique

    def _filter_by_similarity(self, articles: List[Article]) -> List[Article]:
        """标题相似度排重：使用 SimHash 检测相似标题

        相似度判断逻辑：
        - 计算标题的 SimHash 值
        - 与已见过的 hash 值比较汉明距离
        - 汉明距离 <= SIMHASH_THRESHOLD 则认为是重复
        """
        deduped = []

        for article in articles:
            # 计算 SimHash
            hash_value = self._compute_simhash(article.title)

            # 检查是否与已有标题相似
            is_similar = False
            for seen_hash in self.seen_hashes:
                if hash_value.distance(seen_hash) <= self.SIMHASH_THRESHOLD:
                    is_similar = True
                    break

            if not is_similar:
                deduped.append(article)
                self.seen_hashes.append(hash_value)

        return deduped

    def _compute_simhash(self, text: str) -> Simhash:
        """计算文本的 SimHash 值

        使用 jieba 分词提取关键词作为特征
        只取前20个字用于去重，只保留中英文数字
        """
        # 使用 TitleCleaner 清理标题（默认20个字）
        text = TitleCleaner.for_dedup(text)
        # 使用 jieba 分词
        words = list(jieba.cut(text))
        return Simhash(words)

    def get_stats(self, original_count: int, final_count: int) -> dict:
        """获取去重统计信息"""
        return {
            "original": original_count,
            "final": final_count,
            "removed": original_count - final_count,
            "rate": f"{(1 - final_count / original_count * 100) if original_count > 0 else 0:.1f}%"
        }
