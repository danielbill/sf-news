"""奇点研究员 - 总调度

读取查询模板，分次调用 fetcher，拼接结果
"""

import sys
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.fetcher import Fetcher


# 查询模板目录
QUERY_TEMPLATES_DIR = Path(__file__).parent


class Researcher:
    """奇点研究员 - 总调度"""

    def __init__(self):
        self.fetcher = Fetcher()

    def _format_date(self) -> str:
        """格式化当前日期"""
        return datetime.now().strftime("%Y-%m-%d")

    def _parse_query_template(self, template_content: str) -> List[Dict[str, str]]:
        """解析查询模板，提取各次查询的搜索词和指令

        Returns:
            [
                {"search": "搜索词1", "instruction": "指令1"},
                {"search": "搜索词2", "instruction": "指令2"},
                ...
            ]
        """
        lines = template_content.split('\n')
        queries = []
        current_search = ""
        current_instruction = []
        in_instruction = False

        for line in lines:
            if line.startswith("**搜索词**："):
                # 保存之前的查询（如果有）
                if current_search:
                    queries.append({
                        "search": current_search.strip(),
                        "instruction": "\n".join(current_instruction).strip()
                    })
                current_search = line.split("**搜索词**：", 1)[1].strip()
                current_instruction = []
                in_instruction = False
            elif line.startswith("**指令**："):
                current_instruction.append(line.split("**指令**：", 1)[1])
                in_instruction = True
            elif in_instruction:
                current_instruction.append(line)

        # 保存最后一个查询
        if current_search:
            queries.append({
                "search": current_search.strip(),
                "instruction": "\n".join(current_instruction).strip()
            })

        return queries

    def _replace_variables(self, text: str, variables: Dict[str, str]) -> str:
        """替换模板中的变量"""
        for key, value in variables.items():
            text = text.replace(key, value)
        return text

    def research(
        self,
        template_name: str,
        variables: Dict[str, str],
        title: str,
        max_results: int = 10,
        search_recency: str = "year"
    ) -> Dict[str, Any]:
        """执行研究（读取模板，分次查询，拼接结果）

        Args:
            template_name: 查询模板文件名（如 "people_query.md"）
            variables: 要替换的变量字典（如 {"{name_cn}": "张一鸣"}）
            title: 档案标题（如 "张一鸣 档案"）
            max_results: 最大搜索结果数
            search_recency: 时间范围

        Returns:
            {"success": bool, "content": str, "error": str}
        """
        # 加载查询模板
        template_path = QUERY_TEMPLATES_DIR / template_name
        if not template_path.exists():
            return {
                "success": False,
                "content": "",
                "error": f"查询模板不存在: {template_path}"
            }

        template = template_path.read_text(encoding="utf-8")

        # 替换变量
        template = self._replace_variables(template, variables)

        # 解析查询
        queries = self._parse_query_template(template)

        # 拼接结果
        sections = []
        sections.append(f"# {title}\n")
        sections.append(f"> 采集日期：{self._format_date()}\n")

        # 分次查询
        for i, query_info in enumerate(queries, 1):
            print(f"正在执行第{i}次查询...")

            # QPS 限制：每次查询间隔 1 秒
            if i > 1:
                time.sleep(1)

            result = self.fetcher.fetch(
                query=query_info["search"],
                instruction=query_info["instruction"],
                max_results=max_results,
                search_recency=search_recency
            )

            if not result["success"]:
                return {
                    "success": False,
                    "content": "",
                    "error": result["error"]
                }

            sections.append(result["content"])
            sections.append("\n---\n")

        return {
            "success": True,
            "content": "\n".join(sections),
            "error": None
        }


def save_profile(content: str, output_path: str) -> bool:
    """保存档案到文件"""
    try:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(content, encoding="utf-8")
        return True
    except Exception as e:
        print(f"保存文件失败: {e}")
        return False


# CLI 入口
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="奇点档案数据采集")
    parser.add_argument("template", help="查询模板文件名（如 people_query.md）")
    parser.add_argument("--title", required=True, help="档案标题")
    parser.add_argument("--var", action="append", help="变量替换，格式：key=value", default=[])
    parser.add_argument("--output", help="输出文件路径")

    args = parser.parse_args()

    # 解析变量
    variables = {}
    for var in args.var:
        if "=" in var:
            key, value = var.split("=", 1)
            variables[key] = value

    researcher = Researcher()
    result = researcher.research(
        template_name=args.template,
        variables=variables,
        title=args.title
    )

    if result["success"]:
        content = result["content"]
        if args.output:
            if save_profile(content, args.output):
                print(f"已保存到: {args.output}")
            else:
                print(content)
        else:
            print(content)
    else:
        print(f"错误: {result['error']}")
