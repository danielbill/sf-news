"""数据模型定义"""

from datetime import datetime
from typing import Optional, List
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field


class SourceType(str, Enum):
    """新闻来源类型"""
    CANKAOXIAOXI = "cankaoxiaoxi"
    THEPAPER = "thepaper"
    KR36 = "36kr"
    WALLSTREETCN_LIVE = "wallstreetcn-live"
    WALLSTREETCN_NEWS = "wallstreetcn-news"
    CLS_TELEGRAPH = "cls-telegraph"
    CLS_DEPTH = "cls-depth"
    IFENG = "ifeng"
    TOUTIAO = "toutiao"


class Article(BaseModel):
    """文章数据模型"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    title: str
    url: str
    source: SourceType
    timestamp: datetime
    content: Optional[str] = None
    file_path: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    entities: List[str] = Field(default_factory=list)

    class Config:
        use_enum_values = True


class CompanyType(str, Enum):
    """公司类型"""
    SINGULARITY = "singularity"   # 奇点公司
    TIER1 = "tier1"               # 一级供应商
    TIER2 = "tier2"               # 二级供应商


class Company(BaseModel):
    """公司档案模型"""
    id: str
    name: str
    name_cn: Optional[str] = None
    type: CompanyType
    tier: int = 1
    parent_id: Optional[str] = None
    description: Optional[str] = None


class PersonTier(str, Enum):
    """人物层级"""
    SINGULARITY = "singularity"   # 奇点人物
    QUASI = "quasi"               # 准奇点人物


class Person(BaseModel):
    """人物档案模型"""
    id: str
    name: str
    name_cn: Optional[str] = None
    company_id: Optional[str] = None
    role: Optional[str] = None
    tier: PersonTier = PersonTier.QUASI
    description: Optional[str] = None


class RelationType(str, Enum):
    """关系类型"""
    SUPPLIER = "supplier"
    CUSTOMER = "customer"
    PARTNER = "partner"
    COMPETITOR = "competitor"


class Relation(BaseModel):
    """实体关系模型"""
    id: str
    from_type: str  # "company" or "person"
    from_id: str
    to_type: str
    to_id: str
    relation_type: RelationType
