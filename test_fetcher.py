#!/usr/bin/env python
"""测试 Fetcher 是否能正确调用 semantic_search.py"""

import sys
from pathlib import Path

# 添加 src 目录到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from tools.fetcher import Fetcher

def test_fetcher():
    """测试 Fetcher 基本功能"""
    print("=" * 60)
    print("测试 Fetcher 调用 semantic_search.py")
    print("=" * 60)

    # 测试一个简单的查询
    query = "字节跳动 公司介绍"

    print(f"\n执行查询: {query}")
    result = Fetcher.fetch(query, max_results=5)

    print(f"\n结果:")
    print(f"  成功: {result['success']}")
    print(f"  错误: {result['error'] or '无'}")

    if result["success"]:
        content = result["content"]
        print(f"  内容长度: {len(content)} 字符")
        print(f"  内容预览 (前200字符): {content[:200]}...")
    else:
        print(f"  详细错误信息: {result['error']}")

    return result

if __name__ == "__main__":
    test_fetcher()