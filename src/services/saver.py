"""档案保存器 - 读取配置，保存档案文件

职责：
1. 读取 research_config.yaml 配置
2. 根据配置确定输出路径
3. 创建目录并保存文件
"""

import sys
from pathlib import Path
from typing import Dict, Optional
import yaml

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))


class Saver:
    """档案保存器"""

    # 默认配置文件路径
    DEFAULT_CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "research_config.yaml"

    def __init__(self, config_path: Optional[Path] = None):
        """初始化保存器

        Args:
            config_path: 配置文件路径，默认为 config/research_config.yaml
        """
        self.config_path = config_path or self.DEFAULT_CONFIG_PATH
        self._config: Optional[Dict] = None

    def _load_config(self) -> Dict:
        """加载配置文件"""
        if self._config is None:
            if not self.config_path.exists():
                raise FileNotFoundError(f"配置文件不存在: {self.config_path}")

            with open(self.config_path, "r", encoding="utf-8") as f:
                self._config = yaml.safe_load(f)

        return self._config

    def _get_output_path(
        self,
        entity_type: str,
        content_type: str
    ) -> Path:
        """获取输出路径

        Args:
            entity_type: 实体类型 (legend/nova/front)
            content_type: 内容类型 (company/people/product)

        Returns:
            输出目录路径
        """
        config = self._load_config()
        output_paths = config.get("output_paths", {})

        # 获取模板路径
        template_path = output_paths.get(content_type)
        if not template_path:
            raise ValueError(f"配置中没有 {content_type} 的输出路径")

        # 替换 {entity_type}
        output_path = template_path.replace("{entity_type}", entity_type)

        return Path(output_path)

    def save(
        self,
        content: str,
        entity_type: str,
        content_type: str,
        filename: str
    ) -> Path:
        """保存档案文件

        Args:
            content: Markdown 内容
            entity_type: 实体类型 (legend/nova/front)
            content_type: 内容类型 (company/people/product)
            filename: 文件名（如 "bytedance.md"）

        Returns:
            保存的文件完整路径

        Raises:
            FileNotFoundError: 配置文件不存在
            ValueError: 配置项缺失
        """
        output_dir = self._get_output_path(entity_type, content_type)
        output_file = output_dir / filename

        # 创建目录
        output_dir.mkdir(parents=True, exist_ok=True)

        # 写入文件
        output_file.write_text(content, encoding="utf-8")

        return output_file

    def exists(
        self,
        entity_type: str,
        content_type: str,
        filename: str
    ) -> bool:
        """检查文件是否存在

        Args:
            entity_type: 实体类型
            content_type: 内容类型
            filename: 文件名

        Returns:
            文件是否存在
        """
        output_dir = self._get_output_path(entity_type, content_type)
        output_file = output_dir / filename
        return output_file.exists()

    def read(
        self,
        entity_type: str,
        content_type: str,
        filename: str
    ) -> Optional[str]:
        """读取已保存的档案

        Args:
            entity_type: 实体类型
            content_type: 内容类型
            filename: 文件名

        Returns:
            文件内容，不存在则返回 None
        """
        output_dir = self._get_output_path(entity_type, content_type)
        output_file = output_dir / filename

        if output_file.exists():
            return output_file.read_text(encoding="utf-8")
        return None

    def list_files(
        self,
        entity_type: str,
        content_type: str
    ) -> list:
        """列出目录下所有档案

        Args:
            entity_type: 实体类型
            content_type: 内容类型

        Returns:
            文件名列表
        """
        output_dir = self._get_output_path(entity_type, content_type)

        if output_dir.exists():
            return [f.name for f in output_dir.glob("*.md")]
        return []
