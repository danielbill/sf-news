# Tasks: 模块 1 - 奇点档案数据库

**Feature**: 002-legend-researcher
**Module**: module-01-database
**Input**: plan.md, spec.md, checklists/module-01-database.md

**Tests**: 本模块要求 TDD 方式，测试任务已包含在各阶段中

**Organization**: 由于 spec.md 未提供明确的 User Stories，任务按功能模块组织

## Format: `[ID] [P?] [Component] Description`

- **[P]**: 可并行执行（不同文件，无依赖）
- **[Component]**: 所属组件（Models, Services, API, Tests）
- 包含精确文件路径

---

## Phase 1: Setup (项目结构初始化)

**Purpose**: 创建目录结构和基础配置

- [ ] T001 创建 tests 目录结构 in tests/
- [ ] T002 [P] 创建 .pytest.ini 配置文件（测试覆盖率目标 80%）
- [ ] T003 [P] 创建 tests/__init__.py 初始化文件

---

## Phase 2: Foundational (数据模型层 - 阻塞所有后续工作)

**Purpose**: 定义 Pydantic 数据模型，所有服务依赖此层

**⚠️ CRITICAL**: 此阶段完成后才能开始服务和 API 实现

### Tests for Models (TDD - 先写测试)

> **NOTE: 这些测试必须先运行并失败（RED），然后实现模型使其通过（GREEN）**

- [ ] T004 [P] [Tests] Legend 模型测试用例 in tests/test_legend_models.py
  - 测试 LegendType, LegendTier, ImpactLevel 枚举
  - 测试 Legend, LegendCreate, LegendUpdate 模型验证
- [ ] T005 [P] [Tests] Keyword 模型测试用例 in tests/test_legend_models.py
  - 测试 KeywordGroup, LegendKeywords 模型
- [ ] T006 [P] [Tests] Product 模型测试用例 in tests/test_legend_models.py
  - 测试 Product, ProductStatus 模型

### Models Implementation

- [ ] T007 [P] [Models] 创建 Legend 枚举类型 in src/models/legend.py
  - LegendType, LegendTier, ImpactLevel, ProductStatus, OrgType
- [ ] T008 [Models] 创建 Legend 基础模型 in src/models/legend.py
  - LegendBase, Legend, LegendCreate, LegendUpdate, LegendFilters
- [ ] T009 [Models] 创建 Keyword 相关模型 in src/models/legend.py
  - KeywordGroup, LegendKeywords
- [ ] T010 [Models] 创建 Product 相关模型 in src/models/legend.py
  - Product, ProductCreate, ProductStatus
- [ ] T011 [Models] 创建其他辅助模型 in src/models/legend.py
  - CompanyRelation, SyncLog, SyncResult, YamlKeywordsConfig, LegendDetail

**Checkpoint**: 运行 `pytest tests/test_legend_models.py -v` 确保所有测试通过

---

## Phase 3: Database Service (数据库服务层)

**Purpose**: 实现 LegendDB SQLite 数据库操作

### Tests for Database Service (TDD)

- [ ] T012 [P] [Tests] 数据库初始化测试 in tests/test_legend_db.py
  - 测试 init_db() 创建所有表
- [ ] T013 [P] [Tests] Legend CRUD 测试 in tests/test_legend_db.py
  - 测试 create_legend, get_legend, list_legends, update_legend, delete_legend
- [ ] T014 [P] [Tests] Keywords 操作测试 in tests/test_legend_db.py
  - 测试 set_keywords, get_keywords, keywords_changed
- [ ] T015 [P] [Tests] Products 操作测试 in tests/test_legend_db.py
  - 测试 add_product, list_products
- [ ] T016 [P] [Tests] Companies 关联测试 in tests/test_legend_db.py
  - 测试 add_company_relation, list_person_companies, list_company_people
- [ ] T017 [P] [Tests] Sync Log 测试 in tests/test_legend_db.py
  - 测试 log_sync, get_sync_logs

### Database Service Implementation

- [ ] T018 [Services] 创建 LegendDB 类框架 in src/services/legend_db.py
  - __init__, 数据库连接, init_db() 基础结构
- [ ] T019 [Services] 实现 Legend CRUD 方法 in src/services/legend_db.py
  - create_legend, get_legend, list_legends, update_legend, delete_legend, legend_exists
- [ ] T020 [Services] 实现 Keywords 方法 in src/services/legend_db.py
  - set_keywords, get_keywords, keywords_changed
- [ ] T021 [Services] 实现 Products 方法 in src/services/legend_db.py
  - add_product, list_products
- [ ] T022 [Services] 实现 Companies 关联方法 in src/services/legend_db.py
  - add_company_relation, list_person_companies, list_company_people
- [ ] T023 [Services] 实现 Sync Log 方法 in src/services/legend_db.py
  - log_sync, get_sync_logs, get_all_legend_ids

**Checkpoint**: 运行 `pytest tests/test_legend_db.py -v` 确保所有测试通过

---

## Phase 4: File Service (Markdown 文件服务层)

**Purpose**: 实现 LegendFileService Markdown 档案文件操作

### Tests for File Service (TDD)

- [ ] T024 [P] [Tests] 文件读写测试 in tests/test_legend_file.py
  - 测试 create_person_file, create_org_file, read_file, update_file, delete_file
- [ ] T025 [P] [Tests] 模板渲染测试 in tests/test_legend_file.py
  - 测试 render_person_template, render_org_template 输出格式
- [ ] T026 [P] [Tests] 目录操作测试 in tests/test_legend_file.py
  - 测试 list_all_people, list_all_orgs

### File Service Implementation

- [ ] T027 [Services] 创建 LegendFileService 类框架 in src/services/legend_file.py
  - __init__, _ensure_dirs, _get_file_path
- [ ] T028 [Services] 实现文件基础操作 in src/services/legend_file.py
  - file_exists, read_file, write_file, update_file, delete_file
- [ ] T029 [Services] 实现人物档案创建 in src/services/legend_file.py
  - create_person_file, render_person_template
- [ ] T030 [Services] 实现组织档案创建 in src/services/legend_file.py
  - create_org_file, render_org_template
- [ ] T031 [Services] 实现列表查询方法 in src/services/legend_file.py
  - list_all_people, list_all_orgs

**Checkpoint**: 运行 `pytest tests/test_legend_file.py -v` 确保所有测试通过

---

## Phase 5: Sync Service (同步服务层)

**Purpose**: 实现 LegendSyncService 从 YAML 同步到数据库

### Tests for Sync Service (TDD)

- [ ] T032 [P] [Tests] YAML 解析测试 in tests/test_legend_sync.py
  - 测试 _load_yaml, _calculate_file_hash
- [ ] T033 [P] [Tests] 类型推断测试 in tests/test_legend_sync.py
  - 测试 _infer_legend_type 各种情况（人物/组织/已知ID）
- [ ] T034 [P] [Tests] 名称提取测试 in tests/test_legend_sync.py
  - 测试 _extract_names
- [ ] T035 [P] [Tests] 关键词处理测试 in tests/test_legend_sync.py
  - 测试 _flatten_keywords, _calculate_keywords_hash
- [ ] T036 [P] [Tests] 同步流程测试 in tests/test_legend_sync.py
  - Mock YAML 和 DB，测试完整 sync() 流程
  - 测试新增、移除、关键词变化三种情况

### Sync Service Implementation

- [ ] T037 [Services] 创建 LegendSyncService 类框架 in src/services/legend_sync.py
  - __init__, _load_yaml, _calculate_file_hash
- [ ] T038 [Services] 实现辅助方法 in src/services/legend_sync.py
  - _flatten_keywords, _calculate_keywords_hash
- [ ] T039 [Services] 实现类型推断 in src/services/legend_sync.py
  - _infer_legend_type, _extract_names
- [ ] T040 [Services] 实现核心同步方法 in src/services/legend_sync.py
  - sync, _create_legend_from_yaml, _update_keywords, _remove_legend
- [ ] T041 [Services] 实现 YAML 配置获取 in src/services/legend_sync.py
  - get_yaml_legends

**Checkpoint**: 运行 `pytest tests/test_legend_sync.py -v` 确保所有测试通过

---

## Phase 6: API Layer (API 路由层)

**Purpose**: 实现 FastAPI 路由和端点

### Tests for API (TDD)

- [ ] T042 [P] [Tests] Legend CRUD API 测试 in tests/test_legend_api.py
  - 测试 GET /, GET /{id}, POST /, PUT /{id}, DELETE /{id}
- [ ] T043 [P] [Tests] Sync API 测试 in tests/test_legend_api.py
  - 测试 POST /sync, GET /sync/log
- [ ] T044 [P] [Tests] Keywords/Products API 测试 in tests/test_legend_api.py
  - 测试 GET /keywords, GET /{id}/keywords, GET /{id}/products

### API Implementation

- [ ] T045 [API] 创建 API 路由框架 in src/api/biz/legend_basedata.py
  - router 初始化, prefix, tags
- [ ] T046 [API] 实现 Legend CRUD 端点 in src/api/biz/legend_basedata.py
  - GET /, GET /{legend_id}, POST /, PUT /{legend_id}, DELETE /{legend_id}
- [ ] T047 [API] 实现 Sync 端点 in src/api/biz/legend_basedata.py
  - POST /sync, GET /sync/log
- [ ] T048 [API] 实现 Keywords/Products 端点 in src/api/biz/legend_basedata.py
  - GET /keywords, GET /{legend_id}/keywords, GET /{legend_id}/products
- [ ] T049 [API] 实现 Companies 关联端点 in src/api/biz/legend_basedata.py
  - GET /people/{person_id}/companies, GET /orgs/{company_id}/people

### Integration

- [ ] T050 [Integration] 创建 biz 模块初始化 in src/api/biz/__init__.py
- [ ] T051 [Integration] 注册 biz_router 到主应用 in src/main.py

**Checkpoint**: 运行 `pytest tests/test_legend_api.py -v` 确保所有测试通过

---

## Phase 7: Polish & Integration (收尾与集成)

**Purpose**: 端到端验证和文档更新

- [ ] T052 [P] 运行完整测试套件验证覆盖率 `pytest --cov=src --cov-report=term-missing`
- [ ] T053 [P] 更新 module-01-database.md checklist 状态为"已完成"
- [ ] T054 手动测试：调用 POST /biz/legend_basedata/sync 验证同步流程
- [ ] T055 手动测试：检查生成的 Markdown 文件格式正确性
- [ ] T056 [P] 更新 plan.md 状态为"Completed"

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: 无依赖，可立即开始
- **Phase 2 (Models)**: 依赖 Phase 1，**阻塞所有后续阶段**
- **Phase 3 (Database Service)**: 依赖 Phase 2 完成
- **Phase 4 (File Service)**: 依赖 Phase 2 完成
- **Phase 5 (Sync Service)**: 依赖 Phase 3, Phase 4 完成
- **Phase 6 (API Layer)**: 依赖 Phase 3, Phase 4, Phase 5 完成
- **Phase 7 (Polish)**: 依赖所有功能阶段完成

### Parallel Opportunities

- Phase 1 中所有 [P] 任务可并行
- Phase 2 中所有测试任务（T004-T006）可并行编写
- Phase 3 中所有测试任务（T012-T017）可并行编写
- Phase 4 中所有测试任务（T024-T026）可并行编写
- Phase 5 中所有测试任务（T032-T036）可并行编写
- Phase 6 中所有测试任务（T042-T044）可并行编写

### TDD Workflow (必须遵循)

每个阶段内：
1. **先写测试** → 运行测试确认失败（RED）
2. **实现代码** → 运行测试确认通过（GREEN）
3. **重构优化** → 运行所有测试确认无回归（IMPROVE）

---

## Test Coverage Targets

| 组件 | 目标覆盖率 |
|------|-----------|
| src/models/legend.py | >= 90% |
| src/services/legend_db.py | >= 85% |
| src/services/legend_file.py | >= 80% |
| src/services/legend_sync.py | >= 85% |
| src/api/biz/legend_basedata.py | >= 75% |
| **总体** | **>= 80%** |

---

## Phase 8: Scene 0 - AI 档案自动采集

**Purpose**: 使用百度 AI 搜索自动采集 Legend 档案数据

### 工具层实现

- [x] T057 [Tools] 创建 Fetcher 工具类 in src/tools/fetcher.py
  - 封装百度 AI 搜索 API 调用
  - 单次查询，返回结构化结果

### 查询模板实现

- [x] T058 [P] [Services] 创建人物查询模板 in src/services/people_query.md
  - 第一次查询：基础信息 + 家庭背景 + 教育背景
  - 第二次查询：伟愿与理念 + 金句库
  - 第三次查询：创业历程 + 公司矩阵 + 关键里程碑
- [x] T059 [P] [Services] 创建公司查询模板 in src/services/company_query.md
  - 第一次查询：公司基础信息 + 创始团队
  - 第二次查询：核心产品/服务 + 业务模式
  - 第三次查询：发展历程 + 关键里程碑 + 文明级影响

### 研究员调度实现

- [x] T060 [Services] 创建 Researcher 总调度 in src/services/researcher.py
  - 解析查询模板（支持多轮查询定义）
  - 变量替换（{id}, {name_cn}, {name_en}, {avatar} 等）
  - 分次调用 Fetcher（QPS 限制：每次间隔 1 秒）
  - 拼接 Markdown 结果（无表格，便于合并）

### 待完成任务

- [ ] T061 [Services] 集成 AI 采集到 legend_sync 同步流程
- [ ] T062 [Tests] AI 采集功能测试
- [ ] T063 [Services] 创建产品查询模板 in src/services/product_query.md
- [ ] T064 [Services] 实现 archive 档案渲染服务

---

## Phase 9: Scene 0 - AI 档案自动采集 (架构重构)

**Purpose**: 重构 AI 档案采集架构，实现 queryer → render → saver 流程

### 配置和模板

- [x] T065 [Config] 创建 research_config.yaml in config/
  - 定义 output_paths (company/people/product)
  - 定义 templates 路径
- [x] T066 [Config] 创建 company_query.yaml in config/research/
  - 3次查询：基础信息、产品服务、发展历程
- [x] T067 [Config] 创建 people_query.yaml in config/research/
  - 3次查询：基础信息、伟愿理念、创业历程
- [x] T068 [Config] 创建 product_query.yaml in config/research/
  - 3次查询：基础信息、功能特性、市场表现

### queryer (通用查询器)

- [x] T069 [Services] 创建 queryer.py in src/services/
  - _load_template() 读取 YAML 模板
  - _replace_variables() 变量替换
  - research() 主流程：循环调用 AI
- [ ] T070 [Tests] queryer 测试 in tests/test_queryer.py

### render (渲染器)

- [x] T071 [Services] 创建 render.py in src/services/
  - BaseRender 基类
  - CompanyRender / PeopleRender / ProductRender
  - add_result() 累积结果
  - to_markdown() 生成完整内容
- [ ] T072 [Tests] render 测试 in tests/test_render.py

### saver (保存器)

- [x] T073 [Services] 创建 saver.py in src/services/
  - _load_config() 读取 research_config.yaml
  - save() 保存文件到对应目录
- [ ] T074 [Tests] saver 测试 in tests/test_saver.py

### researcher (任务拆解器)

- [x] T075 [Services] 重构 researcher.py in src/services/
  - _parse_legend_data() 解析 legend 数据包
  - _execute_task() 执行单个研究任务
  - research() 批量研究入口
- [ ] T076 [Tests] researcher 测试 in tests/test_researcher.py

### legend_sync 集成

- [x] T077 [Services] 修改 legend_sync.py in src/services/
  - 支持 legend.yaml 和 nova.yaml 两种格式
  - 检测新增时调用 researcher
  - 更新内存中的 legend dict 和 keywords dict
- [x] T078 [Integration] 集成测试：字节跳动档案生成
  - 调用 nova 同步
  - 验证生成 data/nova/company/bytedance.md

---

## Notes

- [P] 任务 = 不同文件，无依赖，可并行
- [Component] 标签 = Models/Services/API/Tests
- 必须遵循 TDD：测试失败 → 实现通过 → 重构优化
- 每完成一个 Phase 运行相应测试验证
- 避免模糊任务描述、同一文件冲突、破坏独立性的跨组件依赖
