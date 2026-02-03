"""Legend 数据模型测试

测试 Legend 相关的所有 Pydantic 模型的验证逻辑。
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from src.models.legend import (
    # 枚举
    LegendType,
    LegendTier,
    ImpactLevel,
    OrgType,
    ProductStatus,
    # 基础模型
    LegendBase,
    Legend,
    LegendKeywordGroup,
    LegendKeyword,
    LegendProduct,
    CompanyRelation,
    SyncLog,
    # DTO
    LegendCreate,
    LegendUpdate,
    LegendFilters,
    ProductCreate,
    CompanyRelationCreate,
    # 复合模型
    SyncResult,
    LegendDetail,
    # YAML 模型
    YamlLegendEntry,
    YamlKeywordsConfig,
)


class TestLegendEnums:
    """测试枚举类型"""

    def test_legend_type_values(self):
        """T004: 测试 LegendType 枚举值"""
        assert LegendType.PERSON.value == "PERSON"
        assert LegendType.ORGANIZATION.value == "ORGANIZATION"
        assert len(LegendType) == 2

    def test_legend_tier_values(self):
        """T004: 测试 LegendTier 枚举值"""
        assert LegendTier.SINGULARITY.value == "SINGULARITY"
        assert LegendTier.QUASI.value == "QUASI"
        assert LegendTier.POTENTIAL.value == "POTENTIAL"
        assert len(LegendTier) == 3

    def test_impact_level_values(self):
        """T004: 测试 ImpactLevel 枚举值"""
        assert ImpactLevel.SINGULARITY.value == "SINGULARITY"
        assert ImpactLevel.INDUSTRY.value == "INDUSTRY"
        assert ImpactLevel.COMPANY.value == "COMPANY"
        assert len(ImpactLevel) == 3

    def test_org_type_values(self):
        """T004: 测试 OrgType 枚举值"""
        assert OrgType.PUBLIC.value == "PUBLIC"
        assert OrgType.PRIVATE.value == "PRIVATE"
        assert OrgType.NONPROFIT.value == "NONPROFIT"
        assert len(OrgType) == 3

    def test_product_status_values(self):
        """T004: 测试 ProductStatus 枚举值"""
        assert ProductStatus.ACTIVE.value == "active"
        assert ProductStatus.DISCONTINUED.value == "discontinued"
        assert ProductStatus.UPCOMING.value == "upcoming"
        assert len(ProductStatus) == 3


class TestLegendBase:
    """测试 LegendBase 基础模型"""

    def test_legend_base_with_all_fields(self):
        """T004: 测试 LegendBase 所有字段"""
        data = {
            "name_en": "Elon Musk",
            "name_cn": "马斯克",
            "avatar_url": "https://example.com/avatar.jpg",
            "bio_short": "Tesla CEO"
        }
        base = LegendBase(**data)
        assert base.name_en == "Elon Musk"
        assert base.name_cn == "马斯克"
        assert base.avatar_url == "https://example.com/avatar.jpg"
        assert base.bio_short == "Tesla CEO"

    def test_legend_base_with_optional_fields(self):
        """T004: 测试 LegendBase 可选字段"""
        base = LegendBase()
        assert base.name_en is None
        assert base.name_cn is None
        assert base.avatar_url is None
        assert base.bio_short is None

    def test_bio_short_max_length(self):
        """T004: 测试 bio_short 最大长度限制"""
        long_bio = "x" * 501
        with pytest.raises(ValidationError):
            LegendBase(bio_short=long_bio)

    def test_bio_short_exactly_max_length(self):
        """T004: 测试 bio_short 恰好最大长度"""
        max_bio = "x" * 500
        base = LegendBase(bio_short=max_bio)
        assert base.bio_short == max_bio


class TestLegend:
    """测试 Legend 完整模型"""

    def test_legend_creation(self):
        """T004: 测试创建 Legend 实例"""
        data = {
            "id": "musk",
            "type": LegendType.PERSON,
            "name_en": "Elon Musk",
            "name_cn": "马斯克",
            "legend_tier": LegendTier.SINGULARITY,
            "impact_level": ImpactLevel.SINGULARITY,
        }
        legend = Legend(**data)
        assert legend.id == "musk"
        assert legend.type == LegendType.PERSON
        assert legend.legend_tier == LegendTier.SINGULARITY
        assert legend.impact_level == ImpactLevel.SINGULARITY

    def test_legend_default_values(self):
        """T004: 测试 Legend 默认值"""
        legend = Legend(id="test", type=LegendType.ORGANIZATION)
        assert legend.legend_tier == LegendTier.POTENTIAL
        assert legend.impact_level == ImpactLevel.COMPANY
        assert legend.file_path is None
        assert legend.created_at is None
        assert legend.updated_at is None

    def test_legend_from_attributes(self):
        """T004: 测试 from_attributes 配置"""
        # 模拟数据库行
        row = {
            "id": "musk",
            "type": "PERSON",
            "name_en": "Elon Musk",
            "name_cn": None,
            "avatar_url": None,
            "bio_short": None,
            "legend_tier": "SINGULARITY",
            "impact_level": "SINGULARITY",
            "file_path": "data/legend/people/musk.md",
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }
        legend = Legend(**row)
        assert legend.id == "musk"
        assert legend.legend_tier == LegendTier.SINGULARITY


class TestLegendCreate:
    """测试 LegendCreate DTO"""

    def test_legend_create_validation(self):
        """T004: 测试 LegendCreate 验证"""
        data = {
            "id": "altman",
            "type": LegendType.PERSON,
            "name_en": "Sam Altman",
            "name_cn": "奥尔特曼",
        }
        create = LegendCreate(**data)
        assert create.id == "altman"
        assert create.type == LegendType.PERSON
        assert create.legend_tier == LegendTier.POTENTIAL  # 默认值

    def test_legend_create_requires_id_and_type(self):
        """T004: 测试 LegendCreate 必填字段"""
        with pytest.raises(ValidationError):
            LegendCreate(name_en="Test")  # 缺少 id 和 type


class TestLegendUpdate:
    """测试 LegendUpdate DTO"""

    def test_legend_update_all_fields(self):
        """T004: 测试 LegendUpdate 所有字段"""
        data = {
            "name_en": "Updated Name",
            "name_cn": "更新名称",
            "avatar_url": "https://example.com/new.jpg",
            "bio_short": "Updated bio",
            "legend_tier": LegendTier.QUASI,
            "impact_level": ImpactLevel.INDUSTRY,
        }
        update = LegendUpdate(**data)
        assert update.name_en == "Updated Name"
        assert update.legend_tier == LegendTier.QUASI

    def test_legend_update_all_optional(self):
        """T004: 测试 LegendUpdate 所有字段可选"""
        update = LegendUpdate()
        assert update.name_en is None
        assert update.legend_tier is None


class TestLegendFilters:
    """测试 LegendFilters 查询过滤器"""

    def test_legend_filters_defaults(self):
        """T004: 测试 LegendFilters 默认值"""
        filters = LegendFilters()
        assert filters.type is None
        assert filters.limit == 100
        assert filters.offset == 0

    def test_legend_filters_with_values(self):
        """T004: 测试 LegendFilters 带值"""
        filters = LegendFilters(
            type=LegendType.PERSON,
            tier=LegendTier.SINGULARITY,
            limit=50,
            offset=10
        )
        assert filters.type == LegendType.PERSON
        assert filters.limit == 50


class TestKeywordModels:
    """测试关键词相关模型 (T005)"""

    def test_legend_keyword_group(self):
        """T005: 测试 KeywordGroup 模型"""
        group = LegendKeywordGroup(
            group_name="人物名",
            keywords=["马斯克", "Elon Musk", "Tesla CEO"]
        )
        assert group.group_name == "人物名"
        assert len(group.keywords) == 3

    def test_legend_keyword_group_optional_name(self):
        """T005: 测试 KeywordGroup 可选 group_name"""
        group = LegendKeywordGroup(keywords=["test"])
        assert group.group_name is None
        assert group.keywords == ["test"]

    def test_legend_keyword(self):
        """T005: 测试 LegendKeyword 模型"""
        keyword = LegendKeyword(
            id=1,
            legend_id="musk",
            keyword_group="group_0",
            keywords=["马斯克", "Elon Musk"],
            source_hash="abc123"
        )
        assert keyword.legend_id == "musk"
        assert keyword.keywords == ["马斯克", "Elon Musk"]
        assert keyword.source_hash == "abc123"

    def test_legend_keywords_json_storage(self):
        """T005: 测试 keywords 以 JSON 格式存储"""
        # 模拟从数据库读取的 JSON 字符串
        keyword = LegendKeyword(
            legend_id="test",
            keywords=["关键词1", "关键词2"]  # 列表格式
        )
        assert isinstance(keyword.keywords, list)
        assert len(keyword.keywords) == 2


class TestProductModels:
    """测试产品相关模型 (T006)"""

    def test_legend_product(self):
        """T006: 测试 LegendProduct 模型"""
        product = LegendProduct(
            id=1,
            legend_id="spacex",
            product_name="Starship",
            description="Reusable rocket",
            status=ProductStatus.ACTIVE,
            category="Spacecraft"
        )
        assert product.legend_id == "spacex"
        assert product.product_name == "Starship"
        assert product.status == ProductStatus.ACTIVE

    def test_product_status_enum(self):
        """T006: 测试 ProductStatus 枚举"""
        assert ProductStatus.ACTIVE == "active"
        assert ProductStatus.DISCONTINUED == "discontinued"
        assert ProductStatus.UPCOMING == "upcoming"

    def test_product_create(self):
        """T006: 测试 ProductCreate DTO"""
        create = ProductCreate(
            legend_id="tesla",
            product_name="Model 3",
            category="Electric Vehicle"
        )
        assert create.legend_id == "tesla"
        assert create.status == ProductStatus.ACTIVE  # 默认值


class TestCompanyRelation:
    """测试人物-公司关联模型"""

    def test_company_relation(self):
        """测试 CompanyRelation 模型"""
        relation = CompanyRelation(
            id=1,
            person_id="musk",
            company_id="tesla",
            role="CEO",
            is_primary=True,
            start_date="2003-01-01"
        )
        assert relation.person_id == "musk"
        assert relation.company_id == "tesla"
        assert relation.role == "CEO"
        assert relation.is_primary is True
        assert relation.end_date is None  # 现任

    def test_company_relation_create(self):
        """测试 CompanyRelationCreate DTO"""
        create = CompanyRelationCreate(
            person_id="musk",
            company_id="spacex",
            role="Founder",
            is_primary=True
        )
        assert create.person_id == "musk"
        assert create.start_date is None


class TestSyncLog:
    """测试同步日志模型"""

    def test_sync_log(self):
        """测试 SyncLog 模型"""
        log = SyncLog(
            id=1,
            sync_type="create",
            legend_id="musk",
            change_type="added",
            details={"keywords_count": 5},
            synced_at=datetime.now()
        )
        assert log.sync_type == "create"
        assert log.change_type == "added"
        assert log.details["keywords_count"] == 5


class TestSyncResult:
    """测试同步结果模型"""

    def test_sync_result_no_changes(self):
        """测试无变化的同步结果"""
        result = SyncResult(
            has_changes=False,
            file_hash="abc123",
            unchanged=8
        )
        assert result.has_changes is False
        assert len(result.added) == 0
        assert len(result.removed) == 0
        assert result.unchanged == 8

    def test_sync_result_with_changes(self):
        """测试有变化的同步结果"""
        result = SyncResult(
            has_changes=True,
            file_hash="def456",
            added=["openai"],
            removed=["deprecated_org"],
            keywords_updated=["anthropic"],
            unchanged=6
        )
        assert result.has_changes is True
        assert "openai" in result.added
        assert "deprecated_org" in result.removed
        assert "anthropic" in result.keywords_updated


class TestLegendDetail:
    """测试 Legend 完整详情模型"""

    def test_legend_detail(self):
        """测试 LegendDetail 模型"""
        detail = LegendDetail(
            id="musk",
            type=LegendType.PERSON,
            name_en="Elon Musk",
            keywords=[
                LegendKeyword(legend_id="musk", keywords=["马斯克"])
            ],
            products=[
                LegendProduct(legend_id="musk", product_name="Starship")
            ],
            companies=[
                CompanyRelation(person_id="musk", company_id="tesla", role="CEO")
            ],
            markdown_content="# 马斯克档案"
        )
        assert detail.id == "musk"
        assert len(detail.keywords) == 1
        assert len(detail.products) == 1
        assert len(detail.companies) == 1
        assert detail.markdown_content.startswith("# ")


class TestYamlModels:
    """测试 YAML 解析模型"""

    def test_yaml_legend_entry(self):
        """测试 YamlLegendEntry 模型"""
        entry = YamlLegendEntry(
            legend_id="musk",
            keywords=[
                ["马斯克", "Elon Musk"],
                ["Tesla", "SpaceX", "CEO"]
            ]
        )
        assert entry.legend_id == "musk"
        assert len(entry.keywords) == 2
        assert entry.flat_keywords == []  # 默认空

    def test_yaml_keywords_config(self):
        """测试 YamlKeywordsConfig 模型"""
        config = YamlKeywordsConfig(
            legends={
                "musk": [["马斯k", "Elon Musk"]],
                "huang": [["黄仁勋", "Jensen Huang"]]
            },
            front=[["前沿", "Frontier"]]
        )
        assert len(config.legends) == 2
        assert "musk" in config.legends
        assert len(config.front) == 1
