"""LegendFileService 文件服务测试

测试 LegendFileService 的 Markdown 文件操作方法。
使用临时目录进行测试。
"""

import os
import tempfile
from pathlib import Path

import pytest

from src.models.legend import LegendType
from src.services.legend_file import LegendFileService


@pytest.fixture
def temp_dir():
    """T024: 创建临时目录用于测试"""
    temp = tempfile.mkdtemp()
    yield temp
    # 清理
    import shutil
    shutil.rmtree(temp)


@pytest.fixture
def file_service(temp_dir):
    """T024: 创建文件服务实例"""
    return LegendFileService(base_dir=temp_dir)


class TestFileServiceBasics:
    """T024: 测试文件基础操作"""

    def test_init_creates_directories(self, file_service):
        """T024: 测试初始化创建目录"""
        assert file_service.people_dir.exists()
        assert file_service.orgs_dir.exists()

    def test_file_exists_not_created(self, file_service):
        """T024: 测试检查不存在的文件"""
        assert not file_service.file_exists("test", LegendType.PERSON)
        assert not file_service.file_exists("test", LegendType.ORGANIZATION)

    def test_write_and_read_person_file(self, file_service):
        """T024: 测试写入和读取人物文件"""
        content = "# Test Person\n\nThis is a test."
        file_service.write_file("test", LegendType.PERSON, content)

        # 文件存在
        assert file_service.file_exists("test", LegendType.PERSON)

        # 读取内容
        read_content = file_service.read_file("test", LegendType.PERSON)
        assert read_content == content

    def test_write_and_read_org_file(self, file_service):
        """T024: 测试写入和读取组织文件"""
        content = "# Test Org\n\nCompany info."
        file_service.write_file("test", LegendType.ORGANIZATION, content)

        assert file_service.file_exists("test", LegendType.ORGANIZATION)

        read_content = file_service.read_file("test", LegendType.ORGANIZATION)
        assert read_content == content

    def test_read_nonexistent_file(self, file_service):
        """T024: 测试读取不存在的文件"""
        content = file_service.read_file("nonexistent", LegendType.PERSON)
        assert content is None

    def test_update_file(self, file_service):
        """T024: 测试更新文件"""
        file_service.write_file("update_test", LegendType.PERSON, "Original content")

        success = file_service.update_file("update_test", LegendType.PERSON, "Updated content")
        assert success is True

        content = file_service.read_file("update_test", LegendType.PERSON)
        assert content == "Updated content"

    def test_update_nonexistent_file(self, file_service):
        """T024: 测试更新不存在的文件"""
        success = file_service.update_file("nonexistent", LegendType.PERSON, "Content")
        assert success is False

    def test_delete_file(self, file_service):
        """T024: 测试删除文件"""
        file_service.write_file("delete_test", LegendType.PERSON, "To be deleted")
        assert file_service.file_exists("delete_test", LegendType.PERSON)

        success = file_service.delete_file("delete_test", LegendType.PERSON)
        assert success is True
        assert not file_service.file_exists("delete_test", LegendType.PERSON)

    def test_delete_nonexistent_file(self, file_service):
        """T024: 测试删除不存在的文件"""
        success = file_service.delete_file("nonexistent", LegendType.PERSON)
        assert success is False


class TestCreateFiles:
    """T024: 测试创建档案文件"""

    def test_create_person_file(self, file_service):
        """T024: 测试创建人物档案文件"""
        data = {
            "name_en": "Elon Musk",
            "name_cn": "马斯克",
            "bio_short": "Tesla CEO",
            "keywords": ["马斯克", "Elon Musk", "Tesla"]
        }

        path = file_service.create_person_file("musk", data)
        assert "musk.md" in path

        # 验证文件内容
        content = file_service.read_file("musk", LegendType.PERSON)
        assert "Elon Musk" in content
        assert "马斯克" in content
        assert "Tesla CEO" in content
        assert "马斯克" in content

    def test_create_org_file(self, file_service):
        """T024: 测试创建组织档案文件"""
        data = {
            "name_en": "Tesla",
            "name_cn": "特斯拉",
            "bio_short": "Electric Vehicle Company",
            "keywords": ["Tesla", "特斯拉", "EV"]
        }

        path = file_service.create_org_file("tesla", data)
        assert "tesla.md" in path

        content = file_service.read_file("tesla", LegendType.ORGANIZATION)
        assert "Tesla" in content
        assert "特斯拉" in content
        assert "Electric Vehicle Company" in content

    def test_list_all_people(self, file_service):
        """T024: 测试列出所有人物文件"""
        file_service.create_person_file("person1", {"name_en": "Person 1"})
        file_service.create_person_file("person2", {"name_en": "Person 2"})
        file_service.create_org_file("org1", {"name_en": "Org 1"})

        people = file_service.list_all_people()
        assert len(people) == 2
        assert "person1" in people
        assert "person2" in people
        assert "org1" not in people

    def test_list_all_orgs(self, file_service):
        """T024: 测试列出所有组织文件"""
        file_service.create_org_file("org1", {"name_en": "Org 1"})
        file_service.create_org_file("org2", {"name_en": "Org 2"})
        file_service.create_person_file("person1", {"name_en": "Person 1"})

        orgs = file_service.list_all_orgs()
        assert len(orgs) == 2
        assert "org1" in orgs
        assert "org2" in orgs
        assert "person1" not in orgs


class TestTemplateRendering:
    """T025: 测试模板渲染"""

    def test_render_person_template_basic(self, file_service):
        """T025: 测试人物模板基础渲染"""
        data = {
            "name_en": "Test Person",
            "name_cn": "测试人物",
            "bio_short": "Test bio"
        }

        content = file_service.render_person_template("test_id", data)

        # 验证标题
        assert "# 测试人物 档案" in content or "# Test Person 档案" in content

        # 验证基础信息表格
        assert "test_id" in content
        assert "Test Person" in content
        assert "测试人物" in content
        assert "Test bio" in content

        # 验证章节标题
        assert "## 人物基础信息" in content
        assert "## 家庭背景" in content
        assert "## 伟愿与理念" in content
        assert "## 公司矩阵" in content
        assert "## 核心产品/服务" in content
        assert "## 影响力" in content
        assert "## 文明级影响" in content
        assert "## 关键里程碑" in content

    def test_render_person_template_with_keywords(self, file_service):
        """T025: 测试人物模板包含关键词"""
        data = {
            "name_en": "Keyword Person",
            "name_cn": "关键词人物",
            "keywords": ["关键词1", "关键词2", "关键词3"]
        }

        content = file_service.render_person_template("kw_test", data)

        # 验证关键词在配置中
        assert "关键词1" in content
        assert "关键词2" in content
        assert "关键词3" in content

    def test_render_org_template_basic(self, file_service):
        """T025: 测试组织模板基础渲染"""
        data = {
            "name_en": "Test Org",
            "name_cn": "测试组织",
            "bio_short": "Test company bio"
        }

        content = file_service.render_org_template("org_id", data)

        # 验证标题
        assert "# 测试组织 档案" in content or "# Test Org 档案" in content

        # 验证基础信息
        assert "org_id" in content
        assert "Test Org" in content
        assert "测试组织" in content
        assert "Test company bio" in content

        # 验证组织特定章节
        assert "## 组织基础信息" in content
        assert "## 核心领袖" in content
        assert "## 商业模式" in content
        assert "## 财务信息" in content
        assert "## 股权结构" in content
        assert "## 竞争格局" in content
        assert "## 使命与理念" in content

    def test_render_org_template_with_keywords(self, file_service):
        """T025: 测试组织模板包含关键词"""
        data = {
            "name_en": "Keyword Org",
            "name_cn": "关键词公司",
            "keywords": ["公司1", "公司2", "产品A"]
        }

        content = file_service.render_org_template("kw_org", data)

        assert "公司1" in content
        assert "公司2" in content
        assert "产品A" in content

    def test_template_has_proper_structure(self, file_service):
        """T025: 测试模板结构完整性"""
        person_content = file_service.render_person_template("struct", {
            "name_en": "Struct",
            "keywords": []
        })

        # 验证 Markdown 格式
        assert person_content.startswith("#")
        assert "---" in person_content  # 分隔符

        # 验证表格语法
        assert "|" in person_content
        assert "---" in person_content


class TestFilePaths:
    """T026: 测试文件路径处理"""

    def test_person_file_path(self, file_service):
        """T026: 测试人物文件路径"""
        path = file_service._get_file_path("test_person", LegendType.PERSON)
        assert path.name == "test_person.md"
        assert "people" in str(path)

    def test_org_file_path(self, file_service):
        """T026: 测试组织文件路径"""
        path = file_service._get_file_path("test_org", LegendType.ORGANIZATION)
        assert path.name == "test_org.md"
        assert "orgs" in str(path)

    def test_file_path_is_absolute(self, file_service):
        """T026: 测试文件路径是绝对路径"""
        path = file_service._get_file_path("test", LegendType.PERSON)
        assert path.is_absolute()

    def test_list_returns_file_stems_only(self, file_service):
        """T026: 测试列表返回文件名不含扩展名"""
        file_service.create_person_file("person_a", {"name_en": "A"})
        file_service.create_person_file("person_b", {"name_en": "B"})

        people = file_service.list_all_people()
        assert "person_a.md" not in people
        assert "person_a" in people
        assert "person_b" in people
