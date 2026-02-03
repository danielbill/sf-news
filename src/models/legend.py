"""Legend 数据模型

Legend 实体数据模型，支持人物(PERSON)和组织(ORGANIZATION)两种类型。
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


# =============================================================================
# 枚举定义
# =============================================================================


class LegendType(str, Enum):
    """Legend 实体类型"""
    PERSON = "PERSON"
    ORGANIZATION = "ORGANIZATION"


class LegendTier(str, Enum):
    """传奇等级 - 定义该实体的历史地位"""
    SINGULARITY = "SINGULARITY"   # 奇点 — 引发文明级跃迁
    QUASI = "QUASI"               # 准奇点 — 引发行业级变革
    POTENTIAL = "POTENTIAL"       # 潜力 — 有可能成为奇点


class ImpactLevel(str, Enum):
    """影响等级 - 定义该实体的影响范围"""
    SINGULARITY = "SINGULARITY"   # 文明级 — 改变人类文明进程
    INDUSTRY = "INDUSTRY"         # 行业级 — 重塑某个行业
    COMPANY = "COMPANY"           # 公司级 — 影响公司自身


class OrgType(str, Enum):
    """组织类型"""
    PUBLIC = "PUBLIC"             # 上市公司
    PRIVATE = "PRIVATE"           # 私营公司
    NONPROFIT = "NONPROFIT"       # 非营利组织


class ProductStatus(str, Enum):
    """产品状态"""
    ACTIVE = "active"             # 在售
    DISCONTINUED = "discontinued" # 已停产
    UPCOMING = "upcoming"         # 即将推出


# =============================================================================
# 基础模型
# =============================================================================


class LegendBase(BaseModel):
    """Legend 基础字段"""
    name_en: Optional[str] = None
    name_cn: Optional[str] = None
    avatar_url: Optional[str] = None
    bio_short: Optional[str] = Field(None, max_length=500)


class Legend(LegendBase):
    """Legend 实体"""
    id: str
    type: LegendType
    legend_tier: LegendTier = LegendTier.POTENTIAL
    impact_level: ImpactLevel = ImpactLevel.COMPANY
    file_path: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class LegendKeywordGroup(BaseModel):
    """关键词组 - 来自 news_keywords.yaml"""
    group_name: Optional[str] = None  # 分组名称（可选）
    keywords: List[str]               # 关键词列表


class LegendKeyword(BaseModel):
    """Legend 关键词（数据库记录）"""
    id: Optional[int] = None
    legend_id: str
    keyword_group: Optional[str] = None
    keywords: List[str]               # 存储为 JSON 数组
    source_hash: Optional[str] = None  # 来源 YAML 的哈希值
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class LegendProduct(BaseModel):
    """Legend 产品/服务"""
    id: Optional[int] = None
    legend_id: str
    product_name: str
    description: Optional[str] = None
    status: ProductStatus = ProductStatus.ACTIVE
    category: Optional[str] = None
    company_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CompanyRelation(BaseModel):
    """人物-公司关联关系"""
    id: Optional[int] = None
    person_id: str
    company_id: str
    role: Optional[str] = None       # CEO | Founder | CTO | Advisor
    is_primary: bool = False
    start_date: Optional[str] = None
    end_date: Optional[str] = None   # 空=现任
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SyncLog(BaseModel):
    """同步日志"""
    id: Optional[int] = None
    sync_type: str                   # scan | create | update | delete
    legend_id: Optional[str] = None
    change_type: Optional[str] = None  # added | removed | keywords_changed
    details: Optional[Dict[str, Any]] = None
    synced_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# =============================================================================
# 创建/更新 DTO
# =============================================================================


class LegendCreate(LegendBase):
    """创建 Legend"""
    id: str
    type: LegendType
    legend_tier: LegendTier = LegendTier.POTENTIAL
    impact_level: ImpactLevel = ImpactLevel.COMPANY


class LegendUpdate(BaseModel):
    """更新 Legend"""
    name_en: Optional[str] = None
    name_cn: Optional[str] = None
    avatar_url: Optional[str] = None
    bio_short: Optional[str] = Field(None, max_length=500)
    legend_tier: Optional[LegendTier] = None
    impact_level: Optional[ImpactLevel] = None


class LegendFilters(BaseModel):
    """Legend 查询过滤器"""
    type: Optional[LegendType] = None
    tier: Optional[LegendTier] = None
    impact_level: Optional[ImpactLevel] = None
    limit: int = 100
    offset: int = 0


class ProductCreate(BaseModel):
    """创建产品"""
    legend_id: str
    product_name: str
    description: Optional[str] = None
    status: ProductStatus = ProductStatus.ACTIVE
    category: Optional[str] = None
    company_id: Optional[str] = None


class CompanyRelationCreate(BaseModel):
    """创建人物-公司关联"""
    person_id: str
    company_id: str
    role: Optional[str] = None
    is_primary: bool = False
    start_date: Optional[str] = None
    end_date: Optional[str] = None


# =============================================================================
# 同步结果
# =============================================================================


class SyncResult(BaseModel):
    """同步结果"""
    has_changes: bool
    file_hash: str
    added: List[str] = []
    removed: List[str] = []
    keywords_updated: List[str] = []
    unchanged: int = 0
    synced_at: Optional[datetime] = None


# =============================================================================
# 完整 Legend 详情（含关联数据）
# =============================================================================


class LegendDetail(Legend):
    """Legend 完整详情"""
    keywords: List[LegendKeyword] = []
    products: List[LegendProduct] = []
    companies: List[CompanyRelation] = []  # 仅当 type=PERSON 时
    markdown_content: Optional[str] = None


# =============================================================================
# YAML 解析模型
# =============================================================================


class YamlLegendEntry(BaseModel):
    """从 news_keywords.yaml 解析的 Legend 条目"""
    legend_id: str
    keywords: List[List[str]]        # YAML 中的关键词数组
    flat_keywords: List[str] = []    # 展平后的关键词列表


class YamlKeywordsConfig(BaseModel):
    """news_keywords.yaml 解析结果"""
    legends: Dict[str, List[List[str]]]  # legend_id -> keywords
    front: List[List[str]]                  # front 关键词
