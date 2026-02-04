"""
Singularity Front - 文明前沿雷达系统

一个实时追踪奇点人物及其生态系统的信息抓取与分析系统。
"""

__version__ = "0.1.0"

# 解决 Windows 控制台中文编码问题
import sys
import io

# 设置标准输出编码为 UTF-8
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
