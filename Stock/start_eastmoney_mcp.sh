#!/bin/bash
# 启动东方财富MCP服务器

cd "$(dirname "$0")"

# 检查Python版本
python3 --version || { echo "需要 Python 3.8+"; exit 1; }

# 检查依赖
pip install mcp requests --quiet 2>/dev/null || pip3 install mcp requests --quiet

# 启动服务器
python3 eastmoney_mcp_server.py