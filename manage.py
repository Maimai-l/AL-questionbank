#!/usr/bin/env python3
"""数据管理页(manager/,docs/data-manager.md)。

    python3 manage.py                 起数据管理页并打开浏览器,局域网可访问
    python3 manage.py --port 8910 --no-open
    python3 manage.py auto            题库更新后运行自动流程(按教材章节分组);题库没变时不运行
    python3 manage.py auto --force    不论题库是否更新都运行

sync.py pull 取回新数据后会运行 auto;数据管理页运行期间每分钟检查一次题库是否更新。
"""
import argparse, sys


def serve(port, open_browser):
    try:
        from manager.server import run
    except ImportError as e:
        sys.exit(f"缺少依赖:{e.name}。运行 pip install aiohttp")
    if open_browser:
        import threading, webbrowser
        threading.Timer(1.0, lambda: webbrowser.open(f"http://localhost:{port}/")).start()
    run(port)


def auto(force):
    from manager import flow
    r = flow.auto_run(force=force, log=print)
    if r is None:
        print("题库没有更新,自动流程不需要运行")
    elif any(x["errors"] for x in r.values()):
        sys.exit(1)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--port", type=int, default=8910)
    p.add_argument("--no-open", action="store_true")
    sub = p.add_subparsers(dest="cmd")
    sub.add_parser("auto").add_argument("--force", action="store_true")
    a = p.parse_args()
    if a.cmd == "auto":
        auto(a.force)
    else:
        serve(a.port, not a.no_open)


if __name__ == "__main__":
    main()
