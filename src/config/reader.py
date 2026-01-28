"""配置读取器"""

from pathlib import Path
from typing import Dict, Any
import yaml

from .models import (
    LegendConfig,
    CompanyConfig,
    CompanyRelationsConfig,
    NewsSourcesConfig,
    CrawlerConfig,
)


class ConfigReader:
    """配置文件读取器"""

    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)

    def _load_yaml(self, filename: str) -> Dict[str, Any]:
        """加载 YAML 文件"""
        path = self.config_dir / filename
        if not path.exists():
            raise FileNotFoundError(f"配置文件不存在: {path}")

        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def load_legend_config(self) -> LegendConfig:
        """加载奇点人物配置"""
        data = self._load_yaml("legend.yaml")
        return LegendConfig(**data)

    def load_company_config(self) -> CompanyRelationsConfig:
        """加载公司档案配置"""
        data = self._load_yaml("company.yaml")
        return CompanyRelationsConfig(**data)

    def load_news_keywords_config(self) -> Dict[str, Any]:
        """加载新闻关键词配置"""
        return self._load_yaml("news_keywords.yaml")

    def load_news_sources_config(self) -> NewsSourcesConfig:
        """加载新闻源配置"""
        data = self._load_yaml("news_sources.yaml")
        return NewsSourcesConfig(**data)

    def load_crawler_config(self) -> CrawlerConfig:
        """加载抓取器配置"""
        data = self._load_yaml("crawler_config.yaml")
        return CrawlerConfig(**data)

    def load_all(self) -> Dict[str, Any]:
        """加载所有配置"""
        return {
            "legend": self.load_legend_config(),
            "company": self.load_company_config(),
            "news_keywords": self.load_news_keywords_config(),
            "news_sources": self.load_news_sources_config(),
            "crawler": self.load_crawler_config(),
        }
