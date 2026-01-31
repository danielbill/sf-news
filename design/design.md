# Singularity Front 设计方案

## 项目概述

**Singularity Front** 是一个"文明前沿雷达系统"，目标是实时追踪奇点人物及其生态系统的所有动态，理解文明前沿正在发生什么。

### 核心理念
- **Singularity** = 能够引发文明级跃迁的"伟人"（马斯克、黄仁勋、Sam Altman 等）
- **Front** = 由奇点人物引发的整个文明冲击波（公司、战略、技术、供应链、资本流向）
- **目标** = 建立一个"文明级趋势的感知系统"

---

## MVP 范围

### 追踪对象
- **首要目标**：埃隆·马斯克（单一奇点人物）

### 信息维度
1. 人物动态（言论、访谈、社交动态）
2. 公司层面（战略、财报、技术路线）
3. 产业生态（竞争格局、供应链、合作伙伴）
4. 资本市场（投资并购、资本开支、资本流向）

### 数据源策略

### 模块化架构

```
┌─────────────────────────────────────────────────────────────┐
│                     Singularity Front                        │
├──────────────┬──────────────┬──────────────┬─────────────────┤
│  新闻抓取模块  │  财报数据模块  │  公司档案模块  │   关联分析模块   │
├──────────────┼──────────────┼──────────────┼─────────────────┤
│ 参考 newsnow  │ 专业财经 API  │ 手动维护     │ 后期实现        │
│ Python 重写   │ 独立数据源    │ AI 辅助      │ 智能关联        │
└──────────────┴──────────────┴──────────────┴─────────────────┘
```

### 1. 新闻抓取模块（参考 newsnow）

**目的**：获取奇点人物/公司相关的新闻动态

**参考项目**：`D:\awesome_projects\newsnow`
- 参考 API 调用方式
- 参考反爬策略
- 用 Python 重写核心逻辑

#### 官媒/权威媒体（优先使用）

| 来源     | 类型 | API/URL                                                           | 说明                    |
| -------- | ---- | ----------------------------------------------------------------- | ----------------------- |
| 参考消息 | 官媒 | `https://china.cankaoxiaoxi.com/json/channel/{channel}/list.json` | 新华社主办，有 JSON API |
| 澎湃新闻 | 权威 | `https://cache.thepaper.cn/contentapi/wwwIndex/rightSidebar`      | 上海报业集团            |
| 腾讯新闻 | 门户 | `https://i.news.qq.com/web_backend/v2/getTagInfo?tagId=xxx`       | 综合早报                |
| 凤凰网   | 门户 | `https://www.ifeng.com/` (页面数据)                               | 热点新闻                |

#### 财经/科技媒体

| 来源       | 类型 | API/URL                                                 | 说明     |
| ---------- | ---- | ------------------------------------------------------- | -------- |
| 华尔街见闻 | 财经 | `https://api-one.wallstcn.com/apiv1/content/lives`      | 实时快讯 |
| 金十数据   | 财经 | `https://www.jin10.com/flash_newest.js`                 | 财经快讯 |
| 36氪       | 科技 | `https://www.36kr.com/newsflashes`                      | 科创快讯 |
| 格隆汇     | 财经 | `https://www.gelonghui.com/news/`                       | 港股财经 |
| 雪球       | 财经 | `https://stock.xueqiu.com/v5/stock/hot_stock/list.json` | 热门股票 |
| Fastbull   | 财经 | `https://www.fastbull.com/cn/express-news`              | 财经快讯 |

#### MVP 新闻数据源选择

**第一阶段（验证）**：
1. 参考消息（官媒 API，结构化数据）
2. 澎湃新闻（权威媒体，API 可用）
3. 36氪（科技媒体，马斯克/特斯拉相关）

**第二阶段（扩展）**：
- 华尔街见闻、金十数据（财经维度）
- 虎嗅、格隆汇（深度分析）

**已实现解析器（2026-01-28）**：
- `parsers/cankaoxiaoxi.py` - 参考消息
- `parsers/thepaper.py` - 澎湃新闻
- `parsers/_36kr.py` - 36氪
- `parsers/ifeng.py` - 凤凰网
- `parsers/toutiao.py` - 今日头条
- `parsers/wallstreetcn_live.py` - 华尔街见闻快讯
- `parsers/wallstreetcn_news.py` - 华尔街见闻资讯
- `parsers/cls_telegraph.py` - 财联社电报
- `parsers/cls_depth.py` - 财联社深度（需签名，暂时禁用）

### 已实现管理功能（2026-01-28）
- **新闻源测试** - `/admin/source_test` - 测试所有新闻源连接状态和数据返回量
- **清空今日数据** - `/admin/cleartodaynews` - 清空今日数据库记录、文章文件和内存缓存

---

### 2. 财报数据模块（独立系统）

**目的**：获取公司财报、财务指标

**数据源**：专业财经 API（待定）
- 这是独立的数据源
- 与新闻抓取模块完全分离
- 提供结构化的财务数据

---

### 3. 公司档案模块（独立系统）

**目的**：维护奇点人物/公司/供应商的元数据

**数据来源**：
- 手动维护核心档案
- AI 辅助补充信息
- 从新闻中提取实体关联

---

## 技术架构

### 技术栈
| 层级     | 技术选择            |
| -------- | ------------------- |
| 编程语言 | Python              |
| 爬虫框架 | Scrapy / Playwright |
| Web 框架 | FastAPI             |
| 数据库   | SQLite              |
| 任务调度 | APScheduler         |

---

## 存储架构设计

### 目录结构

```
data/
├── db/                           # SQLite 数据库（元数据）
│   ├── timeline_2025-01-28.sqlite
│   ├── timeline_2025-01-29.sqlite
│   └── ...
├── articles/                     # 文章正文
│   └── 2025/
│       └── 01/
│           ├── 28/
│           │   ├── {uuid}.md
│           │   └── {uuid}.md
├── financial/                    # 财报数据（结构化）
│   └── 2025/
│       └── 01/
└── companies/                    # 公司/供应商档案
    └── meta.sqlite              # 固定不变的公司元数据
```

### 存储策略：Timeline + 元数据/文件分离

**一天一个 DB**：
- 每天生成独立的 SQLite 文件：`timeline_YYYY-MM-DD.sqlite`
- 优点：天然时间分区、备份方便、并发友好、数据量可控

**元数据 + 文件分离**：
- **SQLite 存储**：元数据（id, title, url, source, timestamp, tags, entities, file_path）
- **文件系统存储**：正文内容（.md 格式）
- 优点：数据库轻量、文章可直接用笔记软件打开、备份灵活

---

## 数据库表结构

### 每日 Timeline DB

```sql
-- ============================================
-- 表：articles（文章元数据）
-- ============================================
CREATE TABLE articles (
    id        TEXT PRIMARY KEY,    -- UUID
    title     TEXT NOT NULL,       -- 文章标题
    url       TEXT UNIQUE,         -- 原始链接
    source    TEXT,                -- 来源：新华社、财新等
    timestamp DATETIME,            -- 发布时间
    file_path TEXT,                -- articles/2025/01/28/{uuid}.md
    tags      TEXT,                -- JSON: ["马斯克", "特斯拉", "光伏"]
    entities  TEXT                 -- JSON: 提取的公司/人物实体
);

-- ============================================
-- 表：financial（财报元数据）
-- ============================================
CREATE TABLE financial (
    id        TEXT PRIMARY KEY,
    company_id TEXT,
    report_type TEXT,              -- Q1/Q2/Q3/Q4/年报
    year      INTEGER,
    file_path TEXT,                -- financial/2025/01/TSLA_Q4_2024.pdf
    timestamp DATETIME,
    UNIQUE(company_id, report_type, year)
);
```

### 公司元数据 DB（固定）

```sql
-- ============================================
-- 文件：companies/meta.sqlite
-- ============================================

-- 表：companies（公司档案）
CREATE TABLE companies (
    id        TEXT PRIMARY KEY,    -- 公司 ID：TSLA, NVDA
    name      TEXT NOT NULL,       -- 公司名称
    name_cn   TEXT,                -- 中文名称
    type      TEXT,                -- 类型：奇点公司/一级供应商/二级供应商
    tier      TEXT,                -- 层级：1/2/3
    parent_id TEXT,                -- 所属奇点公司
    description TEXT,              -- 公司描述
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 表：people（人物档案）
CREATE TABLE people (
    id        TEXT PRIMARY KEY,    -- 人物 ID：musk, huang
    name      TEXT NOT NULL,       -- 姓名
    name_cn   TEXT,                -- 中文姓名
    company_id TEXT,               -- 所属公司
    role      TEXT,                -- 角色：CEO/CTO/创始人
    tier      TEXT,                -- 奇点人物/准奇点人物
    description TEXT,              -- 人物描述
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 表：relations（实体关联）
CREATE TABLE relations (
    id        TEXT PRIMARY KEY,
    from_type TEXT,                -- company/person
    from_id   TEXT,
    to_type   TEXT,
    to_id     TEXT,
    relation_type TEXT,            -- supplier/customer/partner/competitor
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

## 核心功能模块

### 1. 官媒新闻爬虫
- 从国内官媒抓取keywords相关新闻
- 支持多个来源
- 提取文章元数据和正文
- 自动生成标签和实体关联
- 新闻抓取逻辑如下：
    - 预设每小时从各新闻源抓取一次数据，自动抓取最小间隔15分钟，手动刷新最小间隔30秒
    - 只抓取当日新闻
    - 内存保存抓取新闻的url 和 title，进行排重
    - 每次从各个新闻源抓取限制为20条，该值可设置
    - 排重流程：
        1、当日新闻，时间排重
        2、url排重，已存在内存中的丢弃
        3、title排重，已存在内存中的丢弃，使用近似算法排重，得到新增新闻
        4、对新增新闻再进行title排重（本批次文章互相去重）
        5、最后使用keywords筛选本次新增新闻
        
    

### 2. 财报数据抓取
- 通过财经 API 获取美股财报数据
- 解析关键指标（营收、利润、现金流等）
- 存储财报元数据和原始文件

### 3. 公司档案管理
- 维护奇点人物/公司/供应商的元数据
- 管理实体之间的关联关系
- 支持档案的增删改查

### 4. 定时任务调度
- 每小时自动抓取最新新闻
- 每日更新财报数据
- 任务状态监控和错误处理

---

## 用户使用场景

```
用户流程：
1. 打开 Web 界面，看到时间线上的最新动态
2. 看到一条："马斯克宣布百济光伏建设计划"
3. 点击相关链接 → 查看一级供应商信息
4. 继续点击 → 查看该供应商过去一年的：
   - 财报表现
   - 订单跟踪情况
   - 相关新闻历史
```

这是一个**图谱式/关联式**的阅读体验，不是简单的时间线。


---

## 待确认事项

3. **数据关联**：智能关联方案后续讨论
4. **全文搜索**：是否需要 FTS5 或外部搜索引擎

---

## 更新记录

- 2025-01-28：初始设计，确定存储架构和技术栈
- 2026-01-28：完成 7 个新闻源解析器实现
- 2026-01-28：完成新闻源测试功能、清空今日数据功能
- 2026-01-28：关键词配置优化（数组格式修正、误匹配修复）

