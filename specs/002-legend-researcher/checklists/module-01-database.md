# 模块 1: 奇点档案数据库

**层级**: 数据基础层
**状态**: ✅ 已完成 (2026-02-02)
**优先级**: P0 - 必须最先实现，其他模块依赖此模块

## 功能描述

Legend 实体的基础信息存储和维护，支持人物(PERSON)和组织(ORGANIZATION)两种类型的档案。

### 核心设计原则

1. **数据源**: Legend 实体来源于 `config/news_keywords.yaml`，这是权威源头
2. **存储策略**: Markdown + SQLite 混合存储
   - **Markdown 文件**: 档案信息（公司介绍、核心人员介绍、里程碑等）
   - **SQLite 数据库**: 易变且参与计算的数据（财报、战略、供应链、产品等）
3. **自动化流程**: 每日扫描 `news_keywords.yaml`，检测变化
   - 新增 Legend → 创建新档案
   - 移除 Legend → 标记归档
   - Keywords 变化 → 更新关键词配置
4. **数据采集**: 使用 `/baidu-ai-search` skill 自动填充档案
5. **人工干预**: 允许用户编辑和补充档案信息

### API 端点

- **路由**: `/biz/legend_basedata`
- **类型**: 后台业务 API（非公网 API）

## 验收标准

- [x] 能够从 `config/news_keywords.yaml` 读取 Legend 定义
- [x] 能够检测 Legend 的新增、移除、keywords 变化
- [x] 支持 Legend 实体的创建、读取、更新、删除操作
- [x] 支持人物和组织两种类型
- [x] Markdown 档案文件按模板创建（`legend_person_template.md` / `legend_org_template.md`）
- [x] 易变数据存储于 SQLite 数据库
- [x] 提供数据验证和错误处理
- [x] 数据可被其他 11 个模块读取使用
- [x] 支持人工编辑和补充档案信息

## 存储架构

### Markdown 档案（静态/半静态信息）
- 人物档案: `data/legend/people/{id}.md`
- 组织档案: `data/legend/orgs/{id}.md`

### SQLite 数据库（易变数据）
- `legends` 表: 实体基础索引
- `legend_keywords` 表: 关键词配置
- `legend_products` 表: 核心产品/服务
- `legend_financials` 表: 财务数据（与模块 2 关联）
- `legend_strategy` 表: 战略方向（与模块 3 关联）
- `legend_supply_chain` 表: 供应链关系（与模块 5 关联）

## 依赖

- 依赖 `config/news_keywords.yaml` 作为数据源
- 依赖 `/baidu-ai-search` skill 进行数据采集

## 输出物

- [x] `models/legend.py` - Legend 数据模型（SQLite）
- [x] `services/legend_file.py` - Markdown 档案读写服务
- [x] `services/legend_sync.py` - keywords.yaml 同步服务
- [x] `api/biz/legend_basedata.py` - 后台业务 API
- [x] `tools/fetcher.py` - AI 搜索工具类
- [x] `services/researcher.py` - 奇点研究员总调度
- [x] `services/people_query.md` - 人物查询模板
- [x] `services/company_query.md` - 公司查询模板
- [ ] `tests/test_legend_database.py` - 单元测试

## Scene 0: AI 自动采集进展

- [x] Fetcher 工具类 - 封装百度 AI 搜索 API
- [x] 人物查询模板 - 3次查询（基础信息、伟愿理念、创业历程）
- [x] 公司查询模板 - 3次查询（基础信息、产品业务、发展历程）
- [x] Researcher 调度 - 解析模板、分次查询、拼接结果
- [ ] 集成到 legend_sync 同步流程
- [ ] 测试验证
