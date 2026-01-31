"""爬虫 CLI 入口

独立运行爬虫，无需 FastAPI 服务。
"""

import asyncio
import sys

from src.api.crawl import run_crawl


async def main():
    """运行爬虫（独立 CLI 入口）"""
    result = await run_crawl()

    # 打印结果摘要
    print(f"\n抓取完成:")
    print(f"  - 原始抓取: {result['total_fetched']} 条")
    print(f"  - 去重后: {result['after_dedup']} 条")
    print(f"  - 新增入库: {result['total_saved']} 条")

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
