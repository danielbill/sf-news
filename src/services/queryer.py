"""通用查询器 - 读取 YAML 模板，循环调用 AI 搜索

职责：
1. 加载 YAML 查询模板
2. 解析模板中的搜索词和指令
3. 替换模板变量
4. 分次调用 AI 搜索（遵守 QPS 限制）
5. 将结果传递给渲染器
"""

import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
import yaml

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.fetcher import Fetcher


class Queryer:
    """通用查询器"""

    # 默认查询参数
    DEFAULT_MAX_RESULTS = 10
    DEFAULT_SEARCH_RECENCY = "year"
    QUERY_INTERVAL = 1  # QPS 限制：每次间隔 1 秒

    def __init__(
        self,
        template_dir: Optional[Path] = None,
        fetcher: Optional[Fetcher] = None
    ):
        """初始化查询器

        Args:
            template_dir: YAML 模板目录，默认为 config/research/
            fetcher: 数据采集器，默认创建新实例
        """
        if template_dir is None:
            # 默认模板目录
            self.template_dir = Path(__file__).parent.parent.parent / "config" / "research"
        else:
            self.template_dir = Path(template_dir)

        self.fetcher = fetcher or Fetcher()

    def _load_template(self, template_name: str) -> List[Dict[str, str]]:
        """加载 YAML 查询模板

        Args:
            template_name: 模板文件名（如 "company_query.yaml"）

        Returns:
            查询列表 [{"search": "...", "instruction": "..."}, ...]
        """
        template_path = self.template_dir / template_name

        if not template_path.exists():
            raise FileNotFoundError(f"查询模板不存在: {template_path}")

        with open(template_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        return data.get("queries", [])

    def _replace_variables(
        self,
        text: str,
        variables: Dict[str, str]
    ) -> str:
        """替换模板中的变量

        Args:
            text: 包含变量的文本
            variables: 变量字典（如 {"{name_cn}": "字节跳动"}）

        Returns:
            替换后的文本
        """
        result = text
        for key, value in variables.items():
            result = result.replace(key, str(value))
        return result

    def research(
        self,
        template_name: str,
        variables: Dict[str, str],
        max_results: int = DEFAULT_MAX_RESULTS,
        search_recency: str = DEFAULT_SEARCH_RECENCY,
        on_progress: Optional[callable] = None
    ) -> Dict[str, Any]:
        """执行研究

        流程：
        1. 加载 YAML 模板
        2. 替换变量
        3. 分次调用 AI 搜索（间隔 1 秒）
        4. 返回结果列表

        Args:
            template_name: 模板文件名（如 "company_query.yaml"）
            variables: 变量字典（如 {"{id}": "bytedance", "{name_cn}": "字节跳动"}）
            max_results: 最大搜索结果数
            search_recency: 时间范围（week/month/semiyear/year）
            on_progress: 进度回调函数 callback(current, total)

        Returns:
            {
                "success": bool,
                "results": [{"search": "...", "content": "..."}, ...],
                "error": str
            }
        """
        try:
            # 加载模板
            queries = self._load_template(template_name)

            if not queries:
                return {
                    "success": False,
                    "results": [],
                    "error": f"模板中没有查询定义: {template_name}"
                }

            results = []
            total = len(queries)

            # 分次查询
            for i, query in enumerate(queries, 1):
                # 替换变量
                search = self._replace_variables(query["search"], variables)
                instruction = self._replace_variables(query.get("instruction", ""), variables)

                # 进度回调
                if on_progress:
                    on_progress(i, total)

                print(f"[{i}/{total}] 查询: {search[:50]}...")

                # QPS 限制
                if i > 1:
                    time.sleep(self.QUERY_INTERVAL)

                # 调用采集器
                result = self.fetcher.fetch(
                    query=search,
                    instruction=instruction,
                    max_results=max_results,
                    search_recency=search_recency
                )

                if not result["success"]:
                    return {
                        "success": False,
                        "results": results,
                        "error": f"第{i}次查询失败: {result['error']}"
                    }

                results.append({
                    "search": search,
                    "content": result["content"]
                })

            return {
                "success": True,
                "results": results,
                "error": None
            }

        except Exception as e:
            return {
                "success": False,
                "results": [],
                "error": str(e)
            }

    def get_template_info(self, template_name: str) -> Dict[str, Any]:
        """获取模板信息（不执行查询）

        Args:
            template_name: 模板文件名

        Returns:
            {"query_count": int, "queries": [...]}
        """
        queries = self._load_template(template_name)
        return {
            "query_count": len(queries),
            "queries": [
                {"search": q["search"][:50] + "..."}
                for q in queries
            ]
        }
