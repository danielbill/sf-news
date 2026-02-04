# Feature Specification: 奇点研究员系统

**Feature Branch**: `000-legend-researcher`
**Created**: 2026-02-02
**Status**: Draft
**Input**: 想法文件 [奇点研究员功能](../../.specify/ideas/奇点研究员.md)

## 概述

奇点研究员是项目的核心分析引擎，每日主动运行，采集多种数据源，分析新闻和动态，给出奇点前沿的真实发展变化。它将奇点变化纳入经济模型计算，推导其对世界 GDP 的带动情况。

## 系统架构

奇点研究员由 12 个独立功能模块组成，分为 4 层架构：

```
┌─────────────────────────────────────────────────────────────┐
│                    数据基础层                                 │
│  模块1: 奇点档案数据库                                        │
└────────────────────────┬────────────────────────────────────┘
                         │
         ┌───────────────┴───────────────┐
         │                               │
         ▼                               ▼
┌─────────────────────┐       ┌─────────────────────┐
│  外部数据采集层       │       │  情报分析层          │
│  模块2: 财经数据同步   │ ──>   │  模块3-9            │
└─────────────────────┘       └─────────┬───────────┘
                                       │
                                       ▼
                              ┌─────────────────────┐
                              │  经济模型层           │
                              │  模块10-12           │
                              └─────────────────────┘
```

## 用户场景与验收标准

### 场景 0: 自动采集奇点档案数据

**用户工作界面**: `config/legend.yaml` 和 `config/nova.yaml`

用户新增 Legend 实体到配置文件后，点击"刷新"按钮，系统建立档案并调用 AI 搜索采集基础信息，生成 Markdown 档案文件。

**用户操作流程**:
1. 用户在 `config/legend.yaml` 或 `config/nova.yaml` 中添加新的 Legend 定义
   - `people` 下添加人物实体（包含旗下公司）
   - `company` 下添加公司实体（包含关键人物）
2. 用户在管理后台点击"刷新"按钮，调用 `/biz/legend_basedata/sync` API
3. 系统扫描配置文件，更新 keywords，供新闻筛选用。
4. 系统调用AI 搜索采集相关信息
5. 系统自动生成对应的 Markdown 档案文件

**配置文件格式**:
```yaml
# legend.yaml (奇点实体 - 已验证)
people:
  musk:
    keywords: [["马斯克", "埃隆·马斯克", "Elon Musk"]]
    companies:
      - tesla:
          name_en: Tesla
          name_cn: 特斯拉
          key_roles: []
          products:
            - name: Tesla Bot
              keywords: ["Tesla Bot", "擎天柱", "Optimus"]

company:
  anthropic:
    name_en: Anthropic
    name_cn:
    key_roles:
      - name: 达里奥·阿莫迪
        keywords: ["Dario Amodei", "达里奥·阿莫迪"]
    products:
      - name: claude
        keywords: ["claude"]
```

**验收标准**:
- 系统能够正确解析 `legend.yaml` 和 `nova.yaml`
- 系统能够提取所有 keywords 用于新闻筛选（name_en, name_cn, keywords 展平）
- 系统能够根据 Legend 所在分支（people/company）选择合适的搜索策略
- 系统能够使用智谱 AI 搜索 API 获取并提取结构化档案数据
- 系统能够自动填充档案模板，生成完整的 Markdown 文件
- 生成的档案包含：基础信息、创始人/核心人物、成立时间、业务描述、里程碑等
- 采集失败时记录错误日志，不影响数据库记录的创建
- 档案数据来源可追溯，标注采集时间和来源

**技术实现要点**:
- 使用 OpenAI SDK 兼容模式调用智谱 AI 搜索接口（`base_url: https://open.bigmodel.cn/api/paas/v4/`）
- Keywords 提取规则：name_en + name_cn（如有）+ keywords（展平）
- 搜索策略：根据实体所在分支（people 用"创始人"，company 用"公司"）构造搜索词
- AI 提取：利用搜索结果的 AI 总结能力，提取结构化数据填充模板
- 模板填充：复用现有的 `legend_org_template.md` 和 `legend_person_template.md`

### 场景 1: 查看奇点完整发展脉络

用户可以查看某个奇点的完整发展情况，从奇点实体到全产业链，了解其如何推动文明变化。

**验收标准**:
- 用户能够看到奇点的基础信息（档案数据）
- 用户能够看到奇点当前的战略方向和口号
- 用户能够看到奇点所处赛道及竞争格局
- 用户能够看到上下游供应链关系
- 用户能够看到重大项目的落地进展

### 场景 2: 理解经济影响

用户能够看到奇点对经济的定量影响，包括 GDP 拉动效应和实体价值增长预测。

**验收标准**:
- 用户能够看到奇点核心实体的估值数据
- 用户能够看到对国家/全球 GDP 的影响估算
- 用户能够看到未来 1-3 年的价值增长速度预测

### 场景 3: 获取全球态势

用户能够看到全球范围内针对该奇点的竞争/合作态势。

**验收标准**:
- 用户能够看到各国政策对奇点的支持情况
- 用户能够看到全球竞争对手的动态
- 用户能够看到各方对奇点的观点和评价

## 功能模块清单

详见 [checklists/](checklists/) 目录：

| 模块                   | 文件                                                                        | 状态   |
| ---------------------- | --------------------------------------------------------------------------- | ------ |
| 模块 1: 奇点档案数据库 | [module-01-database.md](checklists/module-01-database.md)                   | 待实现 |
| 模块 2: 财经数据同步   | [module-02-finance.md](checklists/module-02-finance.md)                     | 待实现 |
| 模块 3: 战略口号跟踪   | [module-03-strategy.md](checklists/module-03-strategy.md)                   | 待实现 |
| 模块 4: 赛道竞争分析   | [module-04-track.md](checklists/module-04-track.md)                         | 待实现 |
| 模块 5: 供应链监测     | [module-05-supply-chain.md](checklists/module-05-supply-chain.md)           | 待实现 |
| 模块 6: 项目进展追踪   | [module-06-projects.md](checklists/module-06-projects.md)                   | 待实现 |
| 模块 7: 国策配套分析   | [module-07-policy.md](checklists/module-07-policy.md)                       | 待实现 |
| 模块 8: 全球备战态势   | [module-08-global-stance.md](checklists/module-08-global-stance.md)         | 待实现 |
| 模块 9: 观点情绪聚合   | [module-09-sentiment.md](checklists/module-09-sentiment.md)                 | 待实现 |
| 模块 10: 估值模型      | [module-10-valuation.md](checklists/module-10-valuation.md)                 | 待实现 |
| 模块 11: GDP 拉动计算  | [module-11-gdp-impact.md](checklists/module-11-gdp-impact.md)               | 待实现 |
| 模块 12: 增长速度预测  | [module-12-growth-prediction.md](checklists/module-12-growth-prediction.md) | 待实现 |

## 数据采集手段

奇点研究员可重复使用所有手段进行数据采集：

| 手段                 | 用途                               |
| -------------------- | ---------------------------------- |
| `/baidu-ai-search`   | 智能信息聚合采集                   |
| `/github-kb`         | 在 GitHub 上找到符合需求的各种工具 |
| `flaskSite1` 项目    | 财经数据采集接口及数据库           |
| 新闻采集业务（已有） | 新闻源数据                         |

## 依赖关系

**技术依赖**：
- 本项目中的**新闻采集业务**（核心依赖）
- 财务数据模块（专业财经 API）
- 公司档案模块（手动维护，AI 辅助）

**业务依赖**：
- Legend 实体库需要有一定数据积累
- 关键词配置系统
- 数据存储和处理管道

**未来扩展**：
- 关联分析模块（后期实现，智能关联）
- 用户订阅和付费系统
- 可视化 Dashboard

## 成功标准

- 用户能够 2 次点击内看到奇点的完整发展脉络
- 用户能够看到定量化的经济影响数据（GDP、估值、增长速度）
- 系统每日自动更新数据，更新间隔不超过 24 小时
- 数据来源可追溯，标注数据来源和更新时间

## 相关链接

- [奇点档案设计理念](../../design/legend/奇点档案设计理念.md)
- [Legend 资料库设计](../../design/legend/legend_database_design.md)
- [项目核心理念](../../.README.md)
- [001 奇点实体管理](../001-legend-entities/spec.md) - 前置依赖
