# 前端架构文档

## 两种运行模式

| 模式 | 文件 | CSS/JS | 用途 |
|------|------|--------|------|
| **本地开发** | `templates/index.html` | `/static/css/index.css` + `/static/js/index.js` | FastAPI 动态服务 |
| **GitHub Pages** | `docs/index.html` | 样式内联，静态预渲染 | 纯静态托管 |

## 数据流

### 本地开发模式

```
浏览器 → / → FastAPI 返回 templates/index.html
         ↓
    加载 /static/js/index.js
         ↓
    fetch('/api/articles') → FastAPI 从 SQLite 读取 → JSON 返回
         ↓
    index.js 动态渲染页面
```

### GitHub Pages 模式

```
运行 python -m src.generate_static
         ↓
从今日 SQLite 读取数据
         ↓
使用 Jinja2 渲染 templates/static_index.html（预渲染）
         ↓
生成 docs/index.html（样式内联）
         ↓
GitHub Pages 自动发布
```

## 关键文件职责

| 文件 | 职责 |
|------|------|
| `static/css/index.css` | 首页样式（给本地开发 `templates/index.html` 用） |
| `static/js/index.js` | 数据绑定和动态渲染（fetch API + DOM 操作） |
| `templates/index.html` | 本地开发动态模板 |
| `templates/static_index.html` | GitHub Pages 静态模板 |
| `src/generate_static.py` | 静态页面生成器 |

## 修改前端注意事项

1. **修改本地开发界面**：改 `templates/index.html`、`static/css/index.css`、`static/js/index.js`
2. **修改 GitHub Pages 界面**：改 `templates/static_index.html`，然后运行 `python -m src.generate_static`
3. **两者都要改**：需要同步修改两处，保持一致

## 图像资源

- `static/images/people/` - 奇点人物头像
- `static/images/companies/` - 奇点组织 Logo
- 动态背景图根据新闻 `legend` 字段切换

## 页面设计索引

详见 [design/README.md](../design/README.md)
