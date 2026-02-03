"""奇点档案数据采集器

使用百度千帆智能搜索生成 API 采集 Legend 档案数据
"""

import sys
from pathlib import Path
from typing import Dict, Any

# 添加 CybCortex 路径以导入配置
cybcortex_path = Path("D:/workspace/cybcortex/1技能库/py_code")
sys.path.insert(0, str(cybcortex_path))

from gather.search.semantic_search import semantic_search


class Fetcher:
    """单次查询工具类"""

    @staticmethod
    def fetch(
        query: str,
        instruction: str = "",
        max_results: int = 10,
        search_recency: str = "year"
    ) -> Dict[str, Any]:
        """执行单次搜索查询

        Args:
            query: 搜索关键词
            instruction: 人设指令
            max_results: 最大结果数
            search_recency: 时间范围

        Returns:
            {"success": bool, "content": str, "error": str}
        """
        result = semantic_search(
            query=query,
            instruction=instruction,
            max_results=max_results,
            search_recency=search_recency,
            return_raw=False
        )

        if "error" in result:
            return {
                "success": False,
                "content": "",
                "error": result["error"]
            }

        return {
            "success": True,
            "content": result.get("summary", ""),
            "error": None
        }
