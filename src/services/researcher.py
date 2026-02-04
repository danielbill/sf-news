"""研究员 - 任务拆解器

职责：
1. 接收实体数据包
2. 解析数据，生成查询任务列表（company/people/product）
3. 循环调用 queryer 执行查询
4. 调用 render 渲染结果
5. 调用 saver 保存文件
"""

import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.queryer import Queryer
from services.render import get_render, BaseRender
from services.saver import Saver


@dataclass
class ResearchTask:
    """研究任务"""
    content_type: str  # company/people/product
    entity_id: str
    name_cn: str
    name_en: str
    avatar: str = ""
    company_id: str = ""  # 产品需要
    company_name: str = ""  # 产品需要


class Researcher:
    """研究员 - 任务拆解器"""

    def __init__(
        self,
        queryer: Optional[Queryer] = None,
        saver: Optional[Saver] = None,
        entity_type: str = "legend"  # legend/nova/front
    ):
        """初始化研究员

        Args:
            queryer: 查询器，默认创建新实例
            saver: 保存器，默认创建新实例
            entity_type: 实体类型 (legend/nova/front)
        """
        self.queryer = queryer or Queryer()
        self.saver = saver or Saver()
        self.entity_type = entity_type

    def _parse_data(self, entity_id: str, data: Dict) -> List[ResearchTask]:
        """解析实体数据，生成研究任务

        统一处理 legend/nova/front 三种实体类型：
        - 公司档案（实体本身）
        - 人物档案（key_roles 中的关键人物）
        - 产品档案（products 中的产品）

        Args:
            entity_id: 实体 ID（如 "bytedance"）
            data: 实体配置数据（来自 YAML）

        Returns:
            研究任务列表
        """
        tasks = []
        name_en = data.get("name_en", "")
        name_cn = data.get("name_cn", "")

        # 1. 公司/组织档案（实体本身）
        # 如果有 key_roles 或 products，说明是公司
        if "key_roles" in data or "products" in data:
            tasks.append(ResearchTask(
                content_type="company",
                entity_id=entity_id,
                name_cn=name_cn,
                name_en=name_en,
                avatar=""
            ))

        # 2. 人物档案（key_roles 中的关键人物）
        for role in data.get("key_roles", []):
            role_name = role.get("name", "")
            tasks.append(ResearchTask(
                content_type="people",
                entity_id=role_name,
                name_cn=role_name,
                name_en=role_name,
                avatar=""
            ))

        # 3. 产品档案
        for product in data.get("products", []):
            tasks.append(ResearchTask(
                content_type="product",
                entity_id=product["name"].lower().replace(" ", "_").replace("-", "_"),
                name_cn=product.get("name", ""),
                name_en=product.get("name", ""),
                company_id=entity_id,
                company_name=name_cn
            ))

        return tasks

    def _execute_task(self, task: ResearchTask) -> Dict[str, Any]:
        """执行单个研究任务

        流程：
        1. 获取模板名
        2. 准备变量
        3. 调用 queryer
        4. 调用 render
        5. 调用 saver

        Args:
            task: 研究任务

        Returns:
            {"success": bool, "file_path": str, "error": str}
        """
        try:
            # 1. 确定模板名
            template_map = {
                "company": "company_query.yaml",
                "people": "people_query.yaml",
                "product": "product_query.yaml",
            }
            template_name = template_map.get(task.content_type)
            if not template_name:
                return {
                    "success": False,
                    "file_path": "",
                    "error": f"未知的内容类型: {task.content_type}"
                }

            # 2. 准备变量
            variables = {
                "{id}": task.entity_id,
                "{name_cn}": task.name_cn,
                "{name_en}": task.name_en,
                "{avatar}": task.avatar,
            }
            if task.content_type == "product":
                variables["{company}"] = task.company_name

            # 3. 调用 queryer
            query_result = self.queryer.research(
                template_name=template_name,
                variables=variables
            )

            if not query_result["success"]:
                return {
                    "success": False,
                    "file_path": "",
                    "error": f"查询失败: {query_result['error']}"
                }

            # 4. 调用 render
            if task.content_type == "product":
                # ProductRender 使用 product_id 参数
                render_kwargs = {
                    "product_id": task.entity_id,
                    "name_cn": task.name_cn,
                    "name_en": task.name_en,
                    "company_id": task.company_id,
                    "company_name": task.company_name,
                }
            else:
                # CompanyRender 和 PeopleRender 使用 entity_id
                render_kwargs = {
                    "entity_id": task.entity_id,
                    "name_cn": task.name_cn,
                    "name_en": task.name_en,
                    "avatar": task.avatar,
                }

            renderer = get_render(task.content_type, **render_kwargs)

            # 添加查询结果
            for result in query_result["results"]:
                renderer.add_result(result["content"])

            # 生成 Markdown
            markdown = renderer.to_markdown()

            # 5. 调用 saver
            filename = f"{task.entity_id}.md"
            file_path = self.saver.save(
                content=markdown,
                entity_type=self.entity_type,
                content_type=task.content_type,
                filename=filename
            )

            return {
                "success": True,
                "file_path": str(file_path),
                "error": None
            }

        except Exception as e:
            return {
                "success": False,
                "file_path": "",
                "error": str(e)
            }

    def research(
        self,
        entity_data: Dict[str, Dict],
        on_progress: Optional[callable] = None
    ) -> Dict[str, Any]:
        """执行研究（批量）

        Args:
            entity_data: 实体数据字典 {entity_id: entity_config, ...}
            on_progress: 进度回调 callback(current, total, entity_id)

        Returns:
            {
                "success": bool,
                "results": {entity_id: [tasks...], ...},
                "errors": {entity_id: error, ...},
                "total": int,
                "completed": int
            }
        """
        # 解析所有任务
        all_tasks = []
        for entity_id, data in entity_data.items():
            tasks = self._parse_data(entity_id, data)
            all_tasks.extend([(entity_id, task) for task in tasks])

        total = len(all_tasks)
        results = {}
        errors = {}
        completed = 0

        for i, (entity_id, task) in enumerate(all_tasks, 1):
            print(f"\n[{i}/{total}] 研究 {task.content_type}: {task.name_cn}")

            if on_progress:
                on_progress(i, total, entity_id)

            # 执行任务
            result = self._execute_task(task)

            if result["success"]:
                completed += 1
                if entity_id not in results:
                    results[entity_id] = []
                results[entity_id].append({
                    "type": task.content_type,
                    "file_path": result["file_path"]
                })
                print(f"  [OK] 已保存: {result['file_path']}")
            else:
                errors[entity_id] = result["error"]
                error_msg = result['error']
                try:
                    print(f"  [X] 失败: {error_msg}")
                except UnicodeEncodeError:
                    # 如果编码失败，使用替换策略
                    safe_msg = error_msg.encode('gbk', errors='replace').decode('gbk')
                    print(f"  [X] 失败: {safe_msg}")

        return {
            "success": completed == total,
            "results": results,
            "errors": errors,
            "total": total,
            "completed": completed
        }

    def research_single(
        self,
        entity_id: str,
        entity_config: Dict
    ) -> Dict[str, Any]:
        """研究单个实体

        Args:
            entity_id: 实体 ID
            entity_config: 实体配置

        Returns:
            研究结果
        """
        return self.research({entity_id: entity_config})


# CLI 入口
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="奇点档案数据采集")
    parser.add_argument("--id", required=True, help="实体 ID")
    parser.add_argument("--name-cn", required=True, help="中文名")
    parser.add_argument("--name-en", required=True, help="英文名")
    parser.add_argument("--type", choices=["company", "people"], default="company", help="类型")
    parser.add_argument("--entity-type", choices=["legend", "nova", "front"], default="nova", help="实体类型")

    args = parser.parse_args()

    # 构造配置
    config = {
        "name_en": args.name_en,
        "name_cn": args.name_cn,
    }
    if args.type == "company":
        config["products"] = []

    # 执行研究
    researcher = Researcher(entity_type=args.entity_type)
    result = researcher.research_single(args.id, config)

    if result["success"]:
        print(f"\n[OK] 研究完成！共完成 {result['completed']} 个任务")
        for entity_id, files in result["results"].items():
            for f in files:
                print(f"  - {f['file_path']}")
    else:
        print(f"\n[X] 研究完成，但有 {result['total'] - result['completed']} 个任务失败")
        for entity_id, error in result["errors"].items():
            print(f"  {entity_id}: {error}")
