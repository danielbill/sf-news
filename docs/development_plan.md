# Singularity Front 完整开发计划

## 项目概述

**Singularity Front** 是一个"文明前沿雷达系统"，目标是实时追踪奇点人物（Legend）及其生态系统（Front）的所有动态。

### 核心理念
- **Legend** = 能够引发文明级跃迁的"伟人"（马斯克、黄仁勋、Sam Altman 等）
- **Front** = 由奇点人物引发的整个文明冲击波（公司、战略、技术、供应链、资本流向）
- **目标** = 建立一个"文明级趋势的感知系统"

---

## 技术架构

### 技术栈
| 层级 | 技术选择 |
|------|----------|
| 编程语言 | Python 3.11+ |
| Web 框架 | FastAPI |
| 爬虫框架 | httpx + BeautifulSoup4 |
| 数据库 | SQLite |
| 任务调度 | APScheduler |
| 配置格式 | YAML |

### 目录结构

```
singularity-front/
├── config/                    # 配置文件
│   ├── legend.yaml           # 奇点人物档案
│   ├── company.yaml          # 公司档案
│   ├── news_keywords.yaml    # 新闻筛选关键词
│   ├── news_sources.yaml     # 新闻源配置
│   └── crawler_config.yaml   # 抓取配置
├── src/                       # 源代码
│   ├── models/               # 数据模型
│   ├── crawlers/             # 爬虫模块
│   ├── storage/              # 存储模块
│   ├── config/               # 配置读取
│   ├── api/                  # API 路由
│   └── main.py               # 应用入口
├── tests/                     # 测试
├── data/                      # 运行时数据
│   ├── db/                   # SQLite 数据库
│   ├── articles/             # 文章正文
│   └── companies/            # 公司元数据
├── static/                    # 静态文件（前端）
├── templates/                 # HTML 模板
└── .ralph/                    # Ralph 配置
```

---

## 开发阶段规划

### 阶段 0：基础设施 ✅ (已完成)
- [x] 项目结构搭建
- [x] 依赖安装
- [x] 配置文件系统（5 个 YAML + 读取模块）
- [x] 测试通过 (8 passed)

### 阶段 1：快速迭代 Demo ✅ (已完成)
- [x] 修复 `src/crawlers/base.py` - 集成配置关键词
- [x] 完善 `src/crawlers/cankaoxiaoxi.py` - 集成配置读取
- [x] 实现爬虫存储功能 - save_article() 方法
- [x] 创建 `src/api/crawl.py` - POST /api/crawl/trigger
- [x] 创建 `templates/index.html` - 立即抓取按钮+新闻列表
- [x] 集成测试验证 - 17 passed

### 阶段 2：通用爬虫框架 ✅ (已完成)
- [x] 创建 `src/crawlers/universal.py` - 通用爬虫
- [x] 创建 `src/crawlers/parsers/` - 解析器目录
- [x] 创建 `src/crawlers/dedup.py` - 三层去重（时间/URL/SimHash）
- [x] 创建 `src/crawlers/url_cache.py` - 内存URL缓存（每日清零）
- [x] 重构 `src/api/crawl.py` - 集成通用爬虫
- [x] 更新 `config/news_sources.yaml` - 移除parser字段
- [x] 实现 9 个新闻源解析器（参考消息、澎湃、36氪、凤凰、头条、华尔街见闻x2、财联社x2）
- [x] 测试通过 - 38 passed

### 阶段 3：公司档案模块 ⊘ (已跳过)
- 决定跳过此阶段，专注新闻抓取核心功能

### 阶段 4：定时任务 ✅ (已完成)
**目标**：实现自动定时抓取，减少手动触发

**已完成功能**：
- APScheduler 定时调度
- 任务状态监控
- 手动触发 API（已有）
- 任务执行日志（SQLite存储）

**验收标准**：
1. [x] 服务启动后自动开始定时任务
2. [x] 可配置抓取间隔（如每15分钟）
3. [x] 可查看任务执行历史和状态
4. [x] 可手动暂停/恢复定时任务
5. [x] 测试通过（38个测试）

### 阶段 5：财报数据模块
- 财经 API 集成
- 财报存储和查询

### 阶段 6：前端优化
- 更好的 UI/UX
- 图谱式关联展示
- 搜索和筛选

### 阶段 7：部署
- Docker 容器化
- 日志和监控
- 生产环境配置

### 阶段 8：管理功能 ✅ (已完成)
**目标**：提供系统管理和维护工具

**已完成功能**：
- 新闻源测试 - 测试所有新闻源连接状态和数据返回量
- 清空今日数据 - 清空数据库记录、文章文件和内存缓存

**验收标准**：
1. [x] 一键测试所有新闻源状态
2. [x] 显示每个源的数据返回量
3. [x] 清空功能不影响数据库文件（只清空数据）
4. [x] 前端弹窗展示测试结果

---

## 数据流设计

```
┌─────────────────────────────────────────────────────────────┐
│                        数据流                                │
├──────────────┬──────────────┬──────────────┬─────────────────┤
│  新闻抓取     │   存储       │   API        │   前端展示      │
│              │              │              │                 │
│ news_sources │ Timeline DB  │ /api/articles │  文章列表      │
│   ↓          │   ↓          │   ↓          │   ↓            │
│ 关键词过滤    │ + 文件存储   │ JSON 响应    │   HTML 页面     │
│   ↓          │              │              │                 │
│ Article对象  │ articles/    │               │                 │
└──────────────┴──────────────┴──────────────┴─────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                     配置系统                                  │
├──────────────┬──────────────┬──────────────┬─────────────────┤
│ legend.yaml  │ company.yaml │ news_sources │ crawler_config  │
│ 奇点人物      │ 公司档案     │ 新闻源配置    │ 抓取行为控制    │
│              │              │ 7个新闻源    │                 │
└──────────────┴──────────────┴──────────────┴─────────────────┘
              │
│ news_keywords.yaml
│   人物/公司/话题关键词
```

---

## 配置文件详细设计

### config/legend.yaml - 奇点人物档案
```yaml
legends:
  - id: "musk"
    name: "Elon Musk"
    name_cn: "马斯克"
    tier: "singularity"
    company_id: "TSLA"
    role: "CEO"
```

### config/company.yaml - 公司档案
```yaml
companies:
  - id: "TSLA"
    name: "Tesla, Inc."
    name_cn: "特斯拉"
    tier: 1
    type: "singularity"
    legend_id: "musk"
```

### config/news_keywords.yaml - 新闻筛选关键词
```yaml
people:
  musk: ["马斯克", "Elon Musk"]
companies:
  TSLA: ["特斯拉", "Tesla"]
topics:
  - ["FSD", "自动驾驶"]
```

### config/news_sources.yaml - 新闻源配置
```yaml
sources:
  - id: "cankaoxiaoxi"
    name: "参考消息"
    type: "official"
    enabled: true
    url: "..."
    parser: "json"
```

### config/crawler_config.yaml - 抓取配置
```yaml
strategy:
  mode: "scheduled"
  interval: 900  # 15分钟
network:
  timeout: 30
  retry: 3
```

---

## 阶段 1：快速迭代 Demo - 详细任务

### 轮次 1：配置系统 ✅ (已完成)
- [x] 创建 `src/config/` 模块
- [x] 实现配置数据模型
- [x] 实现配置读取器
- [x] 创建 5 个 YAML 配置文件
- [x] 测试通过 (8 passed)

### 轮次 2：新闻抓取模块 (当前)
- [ ] 修复 `src/crawlers/base.py`
  - [ ] 移除硬编码 KEYWORDS
  - [ ] 集成 ConfigReader 读取 news_keywords.yaml
  - [ ] 更新 filter_keywords 方法

- [ ] 完善 `src/crawlers/cankaoxiaoxi.py`
  - [ ] 集成配置读取
  - [ ] 实现完整数据解析

- [ ] 实现爬虫存储功能
  - [ ] 在 BaseCrawler 中添加 save_article() 方法
  - [ ] 保存文章元数据到 TimelineDB
  - [ ] 保存文章正文到 .md 文件
  - [ ] 实现入库前查重（按 URL 和标题）

- [ ] 修复测试文件
  - [ ] 修复 tests/conftest.py 中的 Path mock 问题
  - [ ] 更新 tests/test_crawlers.py

### 轮次 3：抓取 API
- [ ] 创建 `src/api/crawl.py`
- [ ] POST `/api/crawl/trigger` - 手动触发抓取
- [ ] 返回抓取结果统计（抓取数、筛选数、入库数）
- [ ] 集成到 main.py

### 轮次 4：前端页面
- [ ] 创建 `templates/index.html`
- [ ] 顶部添加"立即抓取"按钮
- [ ] 显示当日新闻列表
- [ ] 无新闻时显示"今日暂无相关新闻"
- [ ] 有新闻时显示标题、来源、时间

### 轮次 5：集成测试
- [ ] 启动服务验证
- [ ] 点击抓取按钮测试
- [ ] 验证查重功能
- [ ] 验证页面刷新展示

---

## 阶段 4：定时任务 - 详细任务 ✅ (已完成)

### 轮次 1：安装依赖 ✅
- [x] 添加 APScheduler 到依赖
- [x] 配置文件添加调度参数

### 轮次 2：调度器模块 ✅
- [x] 创建 `src/scheduler/__init__.py`
- [x] 创建 `src/scheduler/scheduler.py` - 调度器核心
  - [x] SchedulerManager 类
  - [x] 启动/停止/暂停方法
  - [x] 添加定时任务方法
  - [x] 任务执行日志记录

### 轮次 3：任务执行器 ✅
- [x] 内置于 `src/scheduler/scheduler.py`
  - [x] `_run_crawl_job()` - 新闻抓取任务
  - [x] 任务异常处理
  - [x] 任务结果记录

### 轮次 4：状态监控 ✅
- [x] 创建 `src/scheduler/store.py` - 任务状态存储
  - [x] 记录任务执行历史
  - [x] 记录任务执行结果
  - [x] 任务状态查询

### 轮次 5：API 接口 ✅
- [x] 创建 `src/api/scheduler.py` - 调度器管理 API
  - [x] GET /api/scheduler/status - 获取调度器状态
  - [x] POST /api/scheduler/start - 启动调度器
  - [x] POST /api/scheduler/stop - 停止调度器
  - [x] POST /api/scheduler/pause - 暂停调度器
  - [x] POST /api/scheduler/resume - 恢复调度器
  - [x] GET /api/scheduler/jobs - 获取任务历史

### 轮次 6：集成测试 ✅
- [x] 启动服务验证定时任务自动运行
- [x] 验证手动暂停/恢复功能
- [x] 验证任务执行日志记录
- [x] 测试通过（38个）

---

## 更新记录

- 2025-01-28：初始开发计划
- 2025-01-28：更新为快速迭代 Demo 目标
- 2026-01-28：完成阶段1、阶段2
- 2026-01-28：跳过阶段3，规划阶段4定时任务
- 2026-01-28：完成阶段4定时任务（38测试通过）
- 2026-01-28：完成7个新闻源解析器实现，文章保存到 data/articles/ 目录
- 2026-01-28：拆分华尔街见闻和财联社解析器为独立源（9个解析器总计）
- 2026-01-28：完成新闻源测试功能和清空今日数据功能
- 2026-01-28：关键词配置优化（修复数组格式、误匹配问题）
- 2026-01-31：**前端设计定稿** - 确定首页视觉设计（design/index-news.html）

---

### 阶段 6：前端优化 ✅ (设计定稿)
**目标**：确定首页视觉设计规范

**设计文件**：
- `design/index-news.html` - 首页定稿
- `design/index-5color.html` - 设计参考

**视觉风格**：科技感 / 赛博朋克 / 信息流

**色彩系统 (5色模板)**：
| 色名 | 色值 | 用途 |
|------|------|------|
| black | `#010400` | 背景 |
| hot-fuchsia | `#ff1654` | 点缀色 |
| maya-blue | `#55c1ff` | 主强调色 |
| ghost-white | `#fbf9ff` | 主要文字 |
| french-blue | `#1c448e` | 深层强调 |

**关键设计元素**：
- Maya-blue 梯度系统（L1-L4层级）
- 15px 蓝色网格背景
- 顶部蓝色光晕效果
- 毛玻璃 Header (`backdrop-filter: blur(20px)`)
- 网站标题支持 raised/inset 两种效果切换
- Timeline 卡片带人物水印
- 响应式布局（6fr + 4fr）

**后续任务**：
- [ ] 将设计应用到实际前端模板
- [ ] 实现数据绑定
- [ ] 添加交互功能

