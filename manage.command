#!/bin/sh
# 数据管理页的窗口:在访达中双击打开(macOS)。等同于在终端中运行 python3 manage.py window。
# 经登录交互 shell 运行,用的是终端里的同一个 python3(conda、pyenv 等常在 ~/.zshrc 中设置,
# /bin/sh 读不到)。
exec "${SHELL:-/bin/zsh}" -lic 'cd "$1" && exec python3 manage.py window' sh "$(cd "$(dirname "$0")" && pwd)"
