#!/usr/bin/env python
"""逐步测试字节跳动档案生成流程"""

import sys
import os
from pathlib import Path

# 先导入 src 以设置编码
sys.path.insert(0, str(Path(__file__).parent / "src"))
import src  # 触发编码设置

def step_1_check_yaml():
    """步骤1: 检查 nova.yaml 配置"""
    print("=" * 60)
    print("步骤1: 检查 nova.yaml 配置")
    print("=" * 60)

    import yaml
    yaml_path = Path("config/nova.yaml")

    with open(yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    print(f"yaml 内容: {data.get('bytedance', {})}")
    print("[OK] 步骤1 完成\n")
    return data

def step_2_parse_data():
    """步骤2: 检查数据解析"""
    print("=" * 60)
    print("步骤2: 检查 researcher._parse_data()")
    print("=" * 60)

    from services.researcher import Researcher

    researcher = Researcher(entity_type="nova")
    bytedance_config = {
        "name_en": "ByteDance",
        "name_cn": "字节跳动",
        "key_roles": [
            {"name": "张一鸣", "keywords": ["张一鸣"]},
            {"name": "梁汝波", "keywords": ["梁汝波"]}
        ],
        "products": [
            {"name": "豆包"},
            {"name": "Dola"},
            {"name": "火山引擎"},
            {"name": "TikTok"},
            {"name": "抖音"}
        ]
    }

    tasks = researcher._parse_data("bytedance", bytedance_config)

    print(f"生成的任务数量: {len(tasks)}")
    for i, task in enumerate(tasks, 1):
        print(f"  任务{i}: {task.content_type} | {task.entity_id} | {task.name_cn}")

    print("[OK] 步骤2 完成\n")
    return tasks

def step_3_check_query_template():
    """步骤3: 检查查询模板"""
    print("=" * 60)
    print("步骤3: 检查 company_query.yaml 模板")
    print("=" * 60)

    import yaml
    template_path = Path("config/research/company_query.yaml")

    with open(template_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    queries = data.get("queries", [])
    print(f"查询数量: {len(queries)}")
    for i, q in enumerate(queries, 1):
        print(f"  查询{i}: {q.get('search', '')[:60]}...")

    print("[OK] 步骤3 完成\n")
    return queries

def step_4_test_queryer():
    """步骤4: 测试 queryer 查询"""
    print("=" * 60)
    print("步骤4: 测试 Queryer.research()")
    print("=" * 60)

    from services.queryer import Queryer

    queryer = Queryer()

    variables = {
        "{id}": "bytedance",
        "{name_cn}": "字节跳动",
        "{name_en}": "ByteDance",
        "{avatar}": ""
    }

    print(f"变量: {variables}")
    print("开始查询 (仅测试第1个模板)...")

    result = queryer.research(
        template_name="company_query.yaml",
        variables=variables,
        max_results=3
    )

    print(f"\n查询结果:")
    print(f"  成功: {result['success']}")
    if result['success']:
        print(f"  结果数量: {len(result['results'])}")
        for i, r in enumerate(result['results'], 1):
            content_len = len(r['content'])
            print(f"    结果{i}: 内容长度 {content_len} 字符")
            # 检查内容前100字符
            preview = r['content'][:100]
            print(f"    预览: {preview}")
    else:
        print(f"  错误: {result['error']}")

    print("\n✓ 步骤4 完成\n")
    return result

def step_5_test_render():
    """步骤5: 测试 render 渲染"""
    print("=" * 60)
    print("步骤5: 测试 CompanyRender")
    print("=" * 60)

    from services.render import CompanyRender

    renderer = CompanyRender(
        entity_id="bytedance",
        name_cn="字节跳动",
        name_en="ByteDance"
    )

    # 添加一些模拟内容
    renderer.add_result("## 测试内容\n这是测试内容。")
    renderer.add_separator()

    markdown = renderer.to_markdown()

    print(f"生成的 Markdown 长度: {len(markdown)} 字符")
    print(f"前200字符:\n{markdown[:200]}")

    print("\n✓ 步骤5 完成\n")
    return markdown

def step_6_test_saver():
    """步骤6: 测试 saver 保存"""
    print("=" * 60)
    print("步骤6: 测试 Saver.save()")
    print("=" * 60)

    from services.saver import Saver

    saver = Saver()
    test_content = "# 测试\n\n这是测试内容。"

    file_path = saver.save(
        content=test_content,
        entity_type="nova",
        content_type="company",
        filename="test_bytedance.md"
    )

    print(f"保存路径: {file_path}")

    # 读取验证
    if file_path.exists():
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        print(f"文件内容: {content}")
        # 清理测试文件
        file_path.unlink()
        print("[OK] 测试文件已清理")
    else:
        print("[X] 文件不存在!")

    print("\n[OK] 步骤6 完成\n")
    return file_path

def step_7_full_pipeline():
    """步骤7: 完整流程测试（单任务）"""
    print("=" * 60)
    print("步骤7: 完整流程测试 - 仅公司档案")
    print("=" * 60)

    from services.researcher import Researcher

    researcher = Researcher(entity_type="nova")

    # 只测试公司档案
    config = {
        "name_en": "ByteDance",
        "name_cn": "字节跳动",
        "key_roles": [],  # 空的，只生成公司
        "products": []     # 空的，只生成公司
    }

    print("开始研究...")
    result = researcher.research_single("bytedance", config)

    print(f"\n结果:")
    print(f"  成功: {result['success']}")
    print(f"  完成: {result['completed']}/{result['total']}")

    if result['success']:
        print(f"  生成的文件:")
        for entity_id, files in result['results'].items():
            for f in files:
                print(f"    - {f['file_path']}")

                # 读取并显示前100字符
                try:
                    with open(f['file_path'], "r", encoding="utf-8") as file:
                        content = file.read()
                    print(f"    内容长度: {len(content)} 字符")
                    print(f"    前100字符: {content[:100]}")
                except Exception as e:
                    print(f"    读取失败: {e}")
    else:
        print(f"  错误: {result['errors']}")

    print("\n✓ 步骤7 完成\n")
    return result

if __name__ == "__main__":
    # 设置环境变量，避免编码问题
    os.environ['PYTHONIOENCODING'] = 'utf-8'

    step_1_check_yaml()
    step_2_parse_data()
    step_3_check_query_template()
    # step_4_test_queryer()  # 跳过，避免实际API调用
    step_5_test_render()
    step_6_test_saver()
    # step_7_full_pipeline()  # 跳过，避免实际API调用

    print("=" * 60)
    print("逐步测试完成！")
    print("=" * 60)