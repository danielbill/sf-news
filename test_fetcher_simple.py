#!/usr/bin/env python
"""简单测试 Fetcher 是否能返回内容"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))
import src  # 触发编码设置

from tools.fetcher import Fetcher

def test_fetcher():
    """测试 Fetcher.fetch() 是否能返回内容"""
    print("=" * 60)
    print("测试 Fetcher.fetch()")
    print("=" * 60)

    # 测试 1: 简单的查询（应该能工作）
    print("\n1. 测试简单查询: '字节跳动'")
    result = Fetcher.fetch("字节跳动", max_results=3)

    print(f"成功: {result['success']}")
    print(f"错误: {result['error']}")
    print(f"内容长度: {len(result['content'])}")
    if result['success'] and result['content']:
        print(f"前200字符: {result['content'][:200]}")
    elif result['content']:
        print(f"实际内容: {repr(result['content'][:100])}")

    # 测试 2: 带 instruction 的查询
    print("\n2. 测试带 instruction 的查询")
    instruction = "请按 Markdown 格式输出以下信息："
    result2 = Fetcher.fetch("字节跳动", instruction=instruction, max_results=3)

    print(f"成功: {result2['success']}")
    print(f"错误: {result2['error']}")
    print(f"内容长度: {len(result2['content'])}")
    if result2['success'] and result2['content']:
        print(f"前200字符: {result2['content'][:200]}")

    # 测试 3: 尝试调试 subprocess 调用
    print("\n3. 测试 subprocess 直接调用")
    cmd = [
        "D:/workspace/cybcortex/.venv/Scripts/python.exe",
        "D:/workspace/cybcortex/1技能库/py_code/gather/search/semantic_search.py",
        "字节跳动",
        "--max-results", "3",
        "--recency", "year"
    ]
    print(f"命令: {' '.join(cmd)}")

if __name__ == "__main__":
    test_fetcher()