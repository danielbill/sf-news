"""Legend 同步服务

支持从 legend.yaml 和 nova.yaml 同步 Legend 数据，并调用 AI 采集档案。
"""

import hashlib
import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from datetime import datetime
import json
import sys

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.legend import (
    Legend,
    LegendType,
    LegendTier,
    ImpactLevel,
    LegendCreate,
    SyncResult,
)
from services.legend_db import LegendDB
from services.researcher import Researcher


class LegendSyncService:
    """Legend 同步服务 - 支持 legend.yaml 和 nova.yaml 格式"""

    def __init__(
        self,
        legend_path: str = "config/legend.yaml",
        nova_path: str = "config/nova.yaml",
        db: Optional[LegendDB] = None,
        entity_type: str = "legend"  # legend | nova | front
    ):
        self.legend_path = Path(legend_path)
        self.nova_path = Path(nova_path)
        self.entity_type = entity_type
        self.db = db or LegendDB()
        self.researcher = Researcher(entity_type=entity_type)

        # 确保数据库已初始化
        self.db.init_db()

    def sync(self, auto_fetch: bool = True) -> SyncResult:
        """执行同步

        Args:
            auto_fetch: 是否自动调用 AI 采集数据（默认 True）

        Returns:
            SyncResult: 同步结果
        """
        # 根据 entity_type 选择配置文件
        if self.entity_type == "legend":
            yaml_path = self.legend_path
        elif self.entity_type == "nova":
            yaml_path = self.nova_path
        else:
            return SyncResult(
                has_changes=False,
                file_hash="",
                synced_at=datetime.now()
            )

        if not yaml_path.exists():
            print(f"配置文件不存在: {yaml_path}")
            return SyncResult(
                has_changes=False,
                file_hash="",
                synced_at=datetime.now()
            )

        # 加载 YAML
        yaml_data = self._load_yaml(yaml_path)
        if not yaml_data:
            return SyncResult(
                has_changes=False,
                file_hash="",
                synced_at=datetime.now()
            )

        # 计算文件哈希
        file_hash = self._calculate_file_hash(yaml_path)

        # 解析 Legend 数据
        # legend.yaml 格式: {people: {...}, company: {...}}
        # nova.yaml 格式: 直接是公司字典 {bytedance: {...}}
        if "people" in yaml_data or "company" in yaml_data:
            # legend.yaml 格式
            people_legends = yaml_data.get("people", {})
            company_legends = yaml_data.get("company", {})
            all_legends = {**people_legends, **company_legends}
        else:
            # nova.yaml 格式（直接公司字典）
            all_legends = yaml_data

        yaml_legend_ids = set(all_legends.keys())

        # 获取现有 Legend IDs
        existing_ids = set(self.db.get_all_legend_ids())

        # 检测变化
        added = yaml_legend_ids - existing_ids
        removed = existing_ids - yaml_legend_ids
        common = existing_ids & yaml_legend_ids

        # 检测内容变化（简化的哈希比较）
        updated = []
        for legend_id in common:
            # 检查 YAML 内容是否变化
            legend_hash = self._calculate_legend_hash(all_legends[legend_id])
            # 这里可以扩展为与数据库中的哈希比较
            # 暂时不处理更新

        # 如果没有变化，直接返回
        if not added and not removed and not updated:
            return SyncResult(
                has_changes=False,
                file_hash=file_hash,
                unchanged=len(existing_ids),
                synced_at=datetime.now()
            )

        # 执行同步操作
        added_list = []
        updated_list = []

        # 处理新增和更新的 Legends
        for legend_id in added | set(updated):
            legend_config = all_legends[legend_id]

            # 判断类型
            if "key_roles" in legend_config:
                # 公司格式（nova.yaml 或 legend.yaml/company）
                legend_type = LegendType.ORGANIZATION
            else:
                # 人物格式（legend.yaml/people）
                legend_type = LegendType.PERSON

            # 创建或更新数据库记录
            self._create_or_update_legend(legend_id, legend_config, legend_type)

            # 调用 AI 采集
            if auto_fetch:
                print(f"\n[{self.entity_type}] AI 采集 {legend_id}...")
                result = self.researcher.research_single(legend_id, legend_config)

                if result["success"]:
                    if legend_id in added:
                        added_list.append(legend_id)
                    else:
                        updated_list.append(legend_id)
                    print(f"  [OK] AI 采集完成")
                else:
                    print(f"  [X] AI 采集失败: {result.get('errors', {})}")
            else:
                if legend_id in added:
                    added_list.append(legend_id)
                else:
                    updated_list.append(legend_id)

        # 处理移除的 Legends
        removed_list = list(removed)
        for legend_id in removed:
            self._remove_legend(legend_id)

        # 记录同步日志
        self.db.log_sync(
            sync_type="manual",
            details={
                "entity_type": self.entity_type,
                "added": added_list,
                "removed": removed_list,
                "updated": updated_list,
                "file_hash": file_hash,
            }
        )

        return SyncResult(
            has_changes=True,
            file_hash=file_hash,
            added=added_list,
            removed=removed_list,
            keywords_updated=updated_list,
            unchanged=len(common) - len(updated_list),
            synced_at=datetime.now()
        )

    def _load_yaml(self, yaml_path: Path) -> Optional[Dict[str, Any]]:
        """加载 YAML 文件"""
        if not yaml_path.exists():
            return None

        with open(yaml_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def _calculate_file_hash(self, yaml_path: Path) -> str:
        """计算文件哈希值"""
        content = yaml_path.read_bytes()
        return hashlib.sha256(content).hexdigest()

    def _calculate_legend_hash(self, legend_config: Dict) -> str:
        """计算 Legend 配置的哈希值"""
        content = json.dumps(legend_config, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(content.encode()).hexdigest()

    def _create_or_update_legend(
        self,
        legend_id: str,
        legend_config: Dict,
        legend_type: LegendType
    ) -> None:
        """创建或更新 Legend"""
        # 提取名称
        name_en = legend_config.get("name_en", "")
        name_cn = legend_config.get("name_cn", "")

        # 检查是否已存在
        existing = self.db.get_legend(legend_id)

        if existing:
            # 更新
            self.db.update_legend(legend_id, {
                "name_en": name_en or existing.name_en,
                "name_cn": name_cn or existing.name_cn,
            })
        else:
            # 创建
            legend_create = LegendCreate(
                id=legend_id,
                type=legend_type,
                name_en=name_en or legend_id,
                name_cn=name_cn,
                legend_tier=LegendTier.POTENTIAL,
                impact_level=ImpactLevel.COMPANY,
            )
            self.db.create_legend(legend_create)

        # 设置关键词
        keywords = self._extract_keywords(legend_config)
        if keywords:
            keyword_groups = [
                {
                    "group_name": "main",
                    "keywords": keywords
                }
            ]
            keywords_hash = self._calculate_legend_hash(legend_config)
            self.db.set_keywords(legend_id, keyword_groups, source_hash=keywords_hash)

    def _extract_keywords(self, legend_config: Dict) -> List[str]:
        """从配置中提取关键词

        规则：
        - name_en: 提取
        - name_cn: 提取（如果有）
        - key_roles[].keywords: 展平提取
        - products[].keywords: 展平提取
        """
        keywords = []

        # 名称
        name_en = legend_config.get("name_en", "")
        name_cn = legend_config.get("name_cn", "")
        if name_en:
            keywords.append(name_en)
        if name_cn:
            keywords.append(name_cn)

        # 关键角色
        for role in legend_config.get("key_roles", []):
            keywords.extend(role.get("keywords", []))

        # 产品
        for product in legend_config.get("products", []):
            keywords.extend(product.get("keywords", []))

        # 去重
        return list(set(keywords))

    def _remove_legend(self, legend_id: str) -> None:
        """移除 Legend（软删除）"""
        self.db.delete_legend(legend_id)

    def get_yaml_legends(self) -> Dict[str, Dict]:
        """获取 YAML 中的 Legend 配置"""
        yaml_path = self.legend_path if self.entity_type == "legend" else self.nova_path

        yaml_data = self._load_yaml(yaml_path)
        if not yaml_data:
            return {}

        # legend.yaml 格式
        if "people" in yaml_data or "company" in yaml_data:
            people_legends = yaml_data.get("people", {})
            company_legends = yaml_data.get("company", {})
            return {**people_legends, **company_legends}

        # nova.yaml 格式
        return yaml_data


class NovaSyncService(LegendSyncService):
    """Nova 同步服务（超新星实体）"""

    def __init__(
        self,
        nova_path: str = "config/nova.yaml",
        db: Optional[LegendDB] = None
    ):
        super().__init__(
            legend_path="config/legend.yaml",
            nova_path=nova_path,
            db=db,
            entity_type="nova"
        )
