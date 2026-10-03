#!/bin/sh
# 数据管理页的窗口:在访达中双击打开(macOS)。等同于 python3 manage.py window
cd "$(dirname "$0")" && exec python3 manage.py window
