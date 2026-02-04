"""档案渲染器 - 累积查询结果，生成 Markdown

职责：
1. 接收查询结果（多次查询）
2. 按模板格式组装 Markdown
3. 生成完整档案内容
"""

import sys
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
from abc import ABC, abstractmethod

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))


class BaseRender(ABC):
    """渲染器基类"""

    def __init__(self, title: str, entity_id: str):
        """初始化渲染器

        Args:
            title: 档案标题
            entity_id: 实体 ID
        """
        self.title = title
        self.entity_id = entity_id
        self.sections: List[str] = []

    def _format_date(self) -> str:
        """格式化当前日期"""
        return datetime.now().strftime("%Y-%m-%d")

    def add_result(self, content: str) -> None:
        """添加一次查询结果

        Args:
            content: AI 生成的 Markdown 内容
        """
        self.sections.append(content)

    def add_separator(self) -> None:
        """添加分隔符"""
        if self.sections:
            self.sections.append("\n---\n")

    @abstractmethod
    def to_markdown(self) -> str:
        """生成完整 Markdown 内容

        Returns:
            完整的 Markdown 字符串
        """
        pass


class CompanyRender(BaseRender):
    """公司档案渲染器"""

    def __init__(
        self,
        entity_id: str,
        name_cn: str,
        name_en: str,
        avatar: str = ""
    ):
        """初始化公司渲染器

        Args:
            entity_id: 公司 ID
            name_cn: 中文名
            name_en: 英文名
            avatar: Logo URL
        """
        title = f"{name_cn} ({name_en}) 档案"
        super().__init__(title, entity_id)
        self.name_cn = name_cn
        self.name_en = name_en
        self.avatar = avatar

    def to_markdown(self) -> str:
        """生成公司档案 Markdown"""
        lines = [
            f"# {self.title}\n",
            f"> 采集日期：{self._format_date()}",
            f"> ID：{self.entity_id}\n",
        ]

        # 添加所有查询结果
        for section in self.sections:
            lines.append(section)
            lines.append("\n---\n")

        # 添加元数据
        lines.extend([
            "## 元数据",
            "",
            f"- **ID**：{self.entity_id}",
            f"- **英文名**：{self.name_en}",
            f"- **中文名**：{self.name_cn}",
            "",
            "---",
            "",
            f"*本档案由 AI 自动采集生成，仅供参考。*"
        ])

        return "\n".join(lines)


class PeopleRender(BaseRender):
    """人物档案渲染器"""

    def __init__(
        self,
        entity_id: str,
        name_cn: str,
        name_en: str,
        avatar: str = ""
    ):
        """初始化人物渲染器

        Args:
            entity_id: 人物 ID
            name_cn: 中文名
            name_en: 英文名
            avatar: 头像 URL
        """
        title = f"{name_cn} ({name_en}) 档案"
        super().__init__(title, entity_id)
        self.name_cn = name_cn
        self.name_en = name_en
        self.avatar = avatar

    def to_markdown(self) -> str:
        """生成人物档案 Markdown"""
        lines = [
            f"# {self.title}\n",
            f"> 采集日期：{self._format_date()}",
            f"> ID：{self.entity_id}\n",
        ]

        # 添加所有查询结果
        for section in self.sections:
            lines.append(section)
            lines.append("\n---\n")

        # 添加元数据
        lines.extend([
            "## 元数据",
            "",
            f"- **ID**：{self.entity_id}",
            f"- **英文名**：{self.name_en}",
            f"- **中文名**：{self.name_cn}",
            f"- **头像**：{self.avatar or '未设置'}",
            "",
            "---",
            "",
            f"*本档案由 AI 自动采集生成，仅供参考。*"
        ])

        return "\n".join(lines)


class ProductRender(BaseRender):
    """产品档案渲染器"""

    def __init__(
        self,
        product_id: str,
        name_cn: str,
        name_en: str,
        company_id: str,
        company_name: str = ""
    ):
        """初始化产品渲染器

        Args:
            product_id: 产品 ID
            name_cn: 中文名
            name_en: 英文名
            company_id: 所属公司 ID
            company_name: 所属公司名称
        """
        title = f"{name_cn} ({name_en}) 档案"
        super().__init__(title, product_id)
        self.name_cn = name_cn
        self.name_en = name_en
        self.company_id = company_id
        self.company_name = company_name

    def to_markdown(self) -> str:
        """生成产品档案 Markdown"""
        company_display = f"{self.company_name} ({self.company_id})" if self.company_name else self.company_id
        lines = [
            f"# {self.title}\n",
            f"> 采集日期：{self._format_date()}",
            f"> ID：{self.entity_id}",
            f"> 所属公司：{company_display}\n",
        ]

        # 添加所有查询结果
        for section in self.sections:
            lines.append(section)
            lines.append("\n---\n")

        # 添加元数据
        company_display2 = f"{self.company_name} ({self.company_id})" if self.company_name else self.company_id
        lines.extend([
            "## 元数据",
            "",
            f"- **ID**：{self.entity_id}",
            f"- **英文名**：{self.name_en}",
            f"- **中文名**：{self.name_cn}",
            f"- **所属公司**：{company_display2}",
            "",
            "---",
            "",
            f"*本档案由 AI 自动采集生成，仅供参考。*"
        ])

        return "\n".join(lines)


def get_render(
    content_type: str,
    **kwargs
) -> BaseRender:
    """工厂函数：根据内容类型获取渲染器

    Args:
        content_type: 内容类型 (company/people/product)
        **kwargs: 渲染器参数

    Returns:
        对应的渲染器实例

    Raises:
        ValueError: 不支持的内容类型
    """
    renders = {
        "company": CompanyRender,
        "people": PeopleRender,
        "product": ProductRender,
    }

    render_class = renders.get(content_type)
    if not render_class:
        raise ValueError(f"不支持的内容类型: {content_type}")

    return render_class(**kwargs)
