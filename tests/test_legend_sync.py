"""LegendSyncService 同步服务测试

测试 LegendSyncService 从 YAML 同步到数据库的逻辑。
"""

import json
import os
import tempfile
from pathlib import Path

import pytest
from unittest.mock import Mock, patch

from src.models.legend import (
    LegendType,
    LegendTier,
    ImpactLevel,
    SyncResult,
)
from src.services.legend_db import LegendDB
from src.services.legend_file import LegendFileService
from src.services.legend_sync import LegendSyncService


@pytest.fixture
def yaml_content():
    """T032: 测试 YAML 内容 - 必须是严格的列表的列表格式"""
    return """
legend:
  musk:
    - - 马斯克
      - Elon Musk
    - - Tesla
    - - SpaceX
  huang:
    - - 黄仁勋
    - - Jensen Huang
    - - NVIDIA
  google:
    - - Google
    - - 谷歌
  microsoft:
    - - Microsoft
    - - 微软

front:
  - - 前沿
  - - Frontier
"""


@pytest.fixture
def temp_yaml_file(yaml_content):
    """T032: 创建临时 YAML 文件"""
    fd, path = tempfile.mkstemp(suffix=".yaml")
    os.close(fd)
    Path(path).write_text(yaml_content, encoding="utf-8")
    yield path
    os.unlink(path)


@pytest.fixture
def temp_db():
    """创建临时数据库"""
    fd, path = tempfile.mkstemp(suffix=".sqlite")
    os.close(fd)
    db = LegendDB(db_path=path)
    db.init_db()
    yield db
    os.unlink(path)


@pytest.fixture
def temp_file_service():
    """创建临时文件服务"""
    temp_dir = tempfile.mkdtemp()
    service = LegendFileService(base_dir=temp_dir)
    yield service
    import shutil
    shutil.rmtree(temp_dir)


@pytest.fixture
def sync_service(temp_yaml_file, temp_db, temp_file_service):
    """T032: 创建同步服务实例"""
    return LegendSyncService(
        keywords_path=temp_yaml_file,
        db=temp_db,
        file_service=temp_file_service
    )


class TestYamlParsing:
    """T032: 测试 YAML 解析"""

    def test_load_yaml_success(self, sync_service):
        """T032: 测试成功加载 YAML"""
        data = sync_service._load_yaml()
        assert data is not None
        assert "legend" in data
        assert "front" in data

    def test_load_yaml_structure(self, sync_service):
        """T032: 测试 YAML 结构"""
        data = sync_service._load_yaml()
        legends = data.get("legend", {})

        assert "musk" in legends
        assert "huang" in legends
        assert "google" in legends
        assert "microsoft" in legends

        # 验证关键词是列表的列表
        assert isinstance(legends["musk"], list)
        assert len(legends["musk"]) >= 2

    def test_load_yaml_front_keywords(self, sync_service):
        """T032: 测试 front 关键词"""
        data = sync_service._load_yaml()
        front = data.get("front", [])
        assert len(front) > 0
        # front 是列表的列表
        assert "前沿" in front[0] or "Frontier" in front[1]

    def test_calculate_file_hash(self, sync_service):
        """T032: 测试计算文件哈希"""
        hash1 = sync_service._calculate_file_hash()
        assert isinstance(hash1, str)
        assert len(hash1) == 64  # SHA256 = 64 hex chars

        # 再次计算应该相同
        hash2 = sync_service._calculate_file_hash()
        assert hash1 == hash2


class TestTypeInference:
    """T033: 测试类型推断"""

    def test_infer_person_by_known_id(self, sync_service):
        """T033: 测试通过已知 ID 推断人物"""
        keywords = [["some", "keywords"]]
        assert sync_service._infer_legend_type("musk", keywords) == LegendType.PERSON
        assert sync_service._infer_legend_type("huang", keywords) == LegendType.PERSON
        assert sync_service._infer_legend_type("altman", keywords) == LegendType.PERSON

    def test_infer_org_by_known_id(self, sync_service):
        """T033: 测试通过已知 ID 推断组织"""
        keywords = [["some", "keywords"]]
        assert sync_service._infer_legend_type("google", keywords) == LegendType.ORGANIZATION
        assert sync_service._infer_legend_type("Microsoft", keywords) == LegendType.ORGANIZATION
        assert sync_service._infer_legend_type("alibaba", keywords) == LegendType.ORGANIZATION
        assert sync_service._infer_legend_type("huawei", keywords) == LegendType.ORGANIZATION
        assert sync_service._infer_legend_type("anthropic", keywords) == LegendType.ORGANIZATION

    def test_infer_person_by_keywords(self, sync_service):
        """T033: 测试通过关键词推断人物"""
        # 包含职位词
        assert sync_service._infer_legend_type("unknown", [
            ["Test Person", "CEO", "Founder"]
        ]) == LegendType.PERSON

        # 包含中文名
        assert sync_service._infer_legend_type("unknown", [
            ["马斯克", "埃隆"]
        ]) == LegendType.PERSON

        # 包含英文职位
        assert sync_service._infer_legend_type("unknown", [
            ["Sam", "CEO", "CTO"]
        ]) == LegendType.PERSON

    def test_infer_org_by_keywords(self, sync_service):
        """T033: 测试通过关键词推断组织"""
        # 包含公司后缀
        assert sync_service._infer_legend_type("unknown", [
            ["Test Corporation", "Inc"]
        ]) == LegendType.ORGANIZATION

        # 包含中文公司词
        assert sync_service._infer_legend_type("unknown", [
            ["测试公司", "科技集团"]
        ]) == LegendType.ORGANIZATION

    def test_infer_default_org(self, sync_service):
        """T033: 测试默认推断为组织"""
        # 无明确标识，默认为组织
        assert sync_service._infer_legend_type("unknown", [
            ["Random", "Keywords"]
        ]) == LegendType.ORGANIZATION


class TestNameExtraction:
    """T034: 测试名称提取"""

    def test_extract_names_both(self, sync_service):
        """T034: 测试提取中英文名"""
        keywords = [
            ["Elon Musk", "马斯克"],
            ["Tesla", "SpaceX"]
        ]
        name_en, name_cn = sync_service._extract_names(keywords)
        assert name_en == "Elon Musk"
        assert name_cn == "马斯克"

    def test_extract_names_only_english(self, sync_service):
        """T034: 测试仅英文名"""
        keywords = [
            ["NVIDIA", "Jensen Huang"],
            ["GPU", "AI"]
        ]
        name_en, name_cn = sync_service._extract_names(keywords)
        assert name_en == "NVIDIA"
        assert name_cn == ""

    def test_extract_names_only_chinese(self, sync_service):
        """T034: 测试仅中文名"""
        keywords = [
            ["华为技术有限公司"],
            ["任正非"]
        ]
        name_en, name_cn = sync_service._extract_names(keywords)
        assert name_en == ""
        assert name_cn == "华为技术有限公司"

    def test_extract_names_empty(self, sync_service):
        """T034: 测试空关键词"""
        name_en, name_cn = sync_service._extract_names([])
        assert name_en == ""
        assert name_cn == ""


class TestKeywordProcessing:
    """T035: 测试关键词处理"""

    def test_flatten_keywords(self, sync_service):
        """T035: 测试展平关键词"""
        keywords = [
            ["a", "b"],
            ["c"],
            ["d", "e", "f"]
        ]
        flat = sync_service._flatten_keywords(keywords)
        assert flat == ["a", "b", "c", "d", "e", "f"]

    def test_flatten_keywords_single_item(self, sync_service):
        """T035: 测试展平单组关键词"""
        keywords = [["only", "group"]]
        flat = sync_service._flatten_keywords(keywords)
        assert flat == ["only", "group"]

    def test_flatten_keywords_empty(self, sync_service):
        """T035: 测试展平空关键词"""
        flat = sync_service._flatten_keywords([])
        assert flat == []

    def test_calculate_keywords_hash(self, sync_service):
        """T035: 测试计算关键词哈希"""
        keywords1 = ["a", "b", "c"]
        keywords2 = ["a", "b", "c"]
        keywords3 = ["a", "b", "d"]

        hash1 = sync_service._calculate_keywords_hash(keywords1)
        hash2 = sync_service._calculate_keywords_hash(keywords2)
        hash3 = sync_service._calculate_keywords_hash(keywords3)

        assert hash1 == hash2  # 相同内容，相同哈希
        assert hash1 != hash3  # 不同内容，不同哈希


class TestSyncFlow:
    """T036: 测试同步流程"""

    def test_sync_new_legends(self, sync_service, temp_db):
        """T036: 测试同步新增 Legends"""
        result = sync_service.sync(auto_fetch=False)

        assert result.has_changes is True
        assert len(result.added) > 0
        assert "musk" in result.added or "Musk" in result.added

        # 验证数据库中存在
        ids = temp_db.get_all_legend_ids()
        assert len(ids) > 0

    def test_sync_no_changes(self, sync_service, temp_db):
        """T036: 测试无变化时不更新"""
        # 第一次同步
        result1 = sync_service.sync(auto_fetch=False)
        assert result1.has_changes is True

        # 第二次同步（无变化）
        result2 = sync_service.sync(auto_fetch=False)
        assert result2.has_changes is False
        assert result2.unchanged > 0

    def test_sync_creates_markdown_files(self, sync_service):
        """T036: 测试同步创建 Markdown 文件"""
        sync_service.sync(auto_fetch=False)

        # 检查人物文件
        people = sync_service.file_service.list_all_people()
        assert len(people) > 0

        # 检查组织文件
        orgs = sync_service.file_service.list_all_orgs()
        assert len(orgs) > 0

    def test_get_yaml_legends(self, sync_service):
        """T036: 测试获取 YAML 配置"""
        config = sync_service.get_yaml_legends()

        assert config.legends is not None
        assert len(config.legends) > 0
        assert config.front is not None
        assert len(config.front) > 0

    def test_sync_records_logs(self, sync_service, temp_db):
        """T036: 测试同步记录日志"""
        sync_service.sync(auto_fetch=False)

        logs = temp_db.get_sync_logs(limit=100)
        assert len(logs) > 0

        # 验证日志类型
        sync_types = [log.sync_type for log in logs]
        assert "create" in sync_types

    def test_result_structure(self, sync_service):
        """T036: 测试同步结果结构"""
        result = sync_service.sync(auto_fetch=False)

        assert isinstance(result, SyncResult)
        assert isinstance(result.has_changes, bool)
        assert isinstance(result.file_hash, str)
        assert isinstance(result.added, list)
        assert isinstance(result.removed, list)
        assert isinstance(result.keywords_updated, list)
        assert isinstance(result.unchanged, int)
        assert result.synced_at is not None


class TestSyncEdgeCases:
    """测试同步边界情况"""

    def test_sync_with_removed_legend(self, sync_service, temp_db):
        """测试移除 Legend"""
        # 先同步
        sync_service.sync(auto_fetch=False)
        assert len(temp_db.get_all_legend_ids()) > 0

        # 修改 YAML 移除一个 Legend（通过修改服务中的 YAML 内容）
        # 这里简化测试：直接删除数据库记录再同步
        temp_db.delete_legend("musk")
        ids_before = temp_db.get_all_legend_ids()

        # 再次同步
        result = sync_service.sync(auto_fetch=False)
        # 移除的 Legend 不应该在结果中（因为 YAML 中仍然存在）
        assert "musk" not in result.removed

    def test_sync_with_empty_yaml(self, temp_db, temp_file_service):
        """测试空 YAML 文件"""
        # 创建空 YAML
        fd, path = tempfile.mkstemp(suffix=".yaml")
        os.close(fd)
        Path(path).write_text("legend: {}\nfront: []\n", encoding="utf-8")

        service = LegendSyncService(
            keywords_path=path,
            db=temp_db,
            file_service=temp_file_service
        )

        result = service.sync(auto_fetch=False)
        assert result.unchanged == 0
        assert len(result.added) == 0

        os.unlink(path)

    def test_infer_case_insensitive(self, sync_service):
        """测试 ID 大小写不敏感"""
        # 大小写变体应该识别为同一类型
        assert sync_service._infer_legend_type("MUSK", []) == LegendType.PERSON
        assert sync_service._infer_legend_type("MUSK", []) == LegendType.PERSON
        assert sync_service._infer_legend_type("GOOGLE", []) == LegendType.ORGANIZATION
        assert sync_service._infer_legend_type("MiCrOsOfT", []) == LegendType.ORGANIZATION
