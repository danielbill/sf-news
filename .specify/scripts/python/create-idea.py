#!/usr/bin/env python3
"""
Create idea file with proper Chinese filename support.
"""

import argparse
import json
import os
import re
from datetime import datetime
from pathlib import Path

def find_repo_root():
    """Find repository root by looking for .git or .specify directory."""
    cwd = Path.cwd()
    for parent in [cwd] + list(cwd.parents):
        if (parent / ".git").exists() or (parent / ".specify").exists():
            return parent
    raise RuntimeError("Could not find repository root")

def sanitize_filename(text: str) -> str:
    """Create safe filename from text, preserving Chinese characters."""
    # Remove leading/trailing whitespace
    text = text.strip()
    # Replace special chars with dash, keep alphanumeric and Chinese
    # Chinese range: \u4e00-\u9fff
    result = []
    for char in text:
        if char.isalnum() or '\u4e00' <= char <= '\u9fff':
            result.append(char)
        elif result and result[-1] != '-':
            result.append('-')
    # Remove trailing dash
    filename = ''.join(result).rstrip('-')
    return filename if filename else f"idea-{datetime.now().strftime('%Y%m%d%H%M%S')}"

def create_idea(description: str, importance: int = 2, json_mode: bool = False):
    """Create a new idea file."""
    repo_root = find_repo_root()
    ideas_dir = repo_root / ".specify" / "ideas"
    ideas_dir.mkdir(parents=True, exist_ok=True)

    # Use description as title
    title = description[:50] + "..." if len(description) > 50 else description

    # Create safe filename
    safe_name = sanitize_filename(description)
    idea_file = ideas_dir / f"{safe_name}.md"

    # Handle duplicate filenames
    if idea_file.exists():
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        idea_file = ideas_dir / f"{safe_name}-{timestamp}.md"

    # Get current date
    date = datetime.now().strftime('%Y-%m-%d')

    # Read template
    template_path = ideas_dir / "idea-template.md"
    if template_path.exists():
        content = template_path.read_text(encoding='utf-8')
        content = content.replace('[TITLE]', title)
        content = content.replace('[DATE]', date)
        content = content.replace('[3 | 2 | 1] (3=最重要)', str(importance))
        content = content.replace('[📝待整理 | 💡已确认 | ✅已完成]', '📝待整理')
        content = content.replace('[简要描述这个想法是什么]', description)
    else:
        # Fallback template
        content = f"""# 想法: {title}

**创建日期**: {date}
**重要度**: {importance} (3=最重要)
**状态**: 📝待整理

## 描述
{description}

## 动机
[为什么需要这个想法？解决了什么问题？]

## 相关链接
[相关 issues、文档、讨论等]

## 备注
[任何额外信息]
"""

    # Write idea file
    idea_file.write_text(content, encoding='utf-8')

    if json_mode:
        output = {
            "IDEA_FILE": str(idea_file),
            "TITLE": title,
            "IMPORTANCE": importance
        }
        print(json.dumps(output, ensure_ascii=False))
    else:
        print(f"IDEA_FILE: {idea_file}")
        print(f"TITLE: {title}")
        print(f"IMPORTANCE: {importance} (3=最重要)")

def main():
    parser = argparse.ArgumentParser(description='Create a new idea file')
    parser.add_argument('description', help='Idea description')
    parser.add_argument('-i', '--importance', type=int, default=2, choices=[1, 2, 3],
                        help='Importance level (1-3, 3=highest)')
    parser.add_argument('--json', action='store_true', help='Output in JSON format')

    args = parser.parse_args()
    create_idea(args.description, args.importance, args.json)

if __name__ == '__main__':
    main()
