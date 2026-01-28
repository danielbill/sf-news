"""配置数据模型"""

from typing import List, Optional, Dict
from pydantic import BaseModel, Field


class Legend(BaseModel):
    """奇点人物"""
    id: str
    name: str
    name_cn: str
    tier: str = "singularity"  # singularity | quasi
    company_id: Optional[str] = None
    role: Optional[str] = None
    description: Optional[str] = None


class LegendConfig(BaseModel):
    """奇点人物配置"""
    legends: List[Legend]


class Company(BaseModel):
    """公司"""
    id: str
    name: str
    name_cn: Optional[str] = None
    tier: int = 1
    type: str = "singularity"  # singularity | tier1 | tier2
    legend_id: Optional[str] = None
    description: Optional[str] = None
    keywords: Optional[List[str]] = None


class CompanyConfig(BaseModel):
    """公司档案配置"""
    companies: List[Company]

    class Config:
        # 简化兼容性
        extra = "allow"


class Relation(BaseModel):
    """公司关系"""
    from_id: str
    to_id: str
    type: str  # partner | subsidiary | supplier
    description: Optional[str] = None


class CompanyRelationsConfig(BaseModel):
    """公司关系配置"""
    companies: List[Company]
    relations: List[Relation]


class NewsSource(BaseModel):
    """新闻源"""
    id: str
    name: str
    type: str  # official | financial | tech | portal
    enabled: bool = True
    url: str
    channels: Optional[List[str]] = None

    class Config:
        extra = "allow"  # 允许额外字段，向后兼容


class NewsSourcesConfig(BaseModel):
    """新闻源配置"""
    sources: List[NewsSource]


class NewsKeywordsConfig(BaseModel):
    """新闻关键词配置（动态结构）"""
    people: Dict[str, List[str]] = {}
    companies: Dict[str, List[str]] = {}
    topics: List[List[str]] = []

    class Config:
        extra = "allow"


class StrategyConfig(BaseModel):
    """抓取策略"""
    interval: int  # 抓取间隔（秒）
    min_interval: int  # 最小抓取间隔限制
    concurrent: int  # 并发抓取数量


class NetworkConfig(BaseModel):
    """网络配置"""
    timeout: int = 30
    retry: int = 3
    retry_delay: int = 5
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"


class StorageConfig(BaseModel):
    """存储配置"""
    save_content: bool = True
    dedup: bool = True
    content_format: str = "markdown"
    db_path: str = "data/db/scheduler.sqlite"  # 调度器数据库路径


class LoggingConfig(BaseModel):
    """日志配置"""
    level: str = "INFO"
    save_logs: bool = True
    log_dir: str = "logs"


class CrawlerConfig(BaseModel):
    """抓取器配置"""
    strategy: StrategyConfig
    network: NetworkConfig
    storage: StorageConfig
    logging: LoggingConfig
