"""新闻源测试器 - 测试各个新闻源的连接状态和数据量

与 UniversalCrawler 的区别：
- 不进行关键词过滤
- 不获取文章正文
- 只测试 API 连接和数据返回量
"""

import importlib
import httpx
from typing import List, Dict, Any
from datetime import datetime

from ..config import ConfigReader


# 源 ID 到解析器模块的映射
PARSER_MODULE_MAP = {
    "36kr": "_36kr",
    "wallstreetcn-live": "wallstreetcn_live",
    "wallstreetcn-news": "wallstreetcn_news",
    "cls-telegraph": "cls_telegraph",
    "cls-depth": "cls_depth",
}


class SourceTester:
    """新闻源测试器"""

    def __init__(self, config_dir: str = "config"):
        """初始化测试器

        Args:
            config_dir: 配置文件目录
        """
        self.config_dir = config_dir
        self.client = httpx.AsyncClient(
            timeout=30,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        )

    async def test_all(self) -> Dict[str, Any]:
        """测试所有启用的新闻源

        Returns:
            测试结果字典
        """
        reader = ConfigReader(self.config_dir)
        sources_config = reader.load_news_sources_config()

        results = []

        for source in sources_config.sources:
            if not source.enabled:
                continue

            result = await self.test_single(source)
            results.append(result)

        return {
            "sources": results,
            "total": len(results),
            "timestamp": datetime.now().isoformat()
        }

    async def test_single(self, source: Any) -> Dict[str, Any]:
        """测试单个新闻源

        Args:
            source: 新闻源配置对象

        Returns:
            测试结果字典
        """
        result = {
            "id": source.id,
            "name": source.name,
            "count": 0,
            "status": "error",
            "message": ""
        }

        try:
            # 动态加载解析器
            module_id = PARSER_MODULE_MAP.get(source.id, source.id)
            module_name = f"src.crawlers.parsers.{module_id}"

            module = importlib.import_module(module_name)
            parse_func = getattr(module, "parse")

            # 调用解析器
            articles = await parse_func(
                response=None,
                source_config={"id": source.id, "name": source.name},
                client=self.client
            )

            result["count"] = len(articles)

            if len(articles) > 0:
                result["status"] = "ok"
                result["message"] = "正常"
            else:
                result["status"] = "empty"
                result["message"] = "无数据"

        except ImportError as e:
            result["status"] = "error"
            result["message"] = f"解析器不存在: {e}"
        except httpx.HTTPStatusError as e:
            result["status"] = "error"
            result["message"] = f"HTTP错误: {e.response.status_code}"
        except httpx.RequestError as e:
            result["status"] = "error"
            result["message"] = f"连接失败: {e}"
        except Exception as e:
            result["status"] = "error"
            result["message"] = f"错误: {e}"

        return result

    async def close(self):
        """关闭 HTTP 客户端"""
        await self.client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
