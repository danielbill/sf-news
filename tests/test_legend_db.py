"""LegendDB 数据库服务测试

测试 LegendDB 类的所有数据库操作方法。
使用临时数据库进行测试，避免影响生产数据。
"""

import json
import os
import tempfile
from pathlib import Path

import pytest

from src.models.legend import (
    Legend,
    LegendCreate,
    LegendUpdate,
    LegendFilters,
    LegendType,
    LegendTier,
    ImpactLevel,
    ProductStatus,
    LegendKeyword,
    LegendProduct,
    CompanyRelation,
    SyncLog,
    ProductCreate,
    CompanyRelationCreate,
)
from src.services.legend_db import LegendDB


@pytest.fixture
def temp_db():
    """T012: 创建临时数据库用于测试"""
    fd, path = tempfile.mkstemp(suffix=".sqlite")
    os.close(fd)
    db = LegendDB(db_path=path)
    db.init_db()
    yield db
    # 清理
    os.unlink(path)


@pytest.fixture
def sample_legend(temp_db):
    """T013: 创建示例 Legend 用于测试"""
    create = LegendCreate(
        id="musk",
        type=LegendType.PERSON,
        name_en="Elon Musk",
        name_cn="马斯克",
        legend_tier=LegendTier.SINGULARITY,
        impact_level=ImpactLevel.SINGULARITY,
        bio_short="Tesla CEO"
    )
    temp_db.create_legend(create)
    return temp_db.get_legend("musk")


class TestDatabaseInitialization:
    """T012: 测试数据库初始化"""

    def test_init_db_creates_all_tables(self, temp_db):
        """T012: 测试 init_db 创建所有表"""
        with temp_db.get_connection() as conn:
            # 检查 legends 表
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='legends'"
            )
            assert cursor.fetchone() is not None

            # 检查 legend_keywords 表
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='legend_keywords'"
            )
            assert cursor.fetchone() is not None

            # 检查 legend_products 表
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='legend_products'"
            )
            assert cursor.fetchone() is not None

            # 检查 legend_companies 表
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='legend_companies'"
            )
            assert cursor.fetchone() is not None

            # 检查 legend_sync_log 表
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='legend_sync_log'"
            )
            assert cursor.fetchone() is not None

    def test_init_db_creates_indexes(self, temp_db):
        """T012: 测试 init_db 创建索引"""
        with temp_db.get_connection() as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_legends_type'"
            )
            assert cursor.fetchone() is not None

            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_legend_keywords_legend_id'"
            )
            assert cursor.fetchone() is not None


class TestLegendCRUD:
    """T013: 测试 Legend CRUD 操作"""

    def test_create_legend(self, temp_db):
        """T013: 测试创建 Legend"""
        create = LegendCreate(
            id="test_person",
            type=LegendType.PERSON,
            name_en="Test Person",
            name_cn="测试人物"
        )
        legend_id = temp_db.create_legend(create)

        assert legend_id == "test_person"
        assert temp_db.legend_exists("test_person")

    def test_get_legend(self, temp_db):
        """T013: 测试获取单个 Legend"""
        create = LegendCreate(
            id="huang",
            type=LegendType.PERSON,
            name_en="Jensen Huang",
            name_cn="黄仁勋"
        )
        temp_db.create_legend(create)

        legend = temp_db.get_legend("huang")
        assert legend is not None
        assert legend.id == "huang"
        assert legend.name_en == "Jensen Huang"
        assert legend.name_cn == "黄仁勋"
        assert legend.type == LegendType.PERSON

    def test_get_legend_not_found(self, temp_db):
        """T013: 测试获取不存在的 Legend"""
        legend = temp_db.get_legend("nonexistent")
        assert legend is None

    def test_list_legends_all(self, temp_db):
        """T013: 测试列出所有 Legends"""
        # 创建多个 Legends
        for i in range(3):
            create = LegendCreate(
                id=f"legend_{i}",
                type=LegendType.ORGANIZATION,
                name_en=f"Company {i}"
            )
            temp_db.create_legend(create)

        legends = temp_db.list_legends()
        assert len(legends) == 3

    def test_list_legends_with_type_filter(self, temp_db):
        """T013: 测试按类型过滤 Legends"""
        temp_db.create_legend(LegendCreate(
            id="person1", type=LegendType.PERSON, name_en="Person 1"
        ))
        temp_db.create_legend(LegendCreate(
            id="org1", type=LegendType.ORGANIZATION, name_en="Org 1"
        ))

        filters = LegendFilters(type=LegendType.PERSON)
        legends = temp_db.list_legends(filters)
        assert len(legends) == 1
        assert legends[0].type == LegendType.PERSON

    def test_list_legends_with_tier_filter(self, temp_db):
        """T013: 测试按等级过滤 Legends"""
        temp_db.create_legend(LegendCreate(
            id="singularity", type=LegendType.PERSON,
            name_en="S", legend_tier=LegendTier.SINGULARITY
        ))
        temp_db.create_legend(LegendCreate(
            id="potential", type=LegendType.PERSON,
            name_en="P", legend_tier=LegendTier.POTENTIAL
        ))

        filters = LegendFilters(tier=LegendTier.SINGULARITY)
        legends = temp_db.list_legends(filters)
        assert len(legends) == 1
        assert legends[0].legend_tier == LegendTier.SINGULARITY

    def test_list_legends_with_limit_and_offset(self, temp_db):
        """T013: 测试分页查询"""
        for i in range(5):
            temp_db.create_legend(LegendCreate(
                id=f"legend_{i}", type=LegendType.PERSON, name_en=f"Legend {i}"
            ))

        filters = LegendFilters(limit=2, offset=1)
        legends = temp_db.list_legends(filters)
        assert len(legends) == 2

    def test_update_legend(self, temp_db):
        """T013: 测试更新 Legend"""
        create = LegendCreate(
            id="update_test",
            type=LegendType.PERSON,
            name_en="Original Name",
            bio_short="Original bio"
        )
        temp_db.create_legend(create)

        update = LegendUpdate(
            name_en="Updated Name",
            bio_short="Updated bio",
            legend_tier=LegendTier.QUASI
        )
        success = temp_db.update_legend("update_test", update)

        assert success is True
        legend = temp_db.get_legend("update_test")
        assert legend.name_en == "Updated Name"
        assert legend.bio_short == "Updated bio"
        assert legend.legend_tier == LegendTier.QUASI

    def test_update_legend_no_fields(self, temp_db):
        """T013: 测试无字段更新"""
        create = LegendCreate(
            id="no_update", type=LegendType.PERSON, name_en="Test"
        )
        temp_db.create_legend(create)

        update = LegendUpdate()  # 空更新
        success = temp_db.update_legend("no_update", update)
        assert success is False

    def test_update_legend_not_found(self, temp_db):
        """T013: 测试更新不存在的 Legend"""
        update = LegendUpdate(name_en="New Name")
        success = temp_db.update_legend("nonexistent", update)
        assert success is False

    def test_delete_legend(self, temp_db):
        """T013: 测试删除 Legend"""
        create = LegendCreate(
            id="to_delete", type=LegendType.PERSON, name_en="Delete Me"
        )
        temp_db.create_legend(create)

        success = temp_db.delete_legend("to_delete")
        assert success is True
        assert temp_db.legend_exists("to_delete") is False

    def test_delete_legend_not_found(self, temp_db):
        """T013: 测试删除不存在的 Legend"""
        success = temp_db.delete_legend("nonexistent")
        assert success is False

    def test_legend_exists(self, temp_db):
        """T013: 测试检查 Legend 是否存在"""
        create = LegendCreate(
            id="exists_test", type=LegendType.PERSON, name_en="Exists"
        )
        temp_db.create_legend(create)

        assert temp_db.legend_exists("exists_test") is True
        assert temp_db.legend_exists("not_exists") is False


class TestKeywordsOperations:
    """T014: 测试 Keywords 操作"""

    def test_set_keywords(self, temp_db):
        """T014: 测试设置关键词"""
        # 先创建 Legend
        create = LegendCreate(
            id="keywords_test", type=LegendType.PERSON, name_en="Test"
        )
        temp_db.create_legend(create)

        # 设置关键词
        keywords = [
            {"group_name": "names", "keywords": ["马斯克", "Elon Musk"]},
            {"group_name": "companies", "keywords": ["Tesla", "SpaceX"]}
        ]
        temp_db.set_keywords("keywords_test", keywords, source_hash="abc123")

        # 验证
        saved_keywords = temp_db.get_keywords("keywords_test")
        assert len(saved_keywords) == 2
        assert saved_keywords[0].keyword_group == "names"
        assert saved_keywords[0].keywords == ["马斯克", "Elon Musk"]
        assert saved_keywords[1].keywords == ["Tesla", "SpaceX"]

    def test_set_keywords_replaces_existing(self, temp_db):
        """T014: 测试设置关键词替换现有关键词"""
        create = LegendCreate(
            id="replace_kw", type=LegendType.PERSON, name_en="Test"
        )
        temp_db.create_legend(create)

        # 第一次设置
        temp_db.set_keywords("replace_kw", [
            {"group_name": "old", "keywords": ["old1", "old2"]}
        ])
        assert len(temp_db.get_keywords("replace_kw")) == 1

        # 第二次设置（替换）
        temp_db.set_keywords("replace_kw", [
            {"group_name": "new", "keywords": ["new1"]},
            {"group_name": "new2", "keywords": ["new2"]}
        ])
        saved = temp_db.get_keywords("replace_kw")
        assert len(saved) == 2
        assert saved[0].keyword_group == "new"

    def test_get_keywords_empty(self, temp_db):
        """T014: 测试获取空关键词列表"""
        create = LegendCreate(
            id="no_keywords", type=LegendType.PERSON, name_en="Test"
        )
        temp_db.create_legend(create)

        keywords = temp_db.get_keywords("no_keywords")
        assert len(keywords) == 0

    def test_keywords_changed_new(self, temp_db):
        """T014: 测试关键词变化检测 - 新关键词"""
        create = LegendCreate(
            id="new_kw", type=LegendType.PERSON, name_en="Test"
        )
        temp_db.create_legend(create)

        # 从未有关键词
        changed = temp_db.keywords_changed(
            "new_kw", ["test1", "test2"], "hash123"
        )
        assert changed is True

    def test_keywords_changed_same(self, temp_db):
        """T014: 测试关键词变化检测 - 无变化"""
        create = LegendCreate(
            id="same_kw", type=LegendType.PERSON, name_en="Test"
        )
        temp_db.create_legend(create)

        temp_db.set_keywords("same_kw", [
            {"keywords": ["test1", "test2"]}
        ], source_hash="hash123")

        # 相同哈希
        changed = temp_db.keywords_changed(
            "same_kw", ["test1", "test2"], "hash123"
        )
        assert changed is False

    def test_keywords_changed_different(self, temp_db):
        """T014: 测试关键词变化检测 - 有变化"""
        create = LegendCreate(
            id="diff_kw", type=LegendType.PERSON, name_en="Test"
        )
        temp_db.create_legend(create)

        temp_db.set_keywords("diff_kw", [
            {"keywords": ["old1", "old2"]}
        ], source_hash="old_hash")

        # 不同哈希
        changed = temp_db.keywords_changed(
            "diff_kw", ["new1", "new2"], "new_hash"
        )
        assert changed is True


class TestProductsOperations:
    """T015: 测试 Products 操作"""

    def test_add_product(self, temp_db):
        """T015: 测试添加产品"""
        create = LegendCreate(
            id="spacex", type=LegendType.ORGANIZATION, name_en="SpaceX"
        )
        temp_db.create_legend(create)

        product = ProductCreate(
            legend_id="spacex",
            product_name="Starship",
            description="Reusable rocket",
            status=ProductStatus.ACTIVE,
            category="Spacecraft"
        )

        product_id = temp_db.add_product(product)
        assert product_id > 0

        products = temp_db.list_products("spacex")
        assert len(products) == 1
        assert products[0].product_name == "Starship"
        assert products[0].category == "Spacecraft"

    def test_list_products_empty(self, temp_db):
        """T015: 测试获取空产品列表"""
        create = LegendCreate(
            id="no_products", type=LegendType.ORGANIZATION, name_en="No Products"
        )
        temp_db.create_legend(create)

        products = temp_db.list_products("no_products")
        assert len(products) == 0

    def test_list_products_multiple(self, temp_db):
        """T015: 测试获取多个产品"""
        create = LegendCreate(
            id="tesla", type=LegendType.ORGANIZATION, name_en="Tesla"
        )
        temp_db.create_legend(create)

        # 添加多个产品
        for name in ["Model S", "Model 3", "Model X"]:
            temp_db.add_product(ProductCreate(
                legend_id="tesla",
                product_name=name,
                category="Vehicle"
            ))

        products = temp_db.list_products("tesla")
        assert len(products) == 3
        product_names = [p.product_name for p in products]
        assert "Model S" in product_names
        assert "Model 3" in product_names
        assert "Model X" in product_names


class TestCompaniesRelation:
    """T016: 测试人物-公司关联操作"""

    def test_add_company_relation(self, temp_db):
        """T016: 测试添加人物-公司关联"""
        # 创建人物和公司
        temp_db.create_legend(LegendCreate(
            id="person1", type=LegendType.PERSON, name_en="Person"
        ))
        temp_db.create_legend(LegendCreate(
            id="company1", type=LegendType.ORGANIZATION, name_en="Company"
        ))

        relation = CompanyRelationCreate(
            person_id="person1",
            company_id="company1",
            role="CEO",
            is_primary=True,
            start_date="2020-01-01"
        )

        relation_id = temp_db.add_company_relation(relation)
        assert relation_id > 0

    def test_list_person_companies(self, temp_db):
        """T016: 测试获取人物关联的公司列表"""
        temp_db.create_legend(LegendCreate(
            id="musk", type=LegendType.PERSON, name_en="Elon"
        ))
        temp_db.create_legend(LegendCreate(
            id="tesla", type=LegendType.ORGANIZATION, name_en="Tesla"
        ))
        temp_db.create_legend(LegendCreate(
            id="spacex", type=LegendType.ORGANIZATION, name_en="SpaceX"
        ))

        # 添加关联
        temp_db.add_company_relation(CompanyRelationCreate(
            person_id="musk", company_id="spacex", role="Founder", is_primary=True
        ))
        temp_db.add_company_relation(CompanyRelationCreate(
            person_id="musk", company_id="tesla", role="CEO", is_primary=False
        ))

        companies = temp_db.list_person_companies("musk")
        assert len(companies) == 2
        # is_primary=True 的应该排在前面
        assert companies[0].company_id == "spacex"
        assert companies[0].is_primary is True
        assert companies[1].company_id == "tesla"
        assert companies[1].is_primary is False

    def test_list_company_people(self, temp_db):
        """T016: 测试获取公司关联的人物列表"""
        temp_db.create_legend(LegendCreate(
            id="company", type=LegendType.ORGANIZATION, name_en="Company"
        ))
        temp_db.create_legend(LegendCreate(
            id="person1", type=LegendType.PERSON, name_en="Person 1"
        ))
        temp_db.create_legend(LegendCreate(
            id="person2", type=LegendType.PERSON, name_en="Person 2"
        ))

        temp_db.add_company_relation(CompanyRelationCreate(
            person_id="person1", company_id="company", role="CEO", is_primary=True
        ))
        temp_db.add_company_relation(CompanyRelationCreate(
            person_id="person2", company_id="company", role="CTO", is_primary=False
        ))

        people = temp_db.list_company_people("company")
        assert len(people) == 2
        person_ids = [p.person_id for p in people]
        assert "person1" in person_ids
        assert "person2" in person_ids

    def test_list_person_companies_empty(self, temp_db):
        """T016: 测试获取空关联列表"""
        temp_db.create_legend(LegendCreate(
            id="lonely", type=LegendType.PERSON, name_en="Lonely"
        ))

        companies = temp_db.list_person_companies("lonely")
        assert len(companies) == 0


class TestSyncLog:
    """T017: 测试 Sync Log 操作"""

    def test_log_sync(self, temp_db):
        """T017: 测试记录同步日志"""
        temp_db.log_sync(
            sync_type="create",
            legend_id="test",
            change_type="added",
            details={"keywords_count": 5}
        )

        logs = temp_db.get_sync_logs(limit=10)
        assert len(logs) == 1
        assert logs[0].sync_type == "create"
        assert logs[0].legend_id == "test"
        assert logs[0].change_type == "added"
        assert logs[0].details["keywords_count"] == 5

    def test_get_sync_logs_limit(self, temp_db):
        """T017: 测试获取同步日志数量限制"""
        # 记录多条日志
        for i in range(10):
            temp_db.log_sync(
                sync_type="test",
                details={"index": i}
            )

        logs = temp_db.get_sync_logs(limit=5)
        assert len(logs) == 5

    def test_get_sync_logs_order(self, temp_db):
        """T017: 测试同步日志按时间倒序"""
        for i in range(3):
            temp_db.log_sync(sync_type=f"test_{i}")

        logs = temp_db.get_sync_logs()
        # 最新的在前
        assert logs[0].sync_type == "test_2"
        assert logs[1].sync_type == "test_1"
        assert logs[2].sync_type == "test_0"

    def test_log_sync_minimal(self, temp_db):
        """T017: 测试记录最小同步日志"""
        temp_db.log_sync(sync_type="scan")

        logs = temp_db.get_sync_logs()
        assert len(logs) == 1
        assert logs[0].sync_type == "scan"
        assert logs[0].legend_id is None
        assert logs[0].change_type is None
        assert logs[0].details is None


class TestBatchOperations:
    """测试批量操作"""

    def test_get_all_legend_ids(self, temp_db):
        """测试获取所有 Legend ID"""
        ids = ["a", "b", "c"]
        for legend_id in ids:
            temp_db.create_legend(LegendCreate(
                id=legend_id, type=LegendType.PERSON, name_en=legend_id
            ))

        result = temp_db.get_all_legend_ids()
        assert set(result) == set(ids)

    def test_get_all_legend_ids_empty(self, temp_db):
        """测试获取空 ID 列表"""
        result = temp_db.get_all_legend_ids()
        assert result == []

    def test_get_file_hash(self, temp_db):
        """测试获取关键词哈希值"""
        temp_db.create_legend(LegendCreate(
            id="hash_test", type=LegendType.PERSON, name_en="Test"
        ))
        temp_db.set_keywords("hash_test", [
            {"keywords": ["test"]}
        ], source_hash="stored_hash")

        hash_value = temp_db.get_file_hash("hash_test")
        assert hash_value == "stored_hash"

    def test_get_file_hash_not_found(self, temp_db):
        """测试获取不存在的哈希值"""
        temp_db.create_legend(LegendCreate(
            id="no_hash", type=LegendType.PERSON, name_en="Test"
        ))

        hash_value = temp_db.get_file_hash("no_hash")
        assert hash_value is None
