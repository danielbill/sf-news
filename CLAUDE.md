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

- 项目哲学：[README.md](README.md)
- 投资思考框架：`D:\my_obsidian\gitee_vault\mynotes\00投资\0操作系统\核心思考\投资的核心思考.md`
- 伟大企业档案 : D:\my_obsidian\gitee_vault\mynotes\00投资\0操作系统\核心思考\伟大企业.md
- 设计方案：[docs/design.md](docs/design.md)

---

## 架构设计原则

### 模块化架构

项目分为四个独立模块，**不要混淆它们的数据源**：

```
┌──────────────┬──────────────┬──────────────┬─────────────────┐
│  新闻抓取模块  │  财报数据模块  │  公司档案模块  │   关联分析模块   │
├──────────────┼──────────────┼──────────────┼─────────────────┤
│ 参考 newsnow  │ 专业财经 API  │ 手动维护     │ 后期实现        │
│ Python 重写   │ 独立数据源    │ AI 辅助      │ 智能关联        │
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
| 编程语言 | Python |
| 爬虫框架 | Scrapy / Playwright |
| Web 框架 | FastAPI |
| 数据库 | SQLite |
| 任务调度 | APScheduler |

---

## 数据源参考

### 新闻抓取模块

参考项目：`D:\awesome_projects\newsnow`

**MVP 第一阶段数据源**：
1. 参考消息（官媒 API）
2. 澎湃新闻（权威媒体）
3. 36氪（科技媒体）

### 财报数据模块

使用专业财经 API（与新闻抓取完全独立）

---

## 开发注意事项

1. **所有回复用简体中文**
2. **数据源必须可靠**：禁止使用制造虚假言论的来源（如东方财富股吧）
3. **模块间保持独立**：新闻抓取、财报数据、公司档案是三个独立的数据源
4. **关联分析后期实现**：先建立数据积累，再讨论智能关联方案
5. 开发使用ralph模板，每次小步快跑，和用户确认一个小的功能点后，更新ralph的必要文档。
6. ralph项目说明及模板 D:\ai_tools\claudecode第三方独立插件\ralph-claude-code\readme.md

---

## Ralph 开发流程约束

### 开发流程规范
1. **详细计划先行**: `docs/development_plan.md` 的每一步都需要做详细计划，记录在 `.ralph/@fix_plan.md`
2. **fix_plan 内容规范**: 每个任务需要包含：
   - 约束条件（如有）
   - 分轮次的详细任务清单
   - 代码接口规格/结构说明
   - 验收标准列表
3. **参考 specs 格式**: 技术规格应参考 `.ralph/specs/` 中的格式编写

### 定时任务约束
1. **最小抓取间隔**: 15分钟（900秒），不能设置更小
2. **启动行为**: 服务启动后默认立刻执行一次抓取


### 项目命令

【update】
将对话中最新确认的设计，更新至 [design](docs/design.md)
总计划更新至 [development_plan](docs/development_plan.md)
步骤计划更新至 [fix_plan](.ralph/@fix_plan.md)