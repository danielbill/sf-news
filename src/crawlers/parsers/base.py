"""解析器基类和工具函数

提供解析器开发中常用的工具函数
"""

from typing import List, Dict, Any, Optional
from httpx import Response
from bs4 import BeautifulSoup
import json


def get_features(text: str, top_k: int = 20) -> List[tuple]:
    """提取文本特征用于 SimHash

    Args:
        text: 输入文本
        top_k: 返回前 k 个关键词

    Returns:
        [(keyword, weight), ...] 特征列表
    """
    import jieba.analyse
    return jieba.analyse.extract_tags(text, topK=top_k, withWeight=True)


def parse_html(response: Response, selector: str, **fields) -> List[Dict[str, Any]]:
    """解析 HTML 响应

    Args:
        response: HTTP 响应对象
        selector: CSS 选择器，用于选择文章列表
        **fields: 字段映射，如 title=".title", url="a@href"

    Returns:
        解析后的数据列表

    Example:
        data = parse_html(
            response,
            selector=".news-item",
            title=".title",
            url="a@href",
            time=".time"
        )
    """
    soup = BeautifulSoup(response.text, "html.parser")
    items = soup.select(selector)
    results = []

    for item in items:
        row = {}
        for field_name, field_selector in fields.items():
            # 处理属性选择器，如 "a@href"
            if "@" in field_selector:
                elem_selector, attr = field_selector.split("@", 1)
                elem = item.select_one(elem_selector)
                value = elem.get(attr) if elem else None
            else:
                elem = item.select_one(field_selector)
                value = elem.get_text(strip=True) if elem else None

            row[field_name] = value
        results.append(row)

    return results


def parse_json(response: Response, data_path: str = None) -> Dict[str, Any]:
    """解析 JSON 响应

    Args:
        response: HTTP 响应对象
        data_path: JSON 路径，如 "data.items" 用于提取嵌套数据

    Returns:
        解析后的字典
    """
    data = json.loads(response.text)

    if data_path:
        for key in data_path.split("."):
            data = data.get(key, [])

    return data
