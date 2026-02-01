# Legend 资料库设计



---

## 资料类型

| 类型 | 代码 | 模板文件 |
|------|------|----------|
| 人物 | PERSON | legend_person_template.md |
| 组织 | ORGANIZATION | legend_org_template.md |

---

## 字段定义

### 一、人物档案 (PERSON)

#### 1. 基础信息
- `id` - 唯一标识
- `name_en` / `name_cn` - 英文名/中文名
- `avatar_url` - 头像URL
- `birth_year` - 出生年份
- `nationality` - 国籍
- `education` - 教育背景
- `bio_short` - 简短介绍（100字）
- `bio_full` - 完整介绍

#### 2. 家庭背景
- `family_background` - 家庭背景描述
- `family_members` - 家庭成员列表（关系/姓名/备注）

#### 3. 伟愿与理念
- `vision_statement` - 伟愿声明
- `core_beliefs` - 核心信念列表
- `famous_quotes` - 金句库（金句/来源/日期）

#### 4. 工作与公司
- `current_focus` - 当下工作重心
- `companies` - 关联公司列表（公司/角色/任期）
- `core_products` - 核心产品/服务

#### 5. 影响力
- `influence_scope` - 影响力范围
- `influence_metrics` - 影响力指标
- `civilization_impact` - 文明级影响描述
- `impact_level` - 影响等级（SINGULARITY/INDUSTRY/COMPANY）
- `legend_tier` - 传奇等级（SINGULARITY/QUASI/POTENTIAL）

#### 6. 里程碑
- `milestones` - 关键事件列表（日期/事件/影响）

---

### 二、组织档案 (ORGANIZATION)

#### 1. 基础信息
- `id` - 唯一标识
- `name_en` / `name_cn` - 英文名/中文名
- `logo_url` - Logo URL
- `founded_year` - 成立年份
- `headquarters` - 总部地点
- `type` - 组织类型（PUBLIC/PRIVATE/NONPROFIT）
- `stock_code` - 股票代码（如上市）
- `bio_short` - 简短介绍
- `bio_full` - 完整介绍

#### 2. 领导层
- `founders` - 创始人列表（人物ID/姓名/角色）
- `current_leadership` - 现任领导层（人物ID/姓名/职位）

#### 3. 商业与产品
- `business_model` - 商业模式描述
- `revenue_streams` - 收入来源
- `core_products` - 核心产品/服务

#### 4. 财务信息
- `market_cap` - 市值
- `revenue` - 年营收
- `revenue_growth` - 营收增长率
- `profit` - 净利润
- `funding` - 融资情况（非上市公司）
- `cash_position` - 现金储备

#### 5. 股权与竞争
- `ownership_structure` - 股权结构
- `industry` - 所属行业
- `market_position` - 市场地位
- `main_competitors` - 主要竞争对手
- `key_differentiators` - 核心优势

#### 6. 使命与影响力
- `vision_statement` - 使命/愿景
- `core_values` - 核心价值观
- `mission` - 使命描述
- `influence_scope` - 影响力范围
- `influence_metrics` - 影响力指标
- `civilization_impact` - 文明级影响
- `impact_level` - 影响等级
- `legend_tier` - 传奇等级

#### 7. 里程碑
- `milestones` - 关键事件列表

---

## 等级定义

### Legend Tier（传奇等级）
| 等级 | 定义 |
|------|------|
| SINGULARITY | 奇点 — 引发文明级跃迁 |
| QUASI | 准奇点 — 引发行业级变革 |
| POTENTIAL | 潜力 — 有可能成为奇点 |

### Impact Level（影响等级）
| 等级 | 定义 |
|------|------|
| SINGULARITY | 文明级 — 改变人类文明进程 |
| INDUSTRY | 行业级 — 重塑某个行业 |
| COMPANY | 公司级 — 影响公司自身 |

### Organization Type（组织类型）
| 类型 | 定义 |
|------|------|
| PUBLIC | 上市公司 |
| PRIVATE | 私营公司 |
| NONPROFIT | 非营利组织 |
