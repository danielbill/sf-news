# Implementation Plan: 模块 1 - 奇点档案数据库

**Feature**: 002-legend-researcher
**Module**: module-01-database
**Created**: 2026-02-02
**Status**: Draft

---

## 1. Overview

本模块实现 Legend 实体（人物和组织）的基础档案管理，采用 **Markdown + SQLite 混合存储**策略：
- **Markdown**: 档案信息（公司介绍、核心人员介绍、里程碑等静态/半静态信息）
- **SQLite**: 易变且参与计算的数据（财报、战略、供应链、产品、关键词等）

### 数据流

```
config/legend.yaml (奇点实体) + config/nova.yaml (超新星实体)
                    ↓
            手动触发同步 (POST /biz/legend_basedata/sync)
                    ↓
            计算文件哈希，对比上次哈希
                    ↓
            ┌─────────────┬─────────────┬─────────────┐
            │   新增      │   移除      │ 内容变化     │
            ▼             ▼             ▼
        创建档案      标记归档      更新记录
            │             │             │
            └─────────────┴─────────────┘
                          │
                   ┌──────┴──────┐
                   ▼             ▼
           ┌──────────────────┐  ┌──────────────────┐
           │  LegendDB (SQLite) │  │ Markdown Files   │
           │  - legends       │  │  - people/{id}.md │
           │  - legend_keywords│  │  - company/{id}.md│
           │  - legend_products│  └──────────────────┘
           │  - legend_XXX    │
           └──────────────────┘
```

**配置文件说明**:

| 文件 | 用途 | 实体类型 |
|------|------|----------|
| `config/legend.yaml` | 奇点实体（已验证） | people + company |
| `config/nova.yaml` | 超新星实体（爆发中） | people + company |

**Keywords 提取规则**:
- `name_en`: 提取
- `name_cn`: 提取（如果有）
- `keywords`: 展平后提取
- 其他字段: 不提取

**触发方式**: 纯手动触发（管理后台按钮 / API 调用），无定时任务

---

## 2. Database Schema

### 2.1 SQLite 表结构

#### `legends` 表 - Legend 实体主表

```sql
CREATE TABLE legends (
    id TEXT PRIMARY KEY,              -- Legend ID (如 musk, huang, anthropic)
    type TEXT NOT NULL,               -- PERSON | ORGANIZATION
    name_en TEXT,                     -- 英文名
    name_cn TEXT,                     -- 中文名
    avatar_url TEXT,                  -- 头像/Logo URL
    legend_tier TEXT,                 -- SINGULARITY | QUASI | POTENTIAL
    impact_level TEXT,                -- SINGULARITY | INDUSTRY | COMPANY
    bio_short TEXT,                   -- 简短介绍 (100字)
    file_path TEXT,                   -- Markdown 档案路径
    created_at DATETIME DEFAULT (datetime('now', 'localtime')),
    updated_at DATETIME DEFAULT (datetime('now', 'localtime'))
);
```

#### `legend_keywords` 表 - 关键词配置

```sql
CREATE TABLE legend_keywords (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    legend_id TEXT NOT NULL,          -- 关联 Legend ID
    keyword_group TEXT,               -- 关键词组名称 (如 "人物名", "公司相关")
    keywords TEXT NOT NULL,           -- JSON 数组: ["马斯克", "Elon Musk"]
    source_hash TEXT,                 -- 来源 YAML 的哈希值（用于检测变化）
    created_at DATETIME DEFAULT (datetime('now', 'localtime')),
    updated_at DATETIME DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (legend_id) REFERENCES legends(id) ON DELETE CASCADE
);
CREATE INDEX idx_legend_keywords_legend_id ON legend_keywords(legend_id);
```

#### `legend_products` 表 - 核心产品/服务

```sql
CREATE TABLE legend_products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    legend_id TEXT NOT NULL,          -- 关联的 Legend ID
    product_name TEXT NOT NULL,       -- 产品名称
    description TEXT,                 -- 产品描述
    status TEXT,                      -- 状态: active | discontinued | upcoming
    category TEXT,                    -- 分类
    company_id TEXT,                  -- 所属公司（如果是产品）
    created_at DATETIME DEFAULT (datetime('now', 'localtime')),
    updated_at DATETIME DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (legend_id) REFERENCES legends(id) ON DELETE CASCADE
);
CREATE INDEX idx_legend_products_legend_id ON legend_products(legend_id);
```

#### `legend_companies` 表 - 人物关联公司

```sql
CREATE TABLE legend_companies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    person_id TEXT NOT NULL,          -- 人物 Legend ID
    company_id TEXT NOT NULL,         -- 公司 Legend ID
    role TEXT,                        -- 角色: CEO | Founder | CTO | Advisor
    is_primary BOOLEAN DEFAULT 0,     -- 是否主要公司
    start_date TEXT,                  -- 任期开始
    end_date TEXT,                    -- 任期结束（空表示现任）
    created_at DATETIME DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (person_id) REFERENCES legends(id) ON DELETE CASCADE,
    FOREIGN KEY (company_id) REFERENCES legends(id) ON DELETE CASCADE
);
CREATE INDEX idx_legend_companies_person_id ON legend_companies(person_id);
CREATE INDEX idx_legend_companies_company_id ON legend_companies(company_id);
```

#### `legend_sync_log` 表 - 同步日志

```sql
CREATE TABLE legend_sync_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sync_type TEXT NOT NULL,          -- scan | create | update | delete
    legend_id TEXT,                   -- 相关 Legend ID
    change_type TEXT,                 -- added | removed | keywords_changed
    details TEXT,                     -- JSON 详情
    synced_at DATETIME DEFAULT (datetime('now', 'localtime'))
);
CREATE INDEX idx_legend_sync_log_synced_at ON legend_sync_log(synced_at);
```

---

## 3. API Design

### 3.1 路由结构

```
/biz/legend_basedata
├── GET    /                         # 列出所有 Legends
├── GET    /{legend_id}              # 获取单个 Legend 详情
├── POST   /                         # 创建 Legend（手动）
├── PUT    /{legend_id}              # 更新 Legend
├── DELETE /{legend_id}              # 删除/归档 Legend
├── POST   /sync                     # 手动触发同步
├── GET    /sync/log                 # 查看同步日志
└── GET    /keywords                 # 获取所有关键词配置
```

### 3.2 API 端点详情

#### GET /biz/legend_basedata

列出所有 Legend 实体

**Query Parameters**:
- `type`: PERSON | ORGANIZATION（可选）
- `tier`: SINGULARITY | QUASI | POTENTIAL（可选）
- `limit`: 默认 100

**Response**:
```json
{
  "code": 200,
  "data": [
    {
      "id": "musk",
      "type": "PERSON",
      "name_en": "Elon Musk",
      "name_cn": "马斯克",
      "legend_tier": "SINGULARITY",
      "bio_short": "...",
      "file_path": "data/legend/people/musk.md"
    }
  ],
  "total": 10
}
```

#### GET /biz/legend_basedata/{legend_id}

获取 Legend 详情（含 Markdown 内容）

**Response**:
```json
{
  "code": 200,
  "data": {
    "legend": { ... },
    "keywords": [ ... ],
    "products": [ ... ],
    "companies": [ ... ],
    "markdown_content": "# Legend 档案\n\n..."
  }
}
```

#### POST /biz/legend_basedata/sync

手动触发同步（扫描 legend.yaml 和 nova.yaml）

**触发方式**: 管理后台按钮 / API 调用

**Request Body**:
```json
{
  "auto_fetch": false     // 是否自动调用 AI 搜索采集数据
}
```

**Response**:
```json
{
  "code": 200,
  "data": {
    "has_changes": true,
    "files": {
      "legend.yaml": "abc123...",
      "nova.yaml": "def456..."
    },
    "added": ["openai"],
    "removed": [],
    "updated": ["anthropic"],
    "unchanged": 7,
    "synced_at": "2026-02-02T10:30:00"
  }
}
```

---

## 4. Service Layer Design

### 4.1 文件结构

```
src/
├── models/
│   └── legend.py              # Legend 数据模型
├── services/
│   ├── legend_db.py           # LegendDB 数据库服务
│   ├── legend_file.py         # LegendFileService Markdown 文件服务
│   └── legend_sync.py         # LegendSyncService 同步服务（手动触发）
├── api/
│   └── biz/
│       └── legend_basedata.py # API 路由
└── tests/
    ├── test_legend_db.py
    ├── test_legend_file.py
    └── test_legend_sync.py
```

### 4.2 核心类设计

#### `LegendDB` 类

```python
class LegendDB:
    """Legend 数据库操作"""

    def __init__(self, db_path: str = "data/db/legend.sqlite"):
        ...

    # Legend CRUD
    def create_legend(self, legend: LegendCreate) -> str
    def get_legend(self, legend_id: str) -> Optional[Legend]
    def list_legends(self, filters: LegendFilters) -> List[Legend]
    def update_legend(self, legend_id: str, data: LegendUpdate) -> bool
    def delete_legend(self, legend_id: str) -> bool  # 软删除/归档

    # Keywords
    def set_keywords(self, legend_id: str, keywords: List[KeywordGroup]) -> None
    def get_keywords(self, legend_id: str) -> List[KeywordGroup]
    def keywords_changed(self, legend_id: str, new_keywords: List) -> bool

    # Products
    def add_product(self, legend_id: str, product: ProductCreate) -> int
    def list_products(self, legend_id: str) -> List[Product]

    # Companies
    def add_company_relation(self, person_id: str, company_id: str, role: str) -> int
    def list_person_companies(self, person_id: str) -> List[CompanyRelation]

    # Sync Log
    def log_sync(self, sync_type: str, legend_id: str = None, details: dict = None)
    def get_sync_logs(self, limit: int = 50) -> List[SyncLog]
```

#### `LegendFileService` 类

```python
class LegendFileService:
    """Markdown 档案文件服务"""

    def __init__(self, base_dir: str = "data/legend"):
        self.people_dir = Path(base_dir) / "people"
        self.orgs_dir = Path(base_dir) / "orgs"

    def create_person_file(self, legend_id: str, data: dict) -> str
    def create_org_file(self, legend_id: str, data: dict) -> str
    def read_file(self, legend_id: str, legend_type: str) -> Optional[str]
    def update_file(self, legend_id: str, content: str) -> bool
    def delete_file(self, legend_id: str, legend_type: str) -> bool
    def file_exists(self, legend_id: str, legend_type: str) -> bool

    # 模板渲染
    def render_person_template(self, data: dict) -> str
    def render_org_template(self, data: dict) -> str
```

#### `LegendSyncService` 类

```python
class LegendSyncService:
    """Legend 同步服务 - 核心"""

    def __init__(
        self,
        legend_path: str = "config/legend.yaml",
        nova_path: str = "config/nova.yaml",
        db: LegendDB = None,
        file_service: LegendFileService = None
    ):
        self.legend_path = Path(legend_path)
        self.nova_path = Path(nova_path)
        self.db = db or LegendDB()
        self.file_service = file_service or LegendFileService()

    async def sync(self, force: bool = False, auto_fetch: bool = False) -> SyncResult:
        """执行同步

        流程:
        1. 读取 legend.yaml 和 nova.yaml
        2. 计算哈希值，检测变化
        3. 对比现有数据库
        4. 识别新增/移除/变化的 Legend
        5. 提取所有 keywords (name_en + name_cn + keywords 展平)
        6. 执行相应操作
        7. 如果 auto_fetch=True，触发数据采集
        """
        ...

    def _extract_keywords(self, config: dict) -> Dict[str, List[str]]:
        """从配置中提取所有 keywords

        规则:
        - name_en: 提取
        - name_cn: 提取（如果有）
        - keywords: 展平后提取
        - 其他字段: 不提取

        返回: {legend_id: [keyword1, keyword2, ...]}
        """
        ...

    def _detect_legend_type(self, branch: str) -> str:
        """根据所在分支确定 Legend 类型

        规则:
        - people 分支 → PERSON
        - company 分支 → ORGANIZATION
        """
        ...
```

---

## 5. Implementation Tasks

### Phase 1: 数据库层 (Priority: P0)

- [ ] **Task 1.1**: 创建 `src/models/legend.py`
  - 定义 `LegendType`, `LegendTier`, `ImpactLevel` 枚举
  - 定义 `Legend`, `LegendKeyword`, `LegendProduct` Pydantic 模型
  - 定义 `LegendCreate`, `LegendUpdate`, `LegendFilters` DTO

- [ ] **Task 1.2**: 创建 `src/services/legend_db.py`
  - 实现 `LegendDB` 类
  - 实现 `init_db()` 创建所有表
  - 实现 Legend CRUD 方法
  - 实现 keywords/products/companies 关联方法
  - 实现 sync_log 方法

- [ ] **Task 1.3**: 单元测试 `tests/test_legend_db.py`
  - 测试表创建
  - 测试 CRUD 操作
  - 测试关联查询

### Phase 2: 文件服务层 (Priority: P0)

- [ ] **Task 2.1**: 创建 `src/services/legend_file.py`
  - 实现 `LegendFileService` 类
  - 实现 Markdown 文件读写
  - 实现模板渲染（使用 `legend_person_template.md` 和 `legend_org_template.md`）

- [ ] **Task 2.2**: 单元测试 `tests/test_legend_file.py`
  - 测试文件创建/读取/更新
  - 测试模板渲染

### Phase 3: 同步服务层 (Priority: P0)

- [ ] **Task 3.1**: 创建 `src/services/legend_sync.py`
  - 实现 `LegendSyncService` 类
  - 实现 YAML 解析和变化检测
  - 实现新增/移除/更新逻辑
  - 实现 Legend 类型推断

- [ ] **Task 3.2**: 集成 `/baidu-ai-search` skill
  - 创建 `src/researchers/fetcher.py`
  - 实现自动数据采集触发

- [ ] **Task 3.3**: 单元测试 `tests/test_legend_sync.py`
  - Mock YAML 文件测试
  - 测试变化检测逻辑
  - 测试类型推断

### Phase 4: API 层 (Priority: P1)

- [ ] **Task 4.1**: 创建 `src/api/biz/legend_basedata.py`
  - 实现所有 API 端点
  - 添加请求验证
  - 添加错误处理

- [ ] **Task 4.2**: 集成到 `src/main.py`
  - 注册 `/biz/legend_basedata` 路由
  - 初始化 LegendDB

### Phase 5: 手动触发支持 (Priority: P1)

- [ ] **Task 5.1**: 更新同步服务
  - 实现文件哈希对比
  - 无变化时返回 early
  - 移除定时调度相关代码

- [ ] **Task 5.2**: 管理后台刷新按钮（可选）
  - 添加简单的前端刷新按钮
  - 调用 `/biz/legend_basedata/sync`

---

## 6. Dependencies

| 模块 | 依赖 |
|------|------|
| models/legend.py | pydantic, typing |
| services/legend_db.py | sqlite3, pathlib, models.legend |
| services/legend_file.py | pathlib, jinja2 (模板渲染) |
| services/legend_sync.py | yaml, hashlib, services.legend_db, services.legend_file |
| api/biz/legend_basedata.py | fastapi, services.* |

**外部依赖**:
- `config/legend.yaml` - 奇点实体配置（手动维护）
- `config/nova.yaml` - 超新星实体配置（手动维护）
- `design/legend/legend_person_template.md` - 人物模板
- `design/legend/legend_org_template.md` - 组织模板
- 智谱 AI 搜索（`https://open.bigmodel.cn/api/paas/v4/`） - 数据采集

---

## 7. Risk & Mitigation

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 配置文件格式变化 | 同步失败 | 添加格式验证和错误日志 |
| Legend 类型推断错误 | 档案分类错误 | 由配置文件分支决定，无需推断 |
| Markdown 文件冲突 | 数据覆盖 | 添加版本控制/备份 |
| SQLite 并发冲突 | 数据损坏 | 使用 WAL 模式 |

---

## 8. Testing Strategy

1. **单元测试**: 覆盖所有核心方法，目标覆盖率 80%+
2. **集成测试**: 测试完整同步流程
3. **Mock 测试**: Mock `/baidu-ai-search` 外部调用
4. **边界测试**: 测试空 YAML、格式错误等边界情况

---

## 9. Success Criteria

- [ ] 能够正确解析 `legend.yaml` 和 `nova.yaml`
- [ ] 能够按规则提取所有 keywords (name_en + name_cn + keywords)
- [ ] 能够检测并处理新增/移除/内容变化
- [ ] 能够创建符合模板的 Markdown 档案
- [ ] 能够通过 API 查询和管理 Legend 数据
- [ ] 单元测试覆盖率 >= 80%
- [ ] 所有验收标准达成

---

## 10. Scene 0: AI 档案自动采集 (扩展设计)

### 10.1 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                    legend_sync                              │
│  - 扫描 legend.yaml                                          │
│  - 检测变更（新增/删除/修改）                                  │
│  - 更新内存中的 legend dict 和 keywords dict                  │
│  - 新增时调用 researcher                                     │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    researcher                               │
│  - 接收新增的 legend 数据包                                   │
│  - 拆解研究任务（company / people / product）                 │
│  - 循环调用 queryer                                          │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    queryer                                  │
│  - 读取 YAML 模板（company_query.yaml 等）                   │
│  - 循环调用 AI 查询（每段间隔 1 秒）                           │
│  - 调用 render 生成 Markdown                                  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    render                                   │
│  - 分为 CompanyRender / PeopleRender / ProductRender         │
│  - 接收多次查询结果                                           │
│  - to_markdown() 生成完整内容                                 │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    saver                                    │
│  - 读取 research_config.yaml 获取输出路径                     │
│  - 保存到 data/company/ / data/people/ / data/product/       │
└─────────────────────────────────────────────────────────────┘
```

### 10.2 组件职责

| 组件 | 职责 |
|------|------|
| **legend_sync** | 扫描配置、检测变更、更新内存、新增时调用 researcher |
| **researcher** | 拆解任务（company/people/product）、循环调用 queryer |
| **queryer** | 读取 YAML 模板、循环 AI 查询、调用 render |
| **render** | 累积查询结果、生成 Markdown |
| **saver** | 读取配置、保存文件 |

### 10.3 YAML 模板格式

**config/research/company_query.yaml**:
```yaml
queries:
  - search: "{name_cn} {name_en} 公司介绍 成立时间 创始人"
    instruction: |
      请搜集 {name_cn} ({name_en}) 的以下信息，按 Markdown 格式输出：
      ## 公司基础信息
      - **ID**：{id}
      - **英文名**：{name_en}
      - **中文名**：{name_cn}
      - **成立时间**：
      - **总部地点**：
      - **简短介绍**：

  - search: "{name_cn} {name_en} 产品 服务 业务模式"
    instruction: |
      ## 核心产品/服务
      ...

  - search: "{name_cn} {name_en} 发展史 里程碑 融资"
    instruction: |
      ## 发展历程
      ...
```

### 10.4 配置文件

**config/research_config.yaml**:
```yaml
# AI 档案采集配置
# entity_type 可选值: legend | nova | front

# 按内容类型配置输出路径模板，程序自动叠加 {entity_type}
output_paths:
  company: "data/{entity_type}/company"
  people: "data/{entity_type}/people"
  product: "data/{entity_type}/product"

# 查询模板配置
templates:
  company: "config/research/company_query.yaml"
  people: "config/research/people_query.yaml"
  product: "config/research/product_query.yaml"

# AI 查询参数配置
query_params:
  max_results: 10
  search_recency: "year"
  query_interval: 1
  max_completion_tokens: 8192
```

### 10.5 文件清单

| 文件 | 说明 | 状态 |
|------|------|------|
| config/research_config.yaml | 研究配置 | 待创建 |
| config/research/company_query.yaml | 公司查询模板 | 待创建 |
| config/research/people_query.yaml | 人物查询模板 | 待创建 |
| config/research/product_query.yaml | 产品查询模板 | 待创建 |
| src/services/queryer.py | 通用查询器 | 待创建 |
| src/services/render.py | 渲染器 | 待创建 |
| src/services/saver.py | 保存器 | 待创建 |
| src/services/researcher.py | 研究员调度（重构） | 待修改 |
| src/services/legend_sync.py | 同步服务（修改） | 待修改 |

### 10.6 实现步骤

1. **创建配置和模板文件** - research_config.yaml, *_query.yaml
2. **实现 queryer** - 通用查询器
3. **实现 render** - 三种渲染器
4. **实现 saver** - 保存器
5. **重构 researcher** - 任务拆解器
6. **集成到 legend_sync** - 调用 researcher
