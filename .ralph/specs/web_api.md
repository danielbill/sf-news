# Web API 技术规格

## 技术栈

- **框架**: FastAPI
- **版本**: 0.100+
- **Python**: 3.11+

## API 结构

```
src/
├── main.py              # FastAPI 应用入口
├── api/
│   ├── __init__.py
│   ├── articles.py      # 文章相关 API
│   ├── companies.py     # 公司档案 API
│   ├── scheduler.py     # 调度器 API
│   └── financial.py     # 财报数据 API
├── models/
│   ├── __init__.py
│   ├── article.py       # Pydantic 模型
│   ├── company.py
│   └── response.py      # 统一响应格式
└── services/
    ├── __init__.py
    ├── article_service.py
    └── company_service.py
```

## 统一响应格式

```python
from pydantic import BaseModel
from typing import Optional, Generic, TypeVar

T = TypeVar('T')

class ApiResponse(BaseModel, Generic[T]):
    code: int = 200
    message: str = "success"
    data: Optional[T] = None

class PaginatedResponse(ApiResponse[T]):
    total: int
    page: int
    page_size: int
```

## 文章 API

### GET /api/articles

获取文章列表（分页）

**Query Parameters**:
- `page`: int = 1
- `page_size`: int = 20
- `source`: Optional[str] = None
- `start_date`: Optional[date] = None
- `end_date`: Optional[date] = None

**Response**:
```json
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "id": "uuid",
      "title": "文章标题",
      "source": "cankaoxiaoxi",
      "timestamp": "2025-01-28T10:00:00Z",
      "tags": ["马斯克", "特斯拉"]
    }
  ],
  "total": 1000,
  "page": 1,
  "page_size": 20
}
```

### GET /api/articles/{id}

获取文章详情

**Response**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": "uuid",
    "title": "文章标题",
    "url": "原始链接",
    "source": "cankaoxiaoxi",
    "timestamp": "2025-01-28T10:00:00Z",
    "content": "# 文章正文\n\n...",
    "tags": ["马斯克", "特斯拉"],
    "entities": ["TSLA", "SpaceX"]
  }
}
```

### GET /api/articles/search

全文搜索文章

**Query Parameters**:
- `q`: str - 搜索关键词
- `page`: int = 1
- `page_size`: int = 20

## 公司档案 API

### GET /api/companies

获取公司列表

**Query Parameters**:
- `type`: Optional[str] = None - singularity/tier1/tier2
- `page`: int = 1
- `page_size`: int = 20

### GET /api/companies/{id}

获取公司详情（含相关人物、关联公司）

## 调度器 API

### GET /api/scheduler/status

获取调度器状态

**Response**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "running": true,
    "last_run": "2025-01-28T10:00:00Z",
    "next_run": "2025-01-28T11:00:00Z",
    "jobs": [
      {
        "name": "news_crawler",
        "last_status": "success",
        "last_run": "2025-01-28T10:00:00Z"
      }
    ]
  }
}
```

### POST /api/scheduler/trigger

手动触发抓取任务

## CORS 配置

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # 前端地址
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 错误处理

```python
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "code": 500,
            "message": str(exc),
            "data": None
        }
    )
```
