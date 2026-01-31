# Singularity Front - Ralph Fix Plan

## High Priority (阶段4: 定时任务)
- [x] 添加 APScheduler>=3.10.0 到 requirements.txt
- [x] 更新 config/crawler_config.yaml 添加调度参数
- [x] 更新 src/config/models.py StrategyConfig
- [x] 创建 src/scheduler/ 目录结构
- [x] 创建 src/scheduler/store.py
- [x] 创建 src/scheduler/scheduler.py
- [x] 创建 src/api/scheduler.py
- [x] 在 src/main.py 集成调度器
- [x] 创建 tests/test_scheduler.py

## High Priority (阶段8: 管理功能)
- [x] 创建 src/crawlers/source_tester.py - 新闻源测试器
- [x] 创建 src/api/admin.py - 管理后台 API
- [x] 实现 POST /admin/cleartodaynews - 清空今日数据
- [x] 实现 GET /admin/source_test - 测试新闻源
- [x] 在 templates/index.html 添加测试按钮和弹窗
- [x] 修复关键词配置格式（字符串改数组）
- [x] 修复关键词误匹配（"生态" → "英伟达生态"）

## High Priority (阶段6: 前端设计定稿)
- [x] 确定首页视觉设计 (design/index-news.html)
- [ ] 将设计应用到实际前端模板
- [ ] 实现数据绑定
- [ ] 添加交互功能

## Completed
- [x] 阶段0: 基础设施（配置系统、测试通过）
- [x] 阶段1: 快速迭代 Demo（抓取API、前端页面）
- [x] 阶段2: 通用爬虫框架（三层去重、动态解析器、9个新闻源解析器）
- [x] 阶段4: 定时任务（APScheduler调度器、38个测试通过）
- [x] 拆分华尔街见闻和财联社解析器（live/news/telegraph/depth）
- [x] 阶段8: 管理功能（新闻源测试、清空数据）
- [x] 阶段6: 前端设计定稿（design/index-news.html）

## Notes
### 定时任务约束
- **最小抓取间隔**: 15分钟（900秒），不能设置更小
- **启动行为**: 服务启动后默认立刻执行一次抓取

### 关键词配置约束
- **格式**: 必须使用数组格式 `["关键词"]`，不能使用字符串格式
- **原因**: Python `set.update("string")` 会将字符串拆分成单个字符
- **精度**: 使用更精确的关键词避免误匹配（如"英伟达生态"而非"生态"）

### API 端点
#### 调度器 API
| 方法 | 路径 | 功能 |
|------|------|------|
| GET | `/api/scheduler/status` | 获取调度器状态 |
| POST | `/api/scheduler/start` | 启动调度器 |
| POST | `/api/scheduler/stop` | 停止调度器 |
| POST | `/api/scheduler/pause` | 暂停调度器 |
| POST | `/api/scheduler/resume` | 恢复调度器 |
| GET | `/api/scheduler/jobs` | 获取任务历史 |

#### 管理后台 API
| 方法 | 路径 | 功能 |
|------|------|------|
| POST | `/admin/cleartodaynews` | 清空今日数据（数据库+文件+缓存） |
| GET | `/admin/source_test` | 测试所有新闻源状态 |

