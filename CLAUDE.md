# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## 项目核心理念

**Singularity Front** 是一个"文明前沿雷达系统"，实时追踪奇点人物（Singularity）及其生态系统（Front）的所有动态。

### 核心概念

| 概念                    | 定义                                                                   |
| ----------------------- | ---------------------------------------------------------------------- |
| **Legend（奇点）**      | 能够引发文明级跃迁的实体（人物或组织），已开启新时代、全球公认、不可逆 |
| **Supernova（超新星）** | 正在爆发式成长、极有可能成为奇点但也可能快速陨落的实体                 |
| **Front**               | 由奇点人物引发的整个文明冲击波（公司、战略、技术、供应链、资本流向）   |

### 奇点与超新星

| 等级            | 定义                           | 例子                                                            |
| --------------- | ------------------------------ | --------------------------------------------------------------- |
| **SINGULARITY** | 已开启新时代，既定事实，不可逆 | 黄仁勋（AI算力时代）、马斯克（太空+电动车）、Google（信息时代） |
| **SUPERNOVA**   | 爆发中，AGI实现后可能成为奇点  | Sam Altman、Anthropic、Satya Nadella                            |

**核心哲学**：奇点是必然影响所有人的。

---

## 关键文档导航

| 类型                  | 文档                                                                   |
| --------------------- | ---------------------------------------------------------------------- |
| **项目哲学**          | [.README.md](.README.md)                                               |
| **Legend 档案索引**   | [data/legend_index.md](data/legend_index.md)                           |
| **奇点档案设计理念**  | [design/legend/奇点档案设计理念.md](design/legend/奇点档案设计理念.md) |
| **Legend 资料库设计** | [design/legend_database_design.md](design/legend_database_design.md)   |
| **页面设计索引**      | [design/README.md](design/README.md)                                   |
| **技术栈**            | [docs/tech_stack.md](docs/tech_stack.md)                               |
| **前端架构**          | [docs/frontend_architecture.md](docs/frontend_architecture.md)         |
| **API 文档**          | [docs/api.md](docs/api.md)                                             |
| **测试规范**          | [docs/testing.md](docs/testing.md)                                     |
| **设计方案**          | [docs/design.md](docs/design.md)                                       |
| **开发计划**          | [docs/development_plan.md](docs/development_plan.md)                   |

---

## 开发约束

### 模块独立性
项目分为四个独立模块，**不要混淆它们的数据源**：
- 新闻抓取模块（9个新闻源，三层去重）
- 财报数据模块（专业财经 API，独立数据源）
- 公司档案模块（手动维护，AI 辅助）
- 关联分析模块（后期实现，智能关联）

### 通用规则
1. **所有回复用简体中文**
2. **数据源必须可靠**：禁止使用制造虚假言论的来源（如东方财富股吧）
3. **关联分析后期实现**：先建立数据积累，再讨论智能关联方案

### Ralph 开发流程
- 详细计划记录在 `.ralph/@fix_plan.md`
- 小步快跑，和用户确认后更新文档
- 最小抓取间隔：15分钟（900秒）
- 关键词配置必须使用数组格式 `["关键词"]`

---

## 常用命令

```bash
# 启动服务（Windows）
start.bat

# 手动启动
python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# 运行测试
pytest tests/ -v

# 生成静态页面（GitHub Pages）
python -m src.generate_static

# 手动触发爬虫
python -m src.crawl_cli

# 手动触发 GitHub Actions
gh workflow run crawler.yml
```

---

## 项目命令

【update】将对话中最新确认的设计，更新至：
- [design](docs/design.md) - 设计方案文档
- [development_plan](docs/development_plan.md) - 开发计划（含工作记录）
- [fix_plan](.ralph/@fix_plan.md) - Ralph 任务计划

【reload】重新读取 CLAUDE.md



## 对外依赖

百度搜索接口资料参考：
D:\workspace\cybcortex\1技能库\doc

财经接口调用：
D:\量化研究\数据管理\A股相关数据采集


## 其他

当用户要求保存重要谈话内容时，总结当前上下文，以【话题+yymmdd】生成文件，保存到 临时话题\ 目录下。
