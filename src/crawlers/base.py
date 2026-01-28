"""爬虫基类"""

from abc import ABC, abstractmethod
from typing import List, Dict, Set
import httpx
from pathlib import Path

from ..models import Article
from ..config import ConfigReader


class BaseCrawler(ABC):
    """爬虫基类"""

    def __init__(self, timeout: int = 30, config_dir: str = "config"):
        self.timeout = timeout
        self.client = httpx.AsyncClient(
            timeout=timeout,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        )
        # 加载关键词配置
        self._keywords = self._load_keywords(config_dir)

    def _load_keywords(self, config_dir: str) -> Dict[str, List[str]]:
        """从配置文件加载关键词"""
        try:
            reader = ConfigReader(config_dir)
            config = reader.load_news_keywords_config()

            # 展平所有关键词
            all_keywords: Set[str] = set()

            # 人物关键词
            for person_keywords in config.get("people", {}).values():
                all_keywords.update(person_keywords)

            # 公司关键词
            for company_keywords in config.get("companies", {}).values():
                all_keywords.update(company_keywords)

            # 话题关键词
            for topic_group in config.get("topics", []):
                all_keywords.update(topic_group)

            return {
                "people": config.get("people", {}),
                "companies": config.get("companies", {}),
                "topics": config.get("topics", []),
                "all": list(all_keywords)
            }
        except Exception as e:
            print(f"Warning: Failed to load keywords config: {e}")
            return {"all": []}

    @property
    def keywords(self) -> List[str]:
        """获取所有关键词（用于过滤）"""
        return self._keywords.get("all", [])

    @abstractmethod
    async def fetch(self) -> List[Article]:
        """抓取并返回文章列表"""
        pass

    def filter_keywords(self, articles: List[Article]) -> List[Article]:
        """根据关键词过滤文章"""
        filtered = []
        all_keywords = self.keywords

        for article in articles:
            # 检查标题和 URL
            text_to_check = f"{article.title} {article.url}".lower()
            if any(kw.lower() in text_to_check for kw in all_keywords):
                filtered.append(article)

        return filtered

    def _sanitize_filename(self, title: str, max_length: int = 200) -> str:
        """将标题转换为安全的文件名

        - 移除/替换特殊字符
        - 移除空格
        - 限制长度
        - 保留中文
        """
        import re
        import unicodedata

        # 移除或替换Windows文件系统非法字符
        illegal_chars = r'[<>:"/\\|?*]'
        safe_title = re.sub(illegal_chars, '-', title)

        # 移除空格
        safe_title = safe_title.replace(' ', '')

        # 移除控制字符
        safe_title = ''.join(char for char in safe_title
                             if not unicodedata.category(char).startswith('C'))

        # 去除首尾空格和点
        safe_title = safe_title.strip('. ')

        # 限制长度
        if len(safe_title) > max_length:
            safe_title = safe_title[:max_length]

        # 如果处理后为空，使用默认名称
        if not safe_title:
            safe_title = "untitled"

        return safe_title

    async def save_article(self, article: Article) -> bool:
        """保存文章到数据库和文件系统

        Returns:
            bool: 是否保存成功（False 表示文章已存在）
        """
        from ..storage import TimelineDB
        from datetime import date
        from pathlib import Path
        import uuid

        # 检查是否已存在
        db = TimelineDB(date.today())
        db.init_db()

        if db.article_exists(article.url):
            return False  # 文章已存在，跳过

        # 生成文章文件路径
        article_date = date.today()
        articles_dir = Path(f"data/articles/{article_date.strftime('%Y/%m/%d')}")
        articles_dir.mkdir(parents=True, exist_ok=True)

        # 生成安全的文件名（处理后的标题）
        safe_title = self._sanitize_filename(article.title)
        file_name = f"{safe_title}.md"
        file_path = articles_dir / file_name

        # 处理 source - 可能是枚举或字符串
        source_value = article.source
        if hasattr(article.source, 'value'):
            source_value = article.source.value

        # 总是创建文件（即使没有正文内容）
        content = f"# {article.title}\n\n"
        content += f"> 来源: {source_value}\n"
        content += f"> 时间: {article.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n"
        content += f"> 链接: {article.url}\n\n"

        if article.content:
            content += article.content
        else:
            content += "*（正文内容未获取）*\n"

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        article.file_path = str(file_path)

        # 保存到数据库
        db.insert_article(article)
        return True

    async def close(self):
        """关闭 HTTP 客户端"""
        await self.client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
