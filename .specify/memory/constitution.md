<!--
================================================================================
SYNC IMPACT REPORT
================================================================================
Version Change: [TEMPLATE] → 1.0.0
Rationale: Initial constitution creation for Singularity Front project

Modified Principles:
  - [N/A - initial version]

Added Sections:
  - I. 数据可靠性原则 (Data Reliability)
  - II. 模块独立性原则 (Module Independence)
  - III. 最小侵入原则 (Minimum Intrusion)
  - IV. 中文优先原则 (Chinese First)
  - Development Workflow
  - Technology Constraints

Removed Sections:
  - [N/A - initial version]

Templates Updated:
  ✅ .specify/memory/constitution.md (this file)
  ✅ .specify/templates/plan-template.md - Constitution Check section aligned with 5 principles
  ✅ .specify/templates/spec-template.md - Requirements section references data reliability and module independence
  ✅ .specify/templates/tasks-template.md - Phase 2 includes Constitution compliance tasks

Follow-up TODOs:
  - None - all placeholders filled

Governance:
  - All specifications must pass data reliability validation
  - All implementations must respect module boundaries
  - Crawler intervals must be >= 900 seconds
================================================================================
-->

# Singularity Front Constitution

## Core Principles

### I. 数据可靠性原则 (Data Reliability)

数据是项目的生命线。所有数据源必须经过严格筛选，禁止使用传播虚假信息或未经验证的来源。

**MANDATORY RULES**:
- 禁止使用已知传播虚假言论的来源（如东方财富股吧、未经证实的社交媒体传言）
- 新闻源必须来自可信赖的主流媒体或官方渠道
- 财报数据必须来自专业财经 API 或官方披露文件
- 所有外部数据必须提供来源追溯
- 发现虚假数据必须立即剔除该数据源

**RATIONALE**: Singularity Front 的核心价值是提供准确、可靠的文明前沿动态。虚假信息会严重损害项目信誉，违背"雷达系统"的初衷。

### II. 模块独立性原则 (Module Independence)

项目分为四个独立模块，每个模块有独立的数据源和实现逻辑，严禁跨模块混淆数据。

**FOUR INDEPENDENT MODULES**:
1. **新闻抓取模块** - 9个新闻源，三层去重机制
2. **财报数据模块** - 专业财经 API，独立数据源
3. **公司档案模块** - 手动维护，AI 辅助整理
4. **关联分析模块** - 基于数据积累的智能关联（后期实现）

**MANDATORY RULES**:
- 每个模块的数据源完全独立，不得混用
- 模块间通过明确的 API 接口交互，不得直接访问内部数据
- 关联分析模块依赖前三个模块的数据积累，不能本末倒置
- 修改一个模块的数据源不得影响其他模块

**RATIONALE**: 模块独立性确保数据质量可控、问题可追溯。如果新闻数据混入财报数据，将导致严重的信任危机。

### III. 最小侵入原则 (Minimum Intrusion)

爬虫系统必须尊重目标服务器，避免对正常运营造成影响。

**MANDATORY RULES**:
- 最小抓取间隔：15分钟（900秒）
- 遵守 robots.txt 协议
- 使用合理的 User-Agent 标识
- 避免高峰时段抓取
- 实现退避策略：遇到 5xx 错误时延长间隔

**RATIONALE**: 过于频繁的抓取可能导致 IP 封禁，破坏数据持续性。15分钟间隔是实时性和服务器负载的平衡点。

### IV. 中文优先原则 (Chinese First)

项目面向中文用户，所有交互内容必须使用简体中文。

**MANDATORY RULES**:
- 所有代码注释使用简体中文
- 所有文档使用简体中文
- API 响应消息使用简体中文
- 日志输出使用简体中文
- 错误提示使用简体中文

**EXCEPTION**: 技术术语、专有名词保留原文（如 FastAPI、Playwright）

**RATIONALE**: 降低中文用户的理解成本，提高开发效率。



**MANDATORY RULES**:
- 所有数据和分析必须围绕 Legend/Supernova 展开
- 追踪的实体必须有明确的"文明级影响"潜力
- 关联分析必须揭示有意义的因果关系，而非数据堆砌
- 档案记录必须客观、中立，避免主观评价

**RATIONALE**: 这一哲学是项目的灵魂。偏离这一原则，项目将沦为普通的信息聚合平台，失去独特价值。

## Development Workflow

### Feature Development Process

1. **Specification (规格定义)**
   - 使用 `/speckit.specify` 创建功能规格
   - 必须明确数据来源及其可靠性
   - 必须说明该功能属于哪个模块
   - 必须评估对奇点哲学的贡献

2. **Planning (实施规划)**
   - 使用 `/speckit.plan` 生成实施计划
   - Constitution Check 必须验证：
     - ✅ 数据源可靠性已确认
     - ✅ 模块边界未被破坏
     - ✅ 抓取间隔 >= 900秒
     - ✅ 符合奇点哲学

3. **Task Breakdown (任务分解)**
   - 使用 `/speckit.tasks` 生成任务列表
   - 必须包含数据源验证任务
   - 必须包含模块边界测试

4. **Implementation (实施实现)**
   - 使用 `/speckit.implement` 执行实施
   - 每个模块的代码必须放在对应目录下
   - 跨模块调用必须通过定义的接口

5. **Analysis (一致性分析)**
   - 使用 `/speckit.analyze` 验证 spec、plan、tasks 的一致性

### Code Review Gates

所有 PR 必须通过以下检查：
- [ ] 数据源是否可靠？是否有来源追溯？
- [ ] 是否混淆了不同模块的数据？
- [ ] 抓取间隔是否 >= 900秒？
- [ ] 是否符合奇点哲学？（是否有明确的文明级影响？）
- [ ] 所有注释和文档是否使用简体中文？

## Technology Constraints

### 技术栈约束
- **后端语言**: Python 3.11+
- **Web 框架**: FastAPI
- **爬虫框架**: httpx（异步 HTTP）
- **HTML 解析**: BeautifulSoup4
- **数据库**: SQLite（元数据存储）
- **任务调度**: APScheduler
- **配置格式**: YAML

### 架构约束
- 前后端分离
- 静态页面生成（GitHub Pages）
- RESTful API 设计
- 最小依赖原则

## Governance

### Amendment Procedure
- 本 Constitution 的修改需要：
  1. 在 issue 中提出修改理由
  2. 讨论并获得维护者批准
  3. 更新版本号（语义化版本）
  4. 同步更新所有受影响的模板和文档

### Versioning Policy
- **MAJOR**: 移除或重新定义核心原则（如放弃数据可靠性原则）
- **MINOR**: 新增原则或大幅扩展现有原则
- **PATCH**: 文字澄清、错别字修正、非语义优化

### Compliance Review
- 所有 PR 必须符合本 Constitution
- 违反 Constitution 的代码必须拒绝合并
- 复杂度增加必须在实施计划中说明理由
- 使用 CLAUDE.md 作为运行时开发指导

**Version**: 1.0.0 | **Ratified**: 2026-02-01 | **Last Amended**: 2026-02-01
