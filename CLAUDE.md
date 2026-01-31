# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## 项目核心理念

**Singularity Front** 是一个"文明前沿雷达系统"，目标是实时追踪奇点人物（Singularity）及其生态系统（Front）的所有动态。

### 核心概念

- **Singularity** = 能够引发文明级跃迁的"伟人"（如马斯克、黄仁勋、Sam Altman）
- **Front** = 由奇点人物引发的整个文明冲击波（公司、战略、技术、供应链、资本流向）
- **目标** = 理解伟大力量正在如何重塑世界

### 关键参考文档

- 项目哲学：[.README.md](.README.md)
- 投资思考框架：`D:\my_obsidian\gitee_vault\mynotes\00投资\0操作系统\核心思考\投资的核心思考.md`
- 伟大企业档案：`D:\my_obsidian\gitee_vault\mynotes\00投资\0操作系统\核心思考\伟大企业.md`
- 设计方案：[docs/design.md](docs/design.md)
- 开发计划：[docs/development_plan.md](docs/development_plan.md)
- Ralph 任务计划：[.ralph/@fix_plan.md](.ralph/@fix_plan.md)

---

## 项目目录结构

```
singularity-front/
├── config/                    # 配置文件（YAML）
│   ├── crawler_config.yaml   # 爬虫配置
│   ├── legend.yaml           # 奇点人物档案
│   ├── company.yaml          # 公司档案
│   ├── news_keywords.yaml    # 新闻筛选关键词
│   └── news_sources.yaml     # 新闻源配置
│
├── design/                    # 前端设计文件
│   ├── index-news.html       # 首页设计定稿 ⭐
│   ├── index-5color.html     # 5色方案设计参考
│   └── 模板/                  # 设计模板
│
├── docs/                      # 项目文档
│   ├── design.md             # 设计方案（非工作记录）
│   └── development_plan.md   # 开发计划（含工作记录）
│
├── src/                       # 源代码
│   ├── api/                  # API 路由
│   │   ├── admin.py          # 管理后台 API
│   │   └── crawl.py          # 新闻抓取 API
│   ├── config/               # 配置读取模块
│   ├── crawlers/             # 爬虫模块
│   │   ├── base.py           # 基础爬虫类
│   │   ├── universal.py      # 通用爬虫
│   │   ├── dedup.py          # 去重逻辑
│   │   ├── keywords_filter.py # 关键词筛选
│   │   ├── url_cache.py      # URL 缓存
│   │   ├── source_tester.py  # 新闻源测试器
│   │   └── parsers/          # 解析器目录
│   ├── models/               # 数据模型
│   ├── scheduler/            # 定时任务调度器
│   ├── storage/              # 存储模块
│   ├── tools/                # 工具函数
│   └── main.py               # 应用入口
│
├── templates/                 # HTML 模板（旧）
│   └── index.html
│
├── static/                    # 静态资源
├── tests/                     # 测试文件
├── data/                      # 运行时数据
│   ├── db/                   # SQLite 数据库
│   └── articles/             # 文章正文 (.md)
│
├── .ralph/                    # Ralph 开发模板配置
│   └── @fix_plan.md          # 当前任务计划
│
├── CLAUDE.md                  # 本文件
├── pyproject.toml            # Python 项目配置
├── requirements.txt           # 依赖列表
└── start.bat                  # 启动脚本
```

---

## 架构设计原则

### 模块化架构

项目分为四个独立模块，**不要混淆它们的数据源**：

```
┌──────────────┬──────────────┬──────────────┬─────────────────┐
│  新闻抓取模块  │  财报数据模块  │  公司档案模块  │   关联分析模块   │
├──────────────┼──────────────┼──────────────┼─────────────────┤
│ 9个新闻源     │ 专业财经 API  │ 手动维护     │ 后期实现        │
│ 三层去重      │ 独立数据源    │ AI 辅助      │ 智能关联        │
└──────────────┴──────────────┴──────────────┴─────────────────┘
```

### 存储架构

**Timeline + 元数据/文件分离**：

```
data/
├── db/                  # SQLite 元数据（一天一个 DB）
│   └── timeline_YYYY-MM-DD.sqlite
├── articles/            # 文章正文（.md 文件）
│   └── YYYY/MM/DD/{uuid}.md
├── financial/           # 财报数据
│   └── YYYY/MM/
└── companies/
    └── meta.sqlite      # 公司/人物元数据（固定）
```

**关键设计决策**：
- **一天一个 DB**：天然时间分区、备份方便、并发友好
- **元数据在 SQLite，正文在文件**：数据库轻量、文章可直接用笔记软件打开

---

## 技术栈

| 层级 | 技术选择 |
|------|----------|
| 编程语言 | Python 3.11+ |
| Web 框架 | FastAPI |
| 爬虫框架 | httpx + BeautifulSoup4 |
| 数据库 | SQLite |
| 任务调度 | APScheduler |
| 配置格式 | YAML |
| 前端 | 原生 HTML/CSS/JS |

---

## 新闻源配置

### 已实现的解析器

| 文件 | 新闻源 | 状态 |
|------|--------|------|
| `parsers/cankaoxiaoxi.py` | 参考消息 | ✅ |
| `parsers/thepaper.py` | 澎湃新闻 | ✅ |
| `parsers/_36kr.py` | 36氪 | ✅ |
| `parsers/ifeng.py` | 凤凰网 | ✅ |
| `parsers/toutiao.py` | 今日头条 | ✅ |
| `parsers/wallstreetcn_live.py` | 华尔街见闻快讯 | ✅ |
| `parsers/wallstreetcn_news.py` | 华尔街见闻资讯 | ✅ |
| `parsers/cls_telegraph.py` | 财联社电报 | ✅ |
| `parsers/cls_depth.py` | 财联社深度（禁用，需签名） | ❌ |

---

## 前端设计规范

### 设计文件
- **首页定稿**：`design/index-news.html`
- **设计参考**：`design/index-5color.html`

### 视觉风格
科技感 / 赛博朋克 / 信息流

### 色彩系统 (5色模板)

| 色名 | 色值 | 用途 |
|------|------|------|
| black | `#010400` | 背景 |
| hot-fuchsia | `#ff1654` | 点缀色 |
| maya-blue | `#55c1ff` | 主强调色 |
| ghost-white | `#fbf9ff` | 主要文字 |
| french-blue | `#1c448e` | 深层强调 |

### Maya-blue 梯度系统
```css
--maya-bright: #8dd4ff;       /* L1 - 最亮层（高光效果） */
--maya-primary: #55c1ff;      /* L2 - 主强调色 */
--maya-mid: #4a8a9a;          /* L3 - 中等层 */
--maya-meta: #6a9cd6;         /* L3.5 - 元数据层 */
--maya-subtle: #2d3a45;       /* L4 - 边框层 */
```

---

## 开发注意事项

1. **所有回复用简体中文**
2. **数据源必须可靠**：禁止使用制造虚假言论的来源（如东方财富股吧）
3. **模块间保持独立**：新闻抓取、财报数据、公司档案是三个独立的数据源
4. **关联分析后期实现**：先建立数据积累，再讨论智能关联方案
5. 开发使用 ralph 模板，每次小步快跑，和用户确认一个小的功能点后，更新 ralph 的必要文档
6. ralph 项目说明及模板：`D:\ai_tools\claudecode第三方独立插件\ralph-claude-code\readme.md`

---

## Ralph 开发流程约束

### 开发流程规范
1. **详细计划先行**: `docs/development_plan.md` 的每一步都需要做详细计划，记录在 `.ralph/@fix_plan.md`
2. **fix_plan 内容规范**: 每个任务需要包含：
   - 约束条件（如有）
   - 分轮次的详细任务清单
   - 代码接口规格/结构说明
   - 验收标准列表

### 定时任务约束
1. **最小抓取间隔**: 15分钟（900秒），不能设置更小
2. **启动行为**: 服务启动后默认立刻执行一次抓取

### 关键词配置约束
- **格式**: 必须使用数组格式 `["关键词"]`，不能使用字符串格式
- **原因**: Python `set.update("string")` 会将字符串拆分成单个字符
- **精度**: 使用更精确的关键词避免误匹配（如"英伟达生态"而非"生态"）

---

## 项目命令

【update】
将对话中最新确认的设计，更新至：
- [design](docs/design.md) - 设计方案文档
- [development_plan](docs/development_plan.md) - 开发计划（含工作记录）
- [fix_plan](.ralph/@fix_plan.md) - Ralph 任务计划

---

## 测试规范

### 测试文件位置
所有测试文件位于 `tests/` 目录，**不要在根目录创建临时测试文件**。

### 常用测试命令

```bash
# 运行所有测试
pytest tests/

# 运行特定测试文件
pytest tests/test_keywords.py
pytest tests/test_config.py
pytest tests/test_scheduler.py

# 运行测试并显示详细输出
pytest tests/ -v

# 运行测试并显示打印输出
pytest tests/ -s
```

### 测试文件说明

| 文件 | 用途 | 运行方式 |
|------|------|----------|
| `test_keywords.py` | 测试关键词筛选功能 | `pytest tests/test_keywords.py -s` |
| `test_config.py` | 测试配置加载 | `pytest tests/test_config.py` |
| `test_storage.py` | 测试数据库操作 | `pytest tests/test_storage.py` |
| `test_new_features.py` | 测试去重、URL缓存 | `pytest tests/test_new_features.py` |
| `test_scheduler.py` | 测试调度器 | `pytest tests/test_scheduler.py` |
| `conftest.py` | pytest fixtures，无需直接运行 | - |

---

## API 端点

### 新闻抓取 API
| 方法 | 路径 | 功能 |
|------|------|------|
| POST | `/api/crawl/trigger` | 手动触发抓取 |
| GET | `/api/articles` | 获取今日新闻列表 |
| GET | `/api/articles/{id}` | 获取单篇文章详情 |

### 调度器 API
| 方法 | 路径 | 功能 |
|------|------|------|
| GET | `/api/scheduler/status` | 获取调度器状态 |
| POST | `/api/scheduler/start` | 启动调度器 |
| POST | `/api/scheduler/stop` | 停止调度器 |
| POST | `/api/scheduler/pause` | 暂停调度器 |
| POST | `/api/scheduler/resume` | 恢复调度器 |
| GET | `/api/scheduler/jobs` | 获取任务历史 |

### 管理后台 API
| 方法 | 路径 | 功能 |
|------|------|------|
| POST | `/admin/cleartodaynews` | 清空今日数据（数据库+文件+缓存） |
| GET | `/admin/source_test` | 测试所有新闻源状态 |

---

## 启动服务

```bash
# Windows
start.bat

# 手动启动
python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```
