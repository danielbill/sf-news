# 模块 1: 奇点档案数据库

**层级**: 数据基础层
**状态**: 待实现
**优先级**: P0 - 必须最先实现，其他模块依赖此模块

## 功能描述

Legend 实体的基础信息存储和维护，支持人物(PERSON)和组织(ORGANIZATION)两种类型的档案 CRUD 操作。

## 验收标准

- [ ] 支持 Legend 实体的创建、读取、更新、删除操作
- [ ] 支持人物和组织两种类型
- [ ] 支持字段按 [legend_database_design.md](../../../../design/legend/legend_database_design.md) 定义
- [ ] 提供数据验证和错误处理
- [ ] 数据可被其他 11 个模块读取使用

## 依赖

- 无前置依赖（这是基础模块）

## 输出物

- `models/legend.py` - Legend 数据模型
- `api/legend.py` - Legend CRUD API
- `tests/test_legend.py` - 单元测试
