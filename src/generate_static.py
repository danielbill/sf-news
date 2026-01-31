"""静态页面生成器

从数据库读取当日新闻，生成预渲染的静态 HTML 页面。
"""

import shutil
import sqlite3
from datetime import date, datetime
from pathlib import Path

from jinja2 import Template


def format_time(iso_string: str) -> str:
    """格式化时间为 MM-DD HH:MM"""
    if not iso_string:
        return ""
    try:
        dt = datetime.fromisoformat(iso_string)
        return dt.strftime("%m-%d %H:%M")
    except (ValueError, TypeError):
        return iso_string


def copy_static_files():
    """复制 static/images 到 docs/site/static/images（增量复制）"""
    src = Path("static/images")
    dst = Path("docs/site/static/images")

    if not src.exists():
        print(f"[Warning] static/images 目录不存在: {src}")
        return

    # 确保目标目录存在
    dst.mkdir(parents=True, exist_ok=True)

    # 增量复制：只复制新文件或修改过的文件
    copied_count = 0
    for file in src.rglob("*"):
        if file.is_file():
            relative_path = file.relative_to(src)
            dest_file = dst / relative_path

            # 只有当目标不存在或源文件更新时才复制
            if not dest_file.exists() or file.stat().st_mtime > dest_file.stat().st_mtime:
                dest_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(file, dest_file)
                copied_count += 1

    print(f"[Generate] 已复制 {copied_count} 个图片文件到 {dst}")


def generate_static_html():
    """生成静态 HTML 页面（仅当日新闻）"""

    # 1. 读取今日数据库
    db_path = Path(f"data/db/timeline_{date.today().strftime('%Y-%m-%d')}.sqlite")

    articles = []
    if db_path.exists():
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(
            "SELECT * FROM articles ORDER BY timestamp DESC LIMIT 100"
        )
        articles = [dict(row) for row in cursor.fetchall()]
        conn.close()
    else:
        print(f"[Warning] 数据库不存在: {db_path}")

    # 2. 按 legend 字段分组，并格式化时间
    for article in articles:
        article["formatted_time"] = format_time(article.get("timestamp"))

    timeline_articles = [a for a in articles if a.get('legend')]
    trending_articles = [a for a in articles if not a.get('legend')]

    print(f"[Generate] 时间线新闻: {len(timeline_articles)} 条")
    print(f"[Generate] 前沿资讯: {len(trending_articles)} 条")

    # 3. 使用 Jinja2 渲染模板
    template_path = Path("templates/static_index.html")
    if not template_path.exists():
        print(f"[Error] 模板文件不存在: {template_path}")
        return 0

    template = Template(template_path.read_text(encoding="utf-8"))
    html = template.render(
        timeline_articles=timeline_articles,
        trending_articles=trending_articles,
        date=date.today().isoformat()
    )

    # 4. 写入 docs/site/ 目录（GitHub Pages 发布源）
    output_path = Path("docs/site/index.html")
    output_path.parent.mkdir(exist_ok=True)
    output_path.write_text(html, encoding="utf-8")

    # 5. 复制 static 目录
    copy_static_files()

    print(f"[Generate] 已生成静态页面: {output_path}")
    return len(articles)


if __name__ == "__main__":
    count = generate_static_html()
    print(f"[Generate] 共 {count} 条当日新闻")
