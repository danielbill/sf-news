"""FastAPI 应用入口"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from datetime import datetime, timedelta, timezone, date
from pathlib import Path

from .storage import TimelineDB
from .api.crawl import router as crawl_router
from .api.admin import router as admin_router
from .api.biz import router as biz_router
from .scheduler import SchedulerManager
from .crawlers.dedup import today_news_cache


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 初始化今日数据库
    db = TimelineDB(date.today())
    db.init_db()

    # 从数据库加载缓存（防止重启后重复抓取）
    today_news_cache.init_from_db(db, limit=100)

    # 初始化并启动调度器
    scheduler = SchedulerManager(config_dir="config")
    await scheduler.start()

    yield

    # 清理资源
    await scheduler.close()


app = FastAPI(
    title="Singularity Front API",
    description="文明前沿雷达系统",
    version="0.1.0",
    lifespan=lifespan
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境需限制
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件
static_dir = Path("static")
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# 注册 API 路由
app.include_router(crawl_router)
app.include_router(admin_router)
app.include_router(biz_router)


@app.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request):
    """后台管理页面"""
    admin_file = Path("templates/admin.html")
    if admin_file.exists():
        with open(admin_file, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Admin page not found</h1>", status_code=404)


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """根路径 - 返回首页"""
    templates_dir = Path("templates")
    index_file = templates_dir / "index.html"

    if index_file.exists():
        with open(index_file, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    else:
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Singularity Front</title>
            <meta charset="utf-8">
        </head>
        <body>
            <h1>Singularity Front - 文明前沿雷达系统</h1>
            <p>模板文件不存在，请先创建 templates/index.html</p>
            <p><a href="/docs">查看 API 文档</a></p>
        </body>
        </html>
        """)


@app.get("/health")
async def health():
    """健康检查"""
    return {"status": "healthy"}


@app.get("/api/articles/today")
async def list_articles_today(limit: int = 100, legend: str = None):
    """获取今日及以后的新闻"""
    # 使用北京时间（UTC+8）获取今日日期
    beijing_tz = timezone(timedelta(hours=8))
    today = datetime.now(beijing_tz).date().isoformat()
    db = TimelineDB()
    articles = db.list_articles(limit=limit, legend=legend, start_date=today)
    return {
        "code": 200,
        "message": "success",
        "data": articles,
        "total": len(articles)
    }


@app.get("/api/articles/latest")
async def list_articles_latest(limit: int = 100, legend: str = None):
    """获取最新新闻（不限日期）"""
    db = TimelineDB()
    articles = db.list_articles_latest(limit=limit, legend=legend)
    return {
        "code": 200,
        "message": "success",
        "data": articles,
        "total": len(articles)
    }


@app.get("/api/articles")
async def list_articles(limit: int = 100, years: int = 1, legend: str = None,
                       start_date: str = None, end_date: str = None):
    """获取文章列表（高级查询）

    Args:
        limit: 返回条数
        years: 查询最近几年（默认 1 年）
        legend: 筛选传奇人物
        start_date: 开始日期 YYYY-MM-DD（可选）
        end_date: 结束日期 YYYY-MM-DD（可选）
    """
    if years == 1:
        db = TimelineDB()
        articles = db.list_articles(limit=limit, legend=legend, start_date=start_date, end_date=end_date)
    else:
        articles = TimelineDB.list_articles_multi_year(years=years, limit=limit, legend=legend,
                                                         start_date=start_date, end_date=end_date)
    return {
        "code": 200,
        "message": "success",
        "data": articles,
        "total": len(articles)
    }


@app.get("/api/articles/{article_id}")
async def get_article(article_id: str):
    """获取文章详情"""
    db = TimelineDB()
    article = db.get_article(article_id)
    if not article:
        return {
            "code": 404,
            "message": "Article not found",
            "data": None
        }
    return {
        "code": 200,
        "message": "success",
        "data": article
    }
