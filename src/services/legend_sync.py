"""Legend 同步服务

从 news_keywords.yaml 同步 Legend 数据到数据库和 Markdown 文件。
"""

import hashlib
import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from datetime import datetime
import json

from ..models.legend import (
    Legend,
    LegendType,
    LegendTier,
    ImpactLevel,
    LegendCreate,
    YamlKeywordsConfig,
    YamlLegendEntry,
    SyncResult,
)
from ..services.legend_db import LegendDB
from ..services.legend_file import LegendFileService


class LegendSyncService:
    """Legend 同步服务 - 核心同步逻辑"""

    def __init__(
        self,
        keywords_path: str = "config/news_keywords.yaml",
        db: Optional[LegendDB] = None,
        file_service: Optional[LegendFileService] = None
    ):
        self.keywords_path = Path(keywords_path)
        self.db = db or LegendDB()
        self.file_service = file_service or LegendFileService()

        # 确保数据库已初始化
        self.db.init_db()

    def sync(self, auto_fetch: bool = False) -> SyncResult:
        """执行同步

        Args:
            auto_fetch: 是否自动调用 /baidu-ai-search 采集数据

        Returns:
            SyncResult: 同步结果
        """
        # 1. 读取 YAML 文件
        yaml_data = self._load_yaml()
        if not yaml_data:
            return SyncResult(
                has_changes=False,
                file_hash="",
                synced_at=datetime.now()
            )

        # 2. 计算文件哈希
        file_hash = self._calculate_file_hash()

        # 3. 解析 Legend 定义
        yaml_legends = yaml_data.get("legend", {})
        yaml_legend_ids = set(yaml_legends.keys())

        # 4. 获取现有 Legend IDs
        existing_ids = set(self.db.get_all_legend_ids())

        # 5. 检测变化
        added = yaml_legend_ids - existing_ids
        removed = existing_ids - yaml_legend_ids
        common = existing_ids & yaml_legend_ids

        # 6. 检测关键词变化
        keywords_updated = []
        for legend_id in common:
            keywords_list = yaml_legends[legend_id]
            flat_keywords = self._flatten_keywords(keywords_list)
            new_hash = self._calculate_keywords_hash(flat_keywords)

            if self.db.keywords_changed(legend_id, flat_keywords, new_hash):
                keywords_updated.append(legend_id)

        # 7. 如果没有变化，直接返回
        if not added and not removed and not keywords_updated:
            return SyncResult(
                has_changes=False,
                file_hash=file_hash,
                unchanged=len(existing_ids),
                synced_at=datetime.now()
            )

        # 8. 执行同步操作
        # 8.1 新增 Legends
        for legend_id in added:
            self._create_legend_from_yaml(legend_id, yaml_legends[legend_id])

        # 8.2 更新关键词变化的 Legends
        for legend_id in keywords_updated:
            self._update_keywords(legend_id, yaml_legends[legend_id])

        # 8.3 移除 Legends（标记归档）
        for legend_id in removed:
            self._remove_legend(legend_id)

        # 9. 记录同步日志
        self.db.log_sync(
            sync_type="manual",
            details={
                "added": list(added),
                "removed": list(removed),
                "keywords_updated": keywords_updated,
                "file_hash": file_hash,
            }
        )

        return SyncResult(
            has_changes=True,
            file_hash=file_hash,
            added=list(added),
            removed=list(removed),
            keywords_updated=keywords_updated,
            unchanged=len(common) - len(keywords_updated),
            synced_at=datetime.now()
        )

    def _load_yaml(self) -> Optional[Dict[str, Any]]:
        """加载 YAML 文件"""
        if not self.keywords_path.exists():
            return None

        with open(self.keywords_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def _calculate_file_hash(self) -> str:
        """计算文件哈希值"""
        content = self.keywords_path.read_bytes()
        return hashlib.sha256(content).hexdigest()

    def _calculate_keywords_hash(self, keywords: List[str]) -> str:
        """计算关键词哈希值"""
        content = json.dumps(keywords, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(content.encode()).hexdigest()

    def _flatten_keywords(self, keywords: List[List[str]]) -> List[str]:
        """展平关键词数组"""
        result = []
        for group in keywords:
            if isinstance(group, list):
                result.extend(group)
            else:
                result.append(str(group))
        return result

    def _infer_legend_type(self, legend_id: str, keywords: List[List[str]]) -> LegendType:
        """推断 Legend 类型 (PERSON | ORGANIZATION)

        规则:
        - 如果关键词包含 "创始人"、"CEO"、"董事长" 等职位词 → PERSON
        - 如果关键词包含公司典型词汇（股票代码模式、纯大写公司名）→ ORGANIZATION
        - 默认 ORGANIZATION

        从 news_keywords.yaml 的实际数据来看：
        - musk: 人物（有"马斯克"）
        - huang: 人物（有"黄仁勋"）
        - altman: 人物（有"奥尔特曼"）
        - anthropic: 组织（公司名，含人物名但主要是公司）
        - google: 组织
        - Microsoft: 组织
        - alibaba: 组织
        - huawei: 组织
        """
        # 优先：已知组织 ID（大小写不敏感）
        known_orgs = {"google", "microsoft", "alibaba", "huawei", "anthropic"}
        if legend_id.lower() in known_orgs:
            return LegendType.ORGANIZATION

        # 优先：已知人物 ID
        known_people = {"musk", "huang", "altman"}
        if legend_id.lower() in known_people:
            return LegendType.PERSON

        flat_keywords = self._flatten_keywords(keywords)
        keywords_str = " ".join(flat_keywords).lower()

        # 人物关键词（职位 + 姓名）
        person_indicators = [
            "创始人", "ceo", "cto", "董事长", "总裁",
            "马斯克", "黄仁勋", "奥尔特曼", "比尔·盖茨", "马云", "任正非",
            "埃隆", "jensen", "sam", "拉里", "谢尔盖", "桑达尔"
        ]

        # 组织关键词
        org_indicators = [
            "corporation", "inc", "ltd", "llc", "co.",
            "公司", "集团", "科技", "智能"
        ]

        # 检查人物指标
        for indicator in person_indicators:
            if indicator.lower() in keywords_str:
                return LegendType.PERSON

        # 检查组织指标
        for indicator in org_indicators:
            if indicator.lower() in keywords_str:
                return LegendType.ORGANIZATION

        # 默认：组织
        return LegendType.ORGANIZATION

    def _extract_names(self, keywords: List[List[str]]) -> tuple[str, str]:
        """从关键词中提取英文名和中文名

        Returns:
            (name_en, name_cn)
        """
        flat_keywords = self._flatten_keywords(keywords)

        name_en = ""
        name_cn = ""

        for kw in flat_keywords:
            # 纯英文 -> 英文名
            if kw.encode("ascii", "ignore").decode() == kw and kw[0].isupper():
                if not name_en:
                    name_en = kw
            # 包含中文 -> 中文名
            elif any("\u4e00" <= c <= "\u9fff" for c in kw):
                if not name_cn:
                    name_cn = kw

        return name_en, name_cn

    def _create_legend_from_yaml(
        self,
        legend_id: str,
        keywords: List[List[str]]
    ) -> None:
        """从 YAML 创建 Legend"""
        # 推断类型
        legend_type = self._infer_legend_type(legend_id, keywords)

        # 提取名称
        name_en, name_cn = self._extract_names(keywords)

        # 创建数据库记录
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
        flat_keywords = self._flatten_keywords(keywords)
        keywords_hash = self._calculate_keywords_hash(flat_keywords)

        # 构建关键词组（保留原始分组）
        keyword_groups = []
        for i, group in enumerate(keywords):
            keyword_groups.append({
                "group_name": f"group_{i}",
                "keywords": group if isinstance(group, list) else [group]
            })

        self.db.set_keywords(
            legend_id,
            keyword_groups,
            source_hash=keywords_hash
        )

        # 创建 Markdown 文件
        if legend_type == LegendType.PERSON:
            self.file_service.create_person_file(legend_id, {
                "name_en": name_en,
                "name_cn": name_cn,
                "bio_short": f"{name_cn or name_en} 的档案",
                "keywords": flat_keywords,
            })
        else:
            self.file_service.create_org_file(legend_id, {
                "name_en": name_en,
                "name_cn": name_cn,
                "bio_short": f"{name_cn or name_en} 的档案",
                "keywords": flat_keywords,
            })

        # 记录日志
        self.db.log_sync(
            sync_type="create",
            legend_id=legend_id,
            change_type="added",
            details={"keywords_count": len(flat_keywords)}
        )

    def _update_keywords(
        self,
        legend_id: str,
        keywords: List[List[str]]
    ) -> None:
        """更新 Legend 的关键词"""
        flat_keywords = self._flatten_keywords(keywords)
        keywords_hash = self._calculate_keywords_hash(flat_keywords)

        # 构建关键词组
        keyword_groups = []
        for i, group in enumerate(keywords):
            keyword_groups.append({
                "group_name": f"group_{i}",
                "keywords": group if isinstance(group, list) else [group]
            })

        self.db.set_keywords(
            legend_id,
            keyword_groups,
            source_hash=keywords_hash
        )

        # 记录日志
        self.db.log_sync(
            sync_type="update",
            legend_id=legend_id,
            change_type="keywords_changed",
            details={"keywords_count": len(flat_keywords)}
        )

    def _remove_legend(self, legend_id: str) -> None:
        """移除 Legend（软删除）"""
        # 获取 Legend 类型
        legend = self.db.get_legend(legend_id)
        if legend:
            # 删除数据库记录
            self.db.delete_legend(legend_id)

            # 删除 Markdown 文件（可选，暂时保留）
            # self.file_service.delete_file(legend_id, legend.type)

        # 记录日志
        self.db.log_sync(
            sync_type="delete",
            legend_id=legend_id,
            change_type="removed",
            details={}
        )

    def get_yaml_legends(self) -> YamlKeywordsConfig:
        """获取 YAML 中的 Legend 配置"""
        yaml_data = self._load_yaml()
        if not yaml_data:
            return YamlKeywordsConfig(legends={}, front=[])

        return YamlKeywordsConfig(
            legends=yaml_data.get("legend", {}),
            front=yaml_data.get("front", [])
        )
