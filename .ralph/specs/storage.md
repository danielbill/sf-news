# 存储模块技术规格

## 目录结构

```
data/
├── db/                           # SQLite 数据库（元数据）
│   ├── timeline_YYYY-MM-DD.sqlite
│   └── ...
├── articles/                     # 文章正文
│   └── YYYY/
│       └── MM/
│           └── DD/
│               └── {uuid}.md
├── financial/                    # 财报数据
│   └── YYYY/
│       └── MM/
└── companies/                    # 公司档案
    └── meta.sqlite
```

## Timeline DB Schema

### articles 表

```sql
CREATE TABLE articles (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    url TEXT UNIQUE,
    source TEXT NOT NULL,
    timestamp DATETIME NOT NULL,
    file_path TEXT NOT NULL,
    tags TEXT,                    -- JSON array
    entities TEXT,                -- JSON array
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_articles_timestamp ON articles(timestamp);
CREATE INDEX idx_articles_source ON articles(source);
```

## Meta DB Schema

### companies 表

```sql
CREATE TABLE companies (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    name_cn TEXT,
    type TEXT,                    -- singularity/tier1/tier2
    tier INTEGER,
    parent_id TEXT,
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### people 表

```sql
CREATE TABLE people (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    name_cn TEXT,
    company_id TEXT,
    role TEXT,
    tier TEXT,                    -- singularity/quasi
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### relations 表

```sql
CREATE TABLE relations (
    id TEXT PRIMARY KEY,
    from_type TEXT NOT NULL,      -- company/person
    from_id TEXT NOT NULL,
    to_type TEXT NOT NULL,
    to_id TEXT NOT NULL,
    relation_type TEXT NOT NULL,  -- supplier/customer/partner
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(from_type, from_id, to_type, to_id, relation_type)
);
```

## 文章文件格式

```markdown
---
title: 文章标题
source: 来源
url: 原始链接
timestamp: 2025-01-28T10:00:00Z
tags: ["马斯克", "特斯拉"]
---

# 文章正文

正文内容...
```

## 数据库操作接口

```python
from datetime import date
from pathlib import Path
import sqlite3
from typing import Optional

class TimelineDB:
    def __init__(self, db_date: date):
        self.db_path = f"data/db/timeline_{db_date.strftime('%Y-%m-%d')}.sqlite"

    def connect(self) -> sqlite3.Connection:
        """获取数据库连接"""
        pass

    def init_db(self) -> None:
        """初始化数据库表结构"""
        pass

    def insert_article(self, article: Article) -> None:
        """插入文章"""
        pass

    def get_article(self, article_id: str) -> Optional[Article]:
        """获取单篇文章"""
        pass

    def list_articles(self, limit: int = 100, offset: int = 0) -> List[Article]:
        """列出文章"""
        pass

    def search_articles(self, keyword: str) -> List[Article]:
        """搜索文章"""
        pass
```

## 生命周期管理

1. **创建**：每日首次写入时自动创建当日 DB
2. **归档**：超过 90 天的 DB 自动归档到 `data/archive/db/`
3. **清理**：超过 2 年的数据按重要度选择性删除
