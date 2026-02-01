# 测试规范

## 测试文件位置

所有测试文件位于 `tests/` 目录，**不要在根目录创建临时测试文件**。

## 常用测试命令

```bash
# 运行所有测试
pytest tests/

# 运行特定测试文件
pytest tests/test_keywords.py
pytest tests/test_config.py
pytest tests/test_scheduler.py

# 运行测试并显示详细输出
pytest tests/ -v

# 运行测试并显示打印输出
pytest tests/ -s
```

## 测试文件说明

| 文件 | 用途 | 运行方式 |
|------|------|----------|
| `test_keywords.py` | 测试关键词筛选功能 | `pytest tests/test_keywords.py -s` |
| `test_config.py` | 测试配置加载 | `pytest tests/test_config.py` |
| `test_storage.py` | 测试数据库操作 | `pytest tests/test_storage.py` |
| `test_new_features.py` | 测试去重、URL缓存 | `pytest tests/test_new_features.py` |
| `test_scheduler.py` | 测试调度器 | `pytest tests/test_scheduler.py` |
| `conftest.py` | pytest fixtures，无需直接运行 | - |

## 测试覆盖率目标

最低测试覆盖率：**80%**
