#!/usr/bin/env bash

set -e

JSON_MODE=false
IMPORTANCE=""
IDEA_DESCRIPTION=""

# Parse arguments
while [ $# -gt 0 ]; do
    case "$1" in
        --json)
            JSON_MODE=true
            shift
            ;;
        --importance|-i)
            IMPORTANCE="$2"
            shift 2
            ;;
        重要度[123])
            IMPORTANCE="${1#重要度}"
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [--json] [--importance <1-3>] <idea_description>"
            echo ""
            echo "Options:"
            echo "  --json              Output in JSON format"
            echo "  --importance, -i    Set importance (1-3, 3=highest)"
            echo "  --help, -h          Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0 '添加用户登录功能'"
            echo "  $0 --importance 3 '实现实时通知'"
            echo "  $0 重要度3 '紧急修复登录bug'"
            exit 0
            ;;
        *)
            IDEA_DESCRIPTION="$*"
            break
            ;;
    esac
done

if [ -z "$IDEA_DESCRIPTION" ]; then
    echo "Error: Idea description is required" >&2
    exit 1
fi

# Function to find repository root
find_repo_root() {
    local dir="$1"
    while [ "$dir" != "/" ]; do
        if [ -d "$dir/.git" ] || [ -d "$dir/.specify" ]; then
            echo "$dir"
            return 0
        fi
        dir="$(dirname "$dir")"
    done
    return 1
}

# Find repository root
SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if git rev-parse --show-toplevel >/dev/null 2>&1; then
    REPO_ROOT=$(git rev-parse --show-toplevel)
else
    REPO_ROOT="$(find_repo_root "$SCRIPT_DIR")"
    if [ -z "$REPO_ROOT" ]; then
        echo "Error: Could not determine repository root" >&2
        exit 1
    fi
fi

cd "$REPO_ROOT"

IDEAS_DIR="$REPO_ROOT/.specify/ideas"
mkdir -p "$IDEAS_DIR"

# Use description as title (first ~50 chars for display)
TITLE=$(echo "$IDEA_DESCRIPTION" | head -c 50)

# Create safe filename from description - preserve Chinese characters
# Simply replace spaces and special chars with dash, keep Chinese
SAFE_TITLE=$(echo "$IDEA_DESCRIPTION" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//' | tr ' ' '-' | sed -E 's/[^-a-zA-Z0-9[:space:]]//g' | sed 's/--\+/-/g' | sed 's/^-//;s/-$//')
# If empty after filtering, use timestamp
if [ -z "$SAFE_TITLE" ]; then
    SAFE_TITLE="idea-$(date +%Y%m%d%H%M%S)"
fi
IDEA_FILE="$IDEAS_DIR/${SAFE_TITLE}.md"

# Handle duplicate filenames
if [ -f "$IDEA_FILE" ]; then
    TIMESTAMP=$(date +%Y%m%d%H%M%S)
    IDEA_FILE="$IDEAS_DIR/${SAFE_TITLE}-${TIMESTAMP}.md"
fi

# Get current date
DATE=$(date +%Y-%m-%d)

# Default importance if not set
if [ -z "$IMPORTANCE" ]; then
    IMPORTANCE=2
fi

# Create idea file from template
TEMPLATE="$IDEAS_DIR/idea-template.md"
if [ -f "$TEMPLATE" ]; then
    sed -e "s/\[TITLE\]/$TITLE/g" \
        -e "s/\[DATE\]/$DATE/g" \
        -e "s/\[3 | 2 | 1\] (3=最重要)/$IMPORTANCE (3=最重要)/g" \
        -e "s/\[📝待整理 | 💡已确认 | ✅已完成\]/📝待整理/g" \
        -e "s/\[简要描述这个想法是什么\]/$IDEA_DESCRIPTION/g" \
        "$TEMPLATE" > "$IDEA_FILE"
else
    # Fallback if template doesn't exist
    cat > "$IDEA_FILE" << EOF
# 想法: $TITLE

**创建日期**: $DATE
**重要度**: $IMPORTANCE (3=最重要)
**状态**: 📝待整理

## 描述
$IDEA_DESCRIPTION

## 动机
[为什么需要这个想法？解决了什么问题？]

## 相关链接
[相关 issues、文档、讨论等]

## 备注
[任何额外信息]
EOF
fi

if $JSON_MODE; then
    printf '{"IDEA_FILE":"%s","TITLE":"%s","IMPORTANCE":%d}\n' "$IDEA_FILE" "$TITLE" "$IMPORTANCE"
else
    echo "IDEA_FILE: $IDEA_FILE"
    echo "TITLE: $TITLE"
    echo "IMPORTANCE: $IMPORTANCE (3=最重要)"
fi
