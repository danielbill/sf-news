# 新闻抓取模块技术规格

## 概述

从国内官媒和科技媒体抓取与奇点人物/公司相关的新闻动态。

## 参考实现

`D:\awesome_projects\newsnow` 项目中的数据源实现。

## 数据源

### 第一阶段（MVP）

| 数据源 | 类型 | URL | 实现文件 |
|--------|------|-----|----------|
| 参考消息 | 官媒 API | `https://china.cankaoxiaoxi.com/json/channel/{channel}/list.json` | `cankaoxiaoxi.py` |
| 澎湃新闻 | 权威 API | `https://cache.thepaper.cn/contentapi/wwwIndex/rightSidebar` | `thepaper.py` |
| 36氪 | 科技爬虫 | `https://www.36kr.com/newsflashes` | `36kr.py` |

## 数据模型

```python
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from enum import Enum

class SourceType(str, Enum):
    CANKAOXIAOXI = "cankaoxiaoxi"
    THEPAPER = "thepaper"
    KR36 = "36kr"

class Article(BaseModel):
    id: str                      # UUID
    title: str                   # 标题
    url: str                     # 原始链接
    source: SourceType           # 来源
    timestamp: datetime          # 发布时间
    content: Optional[str]       # 正文内容
    file_path: str               # 文件存储路径
    tags: List[str] = []         # 标签
    entities: List[str] = []     # 提取的实体

    class Config:
        use_enum_values = True
```

## 爬虫接口

```python
from abc import ABC, abstractmethod
from typing import List

class BaseCrawler(ABC):
    @abstractmethod
    async def fetch(self) -> List[Article]:
        """抓取并返回文章列表"""
        pass

    @abstractmethod
    def filter_keywords(self, articles: List[Article]) -> List[Article]:
        """根据关键词过滤文章"""
        pass

    async def save(self, articles: List[Article]) -> None:
        """保存文章到数据库和文件"""
        pass
```

## 关键词配置

```python
KEYWORDS = {
    "people": ["马斯克", "埃隆·马斯克", "Elon Musk"],
    "companies": ["特斯拉", "Tesla", "SpaceX", "X", "xAI"],
    "topics": ["星舰", "星链", "FSD", "自动驾驶", "电动车"]
}
```

## 错误处理

1. HTTP 请求失败：重试 3 次，指数退避
2. 解析失败：记录日志，跳过该条目
3. 存储失败：回滚事务，报告错误

## 性能要求

1. 单个爬虫运行时间 < 30 秒
2. 所有爬虫并发运行 < 60 秒
3. 每小时抓取频率不超过 API 限制
