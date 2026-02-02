"""Legend Markdown 文件服务

管理 Legend 实体的 Markdown 档案文件。
"""

from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from ..models.legend import LegendType, LegendTier


class LegendFileService:
    """Markdown 档案文件服务"""

    def __init__(self, base_dir: str = "data/legend"):
        self.base_dir = Path(base_dir)
        self.people_dir = self.base_dir / "people"
        self.orgs_dir = self.base_dir / "orgs"
        self._ensure_dirs()

    def _ensure_dirs(self):
        """确保目录存在"""
        self.people_dir.mkdir(parents=True, exist_ok=True)
        self.orgs_dir.mkdir(parents=True, exist_ok=True)

    def _get_file_path(self, legend_id: str, legend_type: LegendType) -> Path:
        """获取文件路径"""
        if legend_type == LegendType.PERSON:
            return self.people_dir / f"{legend_id}.md"
        else:
            return self.orgs_dir / f"{legend_id}.md"

    def file_exists(self, legend_id: str, legend_type: LegendType) -> bool:
        """检查文件是否存在"""
        return self._get_file_path(legend_id, legend_type).exists()

    def read_file(self, legend_id: str, legend_type: LegendType) -> Optional[str]:
        """读取文件内容"""
        path = self._get_file_path(legend_id, legend_type)
        if not path.exists():
            return None
        return path.read_text(encoding="utf-8")

    def write_file(
        self,
        legend_id: str,
        legend_type: LegendType,
        content: str
    ) -> None:
        """写入文件内容"""
        path = self._get_file_path(legend_id, legend_type)
        path.write_text(content, encoding="utf-8")

    def update_file(
        self,
        legend_id: str,
        legend_type: LegendType,
        content: str
    ) -> bool:
        """更新文件（如果存在）"""
        path = self._get_file_path(legend_id, legend_type)
        if not path.exists():
            return False
        path.write_text(content, encoding="utf-8")
        return True

    def delete_file(self, legend_id: str, legend_type: LegendType) -> bool:
        """删除文件"""
        path = self._get_file_path(legend_id, legend_type)
        if not path.exists():
            return False
        path.unlink()
        return True

    def create_person_file(
        self,
        legend_id: str,
        data: Dict[str, Any]
    ) -> str:
        """创建人物档案文件

        Args:
            legend_id: Legend ID
            data: 档案数据（包含 name_en, name_cn, bio_short 等）

        Returns:
            文件路径
        """
        content = self.render_person_template(legend_id, data)
        self.write_file(legend_id, LegendType.PERSON, content)
        return str(self._get_file_path(legend_id, LegendType.PERSON))

    def create_org_file(
        self,
        legend_id: str,
        data: Dict[str, Any]
    ) -> str:
        """创建组织档案文件

        Args:
            legend_id: Legend ID
            data: 档案数据

        Returns:
            文件路径
        """
        content = self.render_org_template(legend_id, data)
        self.write_file(legend_id, LegendType.ORGANIZATION, content)
        return str(self._get_file_path(legend_id, LegendType.ORGANIZATION))

    def render_person_template(
        self,
        legend_id: str,
        data: Dict[str, Any]
    ) -> str:
        """渲染人物档案模板

        Args:
            legend_id: Legend ID
            data: 档案数据，可包含:
                - name_en: 英文名
                - name_cn: 中文名
                - bio_short: 简短介绍
                - bio_full: 完整介绍
                - keywords: 关键词列表（用于推断行业等）
        """
        now = datetime.now().strftime("%Y-%m-%d")

        content = f"""# {data.get("name_cn", data.get("name_en", legend_id))} 档案

> Legend ID: {legend_id}
> 创建时间: {now}

---

## 人物基础信息

| 字段 | 内容 |
|------|------|
| **ID** | {legend_id} |
| **英文名** | {data.get("name_en", "")} |
| **中文名** | {data.get("name_cn", "")} |
| **头像** | |
| **出生年份** | |
| **国籍** | |
| **教育背景** | |
| **简短介绍** | {data.get("bio_short", "")} |
| **完整介绍** | {data.get("bio_full", "")}

---

## 家庭背景

<!-- 描述家庭背景 -->

### 家庭成员

| 关系 | 姓名 | 备注 |
|------|------|------|
| 父亲 | | |
| 母亲 | | |
| 配偶 | | |
| 子女 | | |
| 兄弟姐妹 | | |

---

## 伟愿与理念

### 伟愿声明
<!-- 一句话概括终极目标 -->

### 核心信念
- <!-- 列举核心信念/思维模式 -->
-
-

### 金句库

| 金句 | 来源 | 日期 |
|------|------|------|
| | | |
| | | |

---

## 当下工作重心

<!-- 描述当前主要关注的项目/领域 -->

---

## 公司矩阵

| 公司 | 角色 | 任期 |
|------|------|------|
| | | |
| | | |
| | | |

---

## 核心产品/服务

| 产品/服务 | 描述 | 状态 | 所属公司 |
|-----------|------|------|----------|
| | | | |
| | | | |
| | | | |

---

## 影响力

### 影响力范围
<!-- 如：全球 / 特定行业 -->

### 影响力指标
| 指标 | 数值 |
|------|------|
| 社交媒体粉丝 | |
| 控制公司市值 | |
| 其他 | |

---

## 文明级影响

### 影响等级
- [ ] **SINGULARITY** — 奇点人物（引发文明级跃迁）
- [ ] **QUASI** — 准奇点人物（引发行业级变革）
- [ ] **POTENTIAL** — 潜力人物

### 对人类文明的影响
<!-- 描述如何改变世界 -->

---

## 关键里程碑

| 日期 | 事件 | 影响 |
|------|------|------|
| | | |
| | | |
| | | |
| | | |
| | | |

---

## 关键词配置

<!-- 以下关键词来自 news_keywords.yaml -->

"""
        # 添加关键词列表
        keywords = data.get("keywords", [])
        if keywords:
            for i, kw in enumerate(keywords, 1):
                content += f"{i}. {kw}\n"

        content += "\n---\n\n*本档案由奇点研究员自动生成和维护*"
        return content

    def render_org_template(
        self,
        legend_id: str,
        data: Dict[str, Any]
    ) -> str:
        """渲染组织档案模板

        Args:
            legend_id: Legend ID
            data: 档案数据
        """
        now = datetime.now().strftime("%Y-%m-%d")

        content = f"""# {data.get("name_cn", data.get("name_en", legend_id))} 档案

> Legend ID: {legend_id}
> 创建时间: {now}

---

## 组织基础信息

| 字段 | 内容 |
|------|------|
| **ID** | {legend_id} |
| **英文名** | {data.get("name_en", "")} |
| **中文名** | {data.get("name_cn", "")} |
| **Logo** | |
| **成立年份** | |
| **总部地点** | |
| **组织类型** | |
| **股票代码** | |
| **简短介绍** | {data.get("bio_short", "")} |
| **完整介绍** | {data.get("bio_full", "")} |

---

## 核心领袖

### 创始人

| 人物ID | 姓名 | 角色 |
|--------|------|------|
| | | |
| | | |

### 现任领导层

| 人物ID | 姓名 | 职位 |
|--------|------|------|
| | | |
| | | |

---

## 商业模式

<!-- 描述公司的商业模式 -->

### 收入来源

| 来源 | 描述 |
|------|------|
| | |
| | |

---

## 核心产品/服务

| 产品/服务 | 描述 | 状态 |
|-----------|------|------|
| | | |
| | | |
| | | |

---

## 财务信息

### 市值与营收

| 指标 | 数值 | 备注 |
|------|------|------|
| 市值 | | |
| 年营收 | | 财年： |
| 营收增长率 | | 同比/环比 |
| 净利润 | | 财年： |
| 现金储备 | | |

### 融资情况（非上市公司）

| 轮次 | 金额 | 日期 | 估值 |
|------|------|------|------|
| | | | |
| | | | |

---

## 股权结构

| 持有者 | 类型 | 持股比例 |
|--------|------|----------|
| | | |
| | | |

---

## 竞争格局

### 行业与地位

| 字段 | 内容 |
|------|------|
| **所属行业** | |
| **市场地位** | |
| **核心优势** | |

### 主要竞争对手

| 竞争对手 | 描述 |
|----------|------|
| | |
| | |

---

## 使命与理念

### 使命/愿景
<!-- 一句话概括组织的终极目标 -->

### 核心价值观
- <!-- 列举核心价值观 -->
-
-

### 使命陈述
<!-- 详细描述组织的使命 -->

---

## 影响力

### 影响力范围
<!-- 如：全球 / 特定行业 / 特定地区 -->

### 影响力指标

| 指标 | 数值 |
|------|------|
| | |
| | |

---

## 文明级影响

### 影响等级
- [ ] **SINGULARITY** — 奇点（引发文明级跃迁）
- [ ] **QUASI** — 准奇点（引发行业级变革）
- [ ] **POTENTIAL** — 潜力

### 对人类文明的影响
<!-- 描述如何改变世界 -->

---

## 关键里程碑

| 日期 | 事件 | 影响 |
|------|------|------|
| | | |
| | | |
| | | |

---

## 关键词配置

<!-- 以下关键词来自 news_keywords.yaml -->

"""
        # 添加关键词列表
        keywords = data.get("keywords", [])
        if keywords:
            for i, kw in enumerate(keywords, 1):
                content += f"{i}. {kw}\n"

        content += "\n---\n\n*本档案由奇点研究员自动生成和维护*"
        return content

    def list_all_people(self) -> list[str]:
        """列出所有人物档案文件名"""
        return [f.stem for f in self.people_dir.glob("*.md")]

    def list_all_orgs(self) -> list[str]:
        """列出所有组织档案文件名"""
        return [f.stem for f in self.orgs_dir.glob("*.md")]
