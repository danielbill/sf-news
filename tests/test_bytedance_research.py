"""测试字节跳动 AI 档案生成

调用 NovaSyncService 同步 nova.yaml，生成字节跳动档案
"""

import sys
import os
from pathlib import Path

# 添加 src 目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from services.legend_sync import NovaSyncService


def test_bytedance_research():
    """测试字节跳动档案生成"""
    print("=" * 60)
    print("测试字节跳动 AI 档案生成")
    print("=" * 60)

    # 清理数据库中的 bytedance 记录（强制触发 AI 采集）
    db_path = Path("data/db/legend.sqlite")
    if db_path.exists():
        import sqlite3
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM legends WHERE id = ?", ("bytedance",))
        conn.commit()
        conn.close()
        print("已清理数据库中的 bytedance 记录")

    # 创建 Nova 同步服务
    nova_sync = NovaSyncService()

    # 执行同步（包含 AI 采集）
    print("\n开始同步 nova.yaml...")
    result = nova_sync.sync(auto_fetch=True)

    print(f"\n同步结果:")
    print(f"  - 有变化: {result.has_changes}")
    print(f"  - 新增: {result.added}")
    print(f"  - 移除: {result.removed}")
    print(f"  - 更新: {result.keywords_updated}")
    print(f"  - 未变: {result.unchanged}")
    print(f"  - 同步时间: {result.synced_at}")

    # 检查生成的文件
    print("\n检查生成的档案文件:")
    nova_dir = Path("data/nova/company")
    if nova_dir.exists():
        for md_file in nova_dir.glob("*.md"):
            print(f"  [OK] {md_file}")
            # 读取前几行预览
            content = md_file.read_text(encoding="utf-8")
            lines = content.split("\n")[:5]
            print(f"    预览: {lines[0]}")
    else:
        print(f"  [X] 目录不存在: {nova_dir}")

    return result


if __name__ == "__main__":
    test_bytedance_research()
