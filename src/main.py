"""FastAPI 应用入口"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from datetime import date
from pathlib import Path

from .storage import TimelineDB
from .api.crawl import router as crawl_router
from .api import scheduler as scheduler_api
from .scheduler import SchedulerManager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 初始化今日数据库
    db = TimelineDB(date.today())
    db.init_db()

    # 初始化并启动调度器
    scheduler = SchedulerManager(config_dir="config")
    scheduler_api.set_scheduler(scheduler)
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
app.include_router(scheduler_api.router)


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


@app.get("/api/articles")
async def list_articles(limit: int = 100, offset: int = 0):
    """获取文章列表"""
    db = TimelineDB()
    articles = db.list_articles(limit=limit, offset=offset)
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
