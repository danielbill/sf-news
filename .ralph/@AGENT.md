# Singularity Front - 构建/运行指令

## 项目环境

**Python 版本**：3.11+

## 开发环境设置

```bash
# 进入项目目录
cd d:\ai_tools\Singularity-Front

# 创建虚拟环境（推荐）
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

---

## 运行测试

```bash
# 运行所有测试
pytest

# 运行特定模块测试
pytest tests/test_news_crawler.py

# 带覆盖率报告
pytest --cov=src --cov-report=term-missing

# 运行单个测试
pytest tests/test_news_crawler.py::test_cankaoxiaoxi_fetch
```

---

## 启动开发服务器

```bash
# 启动 FastAPI 开发服务器
uvicorn src.main:app --reload --port 8000

# 或使用 Python 模块运行
python -m src.main
```

访问：http://localhost:8000

API 文档：http://localhost:8000/docs

---

## 代码质量检查

```bash
# 类型检查
mypy src/

# 代码格式化
black src/ tests/

# 导入排序
isort src/ tests/

# Linting
flake8 src/ tests/
```

---

## 数据库操作

```bash
# 初始化数据库
python -m src.scripts.init_db

# 创建今日 Timeline DB
python -m src.scripts.create_timeline_db

# 查看数据库内容
sqlite3 data/db/timeline_$(date +%Y-%m-%d).sqlite "SELECT * FROM articles LIMIT 10;"
```

---

## 手动运行爬虫

```bash
# 运行所有爬虫
python -m src.scripts.run_crawlers

# 运行单个爬虫
python -m src.crawlers.cankaoxiaoxi

# 运行爬虫并输出详细日志
python -m src.crawlers.cankaoxiaoxi --verbose
```

---

## 定时任务

```bash
# 启动调度器（后台运行）
python -m src.scheduler

# 查看调度器状态
curl http://localhost:8000/api/scheduler/status
```

---

## Git 工作流

```bash
# 添加更改
git add .

# 提交（使用约定式提交）
git commit -m "feat(crawler): 实现参考消息爬虫"

# 推送
git push origin feature/news-crawler
```

### 约定式提交格式

- `feat:` 新功能
- `fix:` Bug 修复
- `docs:` 文档更新
- `test:` 测试相关
- `refactor:` 重构
- `chore:` 构建/工具链

---

## 关键学习点

### 数据源 API 调用

参考 `D:\awesome_projects\newsnow` 中的实现：
- 使用 httpx 进行异步 HTTP 请求
- 注意反爬策略（User-Agent、Referer 等）
- 解析 JSON 或 HTML 响应

### Timeline DB 创建

每天一个 SQLite 文件，自动按日期命名：
```python
from datetime import datetime
db_path = f"data/db/timeline_{datetime.now().strftime('%Y-%m-%d')}.sqlite"
```

### 元数据/文件分离

```python
# 元数据存入 SQLite
# 正文存为文件
import uuid
from pathlib import Path

article_id = str(uuid.uuid4())
file_path = f"articles/{datetime.now().strftime('%Y/%m/%d')}/{article_id}.md"
Path(file_path).parent.mkdir(parents=True, exist_ok=True)
Path(file_path).write_text(content)
```

---

## 常见问题

### 依赖安装失败
```bash
# 升级 pip
pip install --upgrade pip

# 使用国内镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 数据库锁定
SQLite 写入时可能锁定，确保：
1. 单写多读
2. 写入操作使用上下文管理器
3. 及时关闭连接

### 爬虫被反爬
1. 添加请求间隔（随机 2-5 秒）
2. 使用 User-Agent 轮换
3. 必要时使用代理 IP
