"""新闻抓取 API

使用通用爬虫框架 + 三层去重策略
"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException

from ..config import ConfigReader
from ..crawlers.dedup import TextDeduplicator
from ..crawlers.universal import UniversalCrawler
from ..models import Article
from ..storage import TimelineDB

router = APIRouter(prefix="/api/crawl", tags=["crawl"])

# 内存中保存最后刷新时间
_last_crawl_time: Optional[datetime] = None
# 最小抓取间隔（秒）
MIN_CRAWL_INTERVAL = 30  # 30秒


async def run_crawl(source_id: str = None) -> Dict[str, Any]:
    """执行抓取任务

    使用通用爬虫框架，支持动态加载解析器。

    流程：
    1. 并发抓取所有启用的新闻源
    2. 三层去重（时间、URL、标题相似度）
    3. 统一入库

    Args:
        source_id: 指定新闻源ID，None表示抓取所有启用的源

    Returns:
        抓取结果统计
    """
    # 加载配置
    reader = ConfigReader()
    sources_config = reader.load_news_sources_config()

    # 获取启用的新闻源
    enabled_sources = [s for s in sources_config.sources if s.enabled]
    if source_id:
        enabled_sources = [s for s in enabled_sources if s.id == source_id]

    # 统计数据
    all_articles: List[Article] = []
    source_results = []

    # 遍历新闻源执行抓取
    for source in enabled_sources:
        crawler = None
        try:
            print(f"[Crawl] 开始抓取: {source.name} ({source.id})")
            crawler = UniversalCrawler(source)

            # 抓取文章（已包含关键词过滤）
            articles = await crawler.fetch()

            source_results.append(
                {
                    "source": source.name,
                    "id": source.id,
                    "fetched": len(articles),
                    "status": "success",
                }
            )

            all_articles.extend(articles)
            print(f"[Crawl] {source.name}: 抓取 {len(articles)} 条")
            # 打印每篇文章的详细信息
            for art in articles:
                print(f"  - {art.title[:40]}... | {art.timestamp} | {art.url[:50]}...")

        except ImportError as e:
            print(f"[Crawl] 解析器不存在: {source.id} - {e}")
            source_results.append(
                {
                    "source": source.name,
                    "id": source.id,
                    "status": "error",
                    "error": f"解析器不存在: {str(e)}",
                }
            )

        except Exception as e:
            import traceback

            print(f"[Crawl] 抓取失败: {source.name} - {e}")
            traceback.print_exc()
            source_results.append(
                {"source": source.name, "id": source.id, "status": "error", "error": str(e)}
            )

        finally:
            if crawler:
                await crawler.close()

    print(f"[Crawl] 总抓取: {len(all_articles)} 条")

    # 三层去重
    original_count = len(all_articles)
    if all_articles:
        deduplicator = TextDeduplicator()
        deduped_articles = deduplicator.dedup(all_articles)
        print(f"[Crawl] 去重: {original_count} -> {len(deduped_articles)} 条")
    else:
        deduped_articles = []

    # 统一入库
    saved_count = 0
    db = TimelineDB(date.today())
    db.init_db()

    # 读取存储配置
    crawler_config = reader.load_crawler_config()
    save_content = crawler_config.storage.save_content

    for article in deduped_articles:
        try:
            # 检查是否已存在
            if not db.article_exists(article.url):
                print(f"[Crawl] 准备入库: {article.title[:40]}..., content={'有' if article.content else '无'}")

                # 保存正文文件
                if save_content and article.content:
                    from pathlib import Path

                    # 生成文件路径: data/articles/YYYY/MM/DD/标题.md
                    article_date = (
                        article.timestamp.date()
                        if hasattr(article.timestamp, 'date')
                        else date.today()
                    )
                    filename = (
                        article.title[:50]
                        .replace('/', '-')
                        .replace('\\', '-')
                        .replace(':', '-')
                        .replace('*', '-')
                        .replace('?', '-')
                        .replace('"', '-')
                        .replace('<', '-')
                        .replace('>', '-')
                        .replace('|', '-')
                    )
                    filename = filename.strip()
                    file_dir = Path(f"data/articles/{article_date.strftime('%Y/%m/%d')}")
                    file_dir.mkdir(parents=True, exist_ok=True)
                    file_path = file_dir / f"{filename}.md"

                    # 写入正文
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(f"# {article.title}\n\n")
                        f.write(f"> 来源: {article.source}\n")
                        f.write(f"> 时间: {article.timestamp}\n")
                        f.write(f"> URL: {article.url}\n\n")
                        f.write(article.content)

                    article.file_path = str(file_path)

                db.insert_article(article)
                saved_count += 1
        except Exception as e:
            print(f"[Crawl] 入库失败: {article.title} - {e}")

    print(f"[Crawl] 入库: {saved_count} 条")

    return {
        "total_fetched": original_count,
        "after_dedup": len(deduped_articles),
        "total_saved": saved_count,
        "sources": source_results,
    }


@router.post("/trigger")
async def trigger_crawl(source_id: str = None, force: bool = False) -> Dict[str, Any]:
    """手动触发抓取

    Args:
        source_id: 可选，指定抓取的新闻源ID
        force: 是否强制跳过频率限制（默认否）

    Returns:
        抓取结果统计
    """
    global _last_crawl_time

    # 检查抓取频率（除非强制）
    if not force and _last_crawl_time:
        elapsed = (datetime.now() - _last_crawl_time).total_seconds()
        if elapsed < MIN_CRAWL_INTERVAL:
            remaining = int(MIN_CRAWL_INTERVAL - elapsed)
            return {
                "code": 429,
                "message": f"刷新过于频繁，请等待 {remaining} 秒后再试",
                "data": {
                    "last_crawl_time": _last_crawl_time.isoformat(),
                    "remaining_seconds": remaining,
                },
            }

    try:
        result = await run_crawl(source_id)

        # 更新最后刷新时间
        _last_crawl_time = datetime.now()

        if result["total_saved"] == 0:
            return {
                "code": 200,
                "message": "抓取完成，但未找到符合条件的新闻或新闻已存在",
                "data": result,
            }

        return {
            "code": 200,
            "message": f"成功抓取并保存 {result['total_saved']} 条新闻",
            "data": result,
        }

    except Exception as e:
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"抓取失败: {str(e)}")


@router.get("/status")
async def get_crawl_status() -> Dict[str, Any]:
    """获取抓取状态"""
    from datetime import date

    db = TimelineDB(date.today())
    db.init_db()
    articles = db.list_articles(limit=1000)

    return {
        "code": 200,
        "message": "success",
        "data": {
            "today_count": len(articles),
            "date": date.today().isoformat(),
            "last_crawl_time": _last_crawl_time.isoformat() if _last_crawl_time else None,
        },
    }


@router.get("/cache")
async def get_cache_status() -> Dict[str, Any]:
    """获取内存缓存状态"""
    from ..crawlers.url_cache import url_cache

    return {
        "code": 200,
        "message": "success",
        "data": {"cache_date": str(url_cache.cache_date), "url_count": url_cache.count},
    }


@router.post("/cache/clear")
async def clear_cache() -> Dict[str, Any]:
    """清空内存缓存"""
    from ..crawlers.url_cache import url_cache

    url_cache.clear()

    return {
        "code": 200,
        "message": "缓存已清空",
        "data": {"cache_date": str(url_cache.cache_date), "url_count": url_cache.count},
    }
