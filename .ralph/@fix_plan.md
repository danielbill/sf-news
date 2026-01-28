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

## Completed
- [x] 阶段0: 基础设施（配置系统、测试通过）
- [x] 阶段1: 快速迭代 Demo（抓取API、前端页面）
- [x] 阶段2: 通用爬虫框架（三层去重、动态解析器、9个新闻源解析器）
- [x] 阶段4: 定时任务（APScheduler调度器、38个测试通过）
- [x] 拆分华尔街见闻和财联社解析器（live/news/telegraph/depth）

## Notes
### 定时任务约束
- **最小抓取间隔**: 15分钟（900秒），不能设置更小
- **启动行为**: 服务启动后默认立刻执行一次抓取

### API 端点
| 方法 | 路径 | 功能 |
|------|------|------|
| GET | `/api/scheduler/status` | 获取调度器状态 |
| POST | `/api/scheduler/start` | 启动调度器 |
| POST | `/api/scheduler/stop` | 停止调度器 |
| POST | `/api/scheduler/pause` | 暂停调度器 |
| POST | `/api/scheduler/resume` | 恢复调度器 |
| GET | `/api/scheduler/jobs` | 获取任务历史 |
