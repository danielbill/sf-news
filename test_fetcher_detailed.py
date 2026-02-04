#!/usr/bin/env python
"""测试 Fetcher 详细调试"""

import sys
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from tools.fetcher import Fetcher

def test_fetcher_detailed():
    """详细测试 Fetcher"""
    print("=" * 60)
    print("详细测试 Fetcher")
    print("=" * 60)

    # 手动测试 subprocess 调用
    print("\n1. 直接测试 subprocess 调用...")
    cmd = [
        Fetcher.CYBCORTEX_PYTHON,
        Fetcher.SEARCH_SCRIPT,
        "字节跳动",
        "--max-results", "3",
        "--recency", "year"
    ]

    print(f"命令: {' '.join(cmd)}")

    try:
        # 先测试简短超时
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )

        print(f"\n返回码: {result.returncode}")
        print(f"标准输出长度: {len(result.stdout)}")
        print(f"标准错误长度: {len(result.stderr)}")

        if result.returncode != 0:
            print(f"\n标准错误内容 (前500字符):")
            print(result.stderr[:500])
        else:
            print(f"\n标准输出内容 (前200字符):")
            print(result.stdout[:200])

    except subprocess.TimeoutExpired:
        print("\n超时!")
    except Exception as e:
        print(f"\n异常: {e}")

    print("\n" + "=" * 60)
    print("2. 使用 Fetcher.fetch() 测试...")

    result = Fetcher.fetch("字节跳动", max_results=3)

    print(f"成功: {result['success']}")
    if not result['success']:
        print(f"错误: {result['error']}")
    else:
        print(f"内容长度: {len(result['content'])} 字符")
        print(f"内容预览 (前200字符):")
        print(result['content'][:200])

if __name__ == "__main__":
    test_fetcher_detailed()