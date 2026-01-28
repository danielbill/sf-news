"""测试配置模块"""

import pytest
from pathlib import Path

from src.config import ConfigReader
from src.config.models import (
    Legend,
    Company,
    NewsSource,
    LegendConfig,
    CompanyConfig,
    NewsSourcesConfig,
    CrawlerConfig,
)


class TestConfigReader:
    """测试配置读取器"""

    def test_load_legend_config(self):
        """测试加载奇点人物配置"""
        reader = ConfigReader()
        config = reader.load_legend_config()

        assert config is not None
        assert len(config.legends) > 0
        assert config.legends[0].id == "musk"
        assert config.legends[0].name_cn == "马斯克"

    def test_load_company_config(self):
        """测试加载公司配置"""
        reader = ConfigReader()
        config = reader.load_company_config()

        assert config is not None
        assert len(config.companies) > 0
        assert config.companies[0].id == "TSLA"

    def test_load_news_keywords_config(self):
        """测试加载新闻关键词配置"""
        reader = ConfigReader()
        config = reader.load_news_keywords_config()

        assert config is not None
        assert "people" in config
        assert "companies" in config
        assert "topics" in config

    def test_load_news_sources_config(self):
        """测试加载新闻源配置"""
        reader = ConfigReader()
        config = reader.load_news_sources_config()

        assert config is not None
        assert len(config.sources) > 0
        # 验证新闻源数量 (参考消息、澎湃、凤凰、头条、华尔街见闻x2、财联社x2、36氪)
        assert len(config.sources) == 9

    def test_load_crawler_config(self):
        """测试加载抓取器配置"""
        reader = ConfigReader()
        config = reader.load_crawler_config()

        assert config is not None
        assert config.strategy.interval == 900  # 15分钟
        assert config.strategy.min_interval == 900  # 最小间隔限制
        assert config.strategy.concurrent == 3
        assert config.network.timeout == 30

    def test_load_all(self):
        """测试加载所有配置"""
        reader = ConfigReader()
        configs = reader.load_all()

        assert "legend" in configs
        assert "company" in configs
        assert "news_keywords" in configs
        assert "news_sources" in configs
        assert "crawler" in configs


class TestConfigModels:
    """测试配置数据模型"""

    def test_legend_model(self):
        """测试 Legend 模型"""
        legend = Legend(
            id="musk",
            name="Elon Musk",
            name_cn="马斯克",
            tier="singularity",
            company_id="TSLA",
            role="CEO"
        )
        assert legend.id == "musk"
        assert legend.name_cn == "马斯克"

    def test_news_source_model(self):
        """测试 NewsSource 模型"""
        source = NewsSource(
            id="cankaoxiaoxi",
            name="参考消息",
            type="official",
            url="https://example.com",
            parser="json"
        )
        assert source.id == "cankaoxiaoxi"
        assert source.enabled is True  # 默认值
