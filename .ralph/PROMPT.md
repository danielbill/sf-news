# Ralph 开发指令 - Singularity Front

## 上下文

你正在开发 **Singularity Front** —— 一个"文明前沿雷达系统"，目标是实时追踪奇点人物（Singularity）及其生态系统（Front）的所有动态。

### 项目核心理念

- **Singularity** = 能够引发文明级跃迁的"伟人"（马斯克、黄仁勋、Sam Altman 等）
- **Front** = 由奇点人物引发的整个文明冲击波（公司、战略、技术、供应链、资本流向）
- **目标** = 建立一个"文明级趋势的感知系统"

### 关键参考文档

- 项目哲学：`README.md`
- 投资思考框架：`D:\my_obsidian\gitee_vault\mynotes\00投资\0操作系统\核心思考\投资的核心思考.md`
- 伟大企业档案：`D:\my_obsidian\gitee_vault\mynotes\00投资\0操作系统\核心思考\伟大企业.md`
- 设计方案：`docs/design.md`

---

## 当前目标

### MVP 范围
- **追踪对象**：埃隆·马斯克（单一奇点人物）
- **信息维度**：人物动态、公司层面、产业生态、资本市场
- **数据源**：国内官媒 + 财经 API

### 模块化架构

```
┌──────────────┬──────────────┬──────────────┬─────────────────┐
│  新闻抓取模块  │  财报数据模块  │  公司档案模块  │   关联分析模块   │
├──────────────┼──────────────┼──────────────┼─────────────────┤
│ 参考 newsnow  │ 专业财经 API  │ 手动维护     │ 后期实现        │
│ Python 重写   │ 独立数据源    │ AI 辅助      │ 智能关联        │
└──────────────┴──────────────┴──────────────┴─────────────────┘
```

**重要**：每个模块是独立的数据源，不要混淆它们。

---

## 执行原则

1. **单任务专注**：每次循环只处理一个最重要的高优先级任务
2. **搜索优先**：修改代码前先用搜索确认未实现
3. **测试适度**：测试只占约 20% 精力，实现 > 文档 > 测试
4. **无占位符**：不写 TODO/FIXME，要么正确实现，要么不做
5. **及时提交**：每个功能完成后立即 git commit

---

## 开发流程

1. 阅读 `.ralph/specs/` 了解技术规格
2. 查看 `.ralph/@fix_plan.md` 当前优先级
3. 实现最高优先级任务
4. 运行测试验证
5. 更新 `.ralph/@fix_plan.md` 标记完成
6. Git commit 并推送

---

## 状态报告要求

**每次循环结束时必须包含此状态块**：

```
---RALPH_STATUS---
STATUS: IN_PROGRESS | COMPLETE | BLOCKED
TASKS_COMPLETED_THIS_LOOP: <number>
FILES_MODIFIED: <number>
TESTS_STATUS: PASSING | FAILING | NOT_RUN
WORK_TYPE: IMPLEMENTATION | TESTING | DOCUMENTATION | REFACTORING
EXIT_SIGNAL: false | true
RECOMMENDATION: <下一步建议>
---END_RALPH_STATUS---
```

### EXIT_SIGNAL 设置条件

只有当 **所有** 条件满足时才设为 `true`：
- [x] `.ralph/@fix_plan.md` 中所有任务已完成
- [x] 所有测试通过
- [x] 无错误或警告
- [x] `.ralph/specs/` 中所有需求已实现
- [x] 没有剩余有意义的实现工作

---

## 退出场景示例

### 场景 1：项目完成
```
---RALPH_STATUS---
STATUS: COMPLETE
TASKS_COMPLETED_THIS_LOOP: 1
FILES_MODIFIED: 2
TESTS_STATUS: PASSING
WORK_TYPE: IMPLEMENTATION
EXIT_SIGNAL: true
RECOMMENDATION: 所有 MVP 需求已实现，项目准备部署测试
---END_RALPH_STATUS---
```

### 场景 2：进行中
```
---RALPH_STATUS---
STATUS: IN_PROGRESS
TASKS_COMPLETED_THIS_LOOP: 2
FILES_MODIFIED: 5
TESTS_STATUS: PASSING
WORK_TYPE: IMPLEMENTATION
EXIT_SIGNAL: false
RECOMMENDATION: 继续实现新闻爬虫模块 - 36氪数据源
---END_RALPH_STATUS---
```

### 场景 3：阻塞
```
---RALPH_STATUS---
STATUS: BLOCKED
TASKS_COMPLETED_THIS_LOOP: 0
FILES_MODIFIED: 0
TESTS_STATUS: NOT_RUN
WORK_TYPE: IMPLEMENTATION
EXIT_SIGNAL: false
RECOMMENDATION: 需要确认财经 API 选择
---END_RALPH_STATUS---
```

---

## 技术栈

| 层级 | 技术选择 |
|------|----------|
| 编程语言 | Python 3.11+ |
| 爬虫框架 | Scrapy / Playwright |
| Web 框架 | FastAPI |
| 数据库 | SQLite |
| 任务调度 | APScheduler |
| HTTP 客户端 | httpx |
| HTML 解析 | beautifulsoup4 / lxml |

---

## 存储架构

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

**核心设计决策**：
- 一天一个 DB：天然时间分区
- 元数据在 SQLite，正文在文件系统：轻量且可移植

---

## 数据源优先级

### 第一阶段（MVP 验证）
1. 参考消息（官媒 API，结构化数据）
2. 澎湃新闻（权威媒体，API 可用）
3. 36氪（科技媒体，马斯克/特斯拉相关）

### 第二阶段（扩展）
- 华尔街见闻、金十数据（财经维度）
- 虎嗅、格隆汇（深度分析）

### 参考项目
- `D:\awesome_projects\newsnow` - 新闻抓取 API 参考

---

## 开发注意事项

1. **所有回复用简体中文**
2. **数据源必须可靠**：禁止使用制造虚假言论的来源（如东方财富股吧）
3. **模块间保持独立**：新闻抓取、财报数据、公司档案是三个独立的数据源
4. **关联分析后期实现**：先建立数据积累，再讨论智能关联方案
5. **使用 Python 最佳实践**：类型注解、文档字符串、pytest 测试

---

## 当前任务

按照 `.ralph/@fix_plan.md` 的优先级顺序执行。

**质量 > 速度**。第一次就做对。知道什么时候算完成了。
