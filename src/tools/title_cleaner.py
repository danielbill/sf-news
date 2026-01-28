"""文本清理工具

用于清理新闻标题，统一格式以便去重
"""

import re
from typing import List


class TitleCleaner:
    """标题清理器 - 统一标题格式以便去重"""

    # 需要清理的 HTML 实体
    HTML_ENTITIES = {
        "&amp;": "&",
        "&quot;": '"',
        "&lt;": "<",
        "&gt;": ">",
        "&#39;": "'",
        "&apos;": "'",
    }

    @classmethod
    def for_dedup(cls, title: str, max_length: int = 20) -> str:
        """清理标题用于去重

        只保留中英文数字，去除其他符号
        步骤：先清理HTML实体，再去符号，最后截断
        默认只取前20个字进行比较

        Args:
            title: 原始标题
            max_length: 最大长度，默认20

        Returns:
            清理后的标题
        """
        # 先清理 HTML 实体
        for entity, char in cls.HTML_ENTITIES.items():
            title = title.replace(entity, char)

        # 只保留中英文数字
        title = re.sub(r'[^a-zA-Z0-9\u4e00-\u9fff]', '', title)

        # 最后截断到指定长度
        title = title[:max_length]

        return title

    @classmethod
    def clean_filename(cls, title: str, max_length: int = 100) -> str:
        """清理标题用于文件名

        去除文件名不允许的字符

        Args:
            title: 原始标题
            max_length: 最大长度，默认100

        Returns:
            清理后的标题
        """
        # 截断到指定长度
        title = title[:max_length]

        # 替换文件名不允许的字符
        title = title.replace('/', '-').replace('\\', '-').replace(':', '-')
        title = title.replace('*', '-').replace('?', '-').replace('"', '-')
        title = title.replace('<', '-').replace('>', '-').replace('|', '-')
        title = title.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')

        # 去除首尾空格
        title = title.strip()

        return title

    @classmethod
    def get_keywords(cls, title: str) -> List[str]:
        """从标题中提取关键词

        只保留中英文单词

        Args:
            title: 原始标题

        Returns:
            关键词列表
        """
        # 清理 HTML 实体
        for entity, char in cls.HTML_ENTITIES.items():
            title = title.replace(entity, char)

        # 只保留中英文数字和空格
        title = re.sub(r'[^a-zA-Z0-9\u4e00-\u9fff\s]', ' ', title)

        # 分割成单词
        words = title.split()

        return words
