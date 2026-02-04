"""奇点档案数据采集器

使用百度千帆智能搜索生成 API 采集 Legend 档案数据
"""

import subprocess
import sys
from pathlib import Path
from typing import Dict, Any


class Fetcher:
    """单次查询工具类"""

    # CybCortex Python 路径（用于调用 semantic_search.py）
    CYBCORTEX_PYTHON = "D:/workspace/cybcortex/.venv/Scripts/python.exe"
    SEARCH_SCRIPT = "D:/workspace/cybcortex/1技能库/py_code/gather/search/semantic_search.py"

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
        cmd = [
            Fetcher.CYBCORTEX_PYTHON,
            Fetcher.SEARCH_SCRIPT,
            query,
            "--max-results", str(max_results),
            "--recency", search_recency
        ]

        try:
            # 不指定 encoding，让 subprocess 自动检测
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode != 0:
                return {
                    "success": False,
                    "content": "",
                    "error": result.stderr or "命令执行失败"
                }

            # 返回的 stdout 就是 Markdown 内容
            return {
                "success": True,
                "content": result.stdout,
                "error": None
            }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "content": "",
                "error": "查询超时"
            }
        except Exception as e:
            return {
                "success": False,
                "content": "",
                "error": str(e)
            }
