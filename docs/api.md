# API 文档

## 新闻抓取 API

| 方法 | 路径 | 功能 |
|------|------|------|
| POST | `/api/crawl/trigger` | 手动触发抓取 |
| GET | `/api/articles` | 获取今日新闻列表 |
| GET | `/api/articles/{id}` | 获取单篇文章详情 |

## 调度器 API

| 方法 | 路径 | 功能 |
|------|------|------|
| GET | `/api/scheduler/status` | 获取调度器状态 |
| POST | `/api/scheduler/start` | 启动调度器 |
| POST | `/api/scheduler/stop` | 停止调度器 |
| POST | `/api/scheduler/pause` | 暂停调度器 |
| POST | `/api/scheduler/resume` | 恢复调度器 |
| GET | `/api/scheduler/jobs` | 获取任务历史 |

## 管理后台 API

| 方法 | 路径 | 功能 |
|------|------|------|
| POST | `/admin/cleartodaynews` | 清空今日数据（数据库+文件+缓存） |
| GET | `/admin/source_test` | 测试所有新闻源状态 |
