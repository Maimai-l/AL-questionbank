#!/usr/bin/env python3
"""数据管理页(manager/,docs/data-manager.md)。

    python3 manage.py                 起数据管理页并打开浏览器,局域网可访问
    python3 manage.py --port 8910 --no-open
    python3 manage.py window          在独立窗口中打开(pywebview);manage.command 可在访达中双击
    python3 manage.py auto            题库更新后运行自动流程(按教材章节分组);题库没变时不运行
    python3 manage.py auto --force    不论题库是否更新都运行

sync.py pull 取回新数据后会运行 auto;数据管理页运行期间每分钟检查一次题库是否更新。
"""
import argparse, os, socket, subprocess, sys, urllib.request

from lib import paths

PIP = {"yaml": "pyyaml", "PIL": "pillow", "webview": "pywebview"}   # module name -> pip package


def need(e):
    sys.exit(f"缺少依赖:{e.name}。运行 pip install {PIP.get(e.name, e.name)}")


def serve(port, open_browser):
    try:
        from manager.server import run
    except ImportError as e:
        need(e)
    if open_browser:
        import threading, webbrowser
        threading.Timer(1.0, lambda: webbrowser.open(f"http://localhost:{port}/")).start()
    run(port)


def _serving(port):
    """True when the data manager already answers on the port, False when the port is free."""
    try:
        with urllib.request.urlopen(f"http://localhost:{port}/api/flows/catalog", timeout=2) as r:
            return r.status == 200
    except OSError:
        pass
    with socket.socket() as s:
        if s.connect_ex(("127.0.0.1", port)) == 0:
            sys.exit(f"端口 {port} 已被其他程序占用。换一个端口:python3 manage.py window --port 8911")
    return False


class Bridge:
    """What the page asks of the window (window.pywebview.api): what a browser does itself."""

    def __init__(self, base):
        self.base = base
        self._window = None                  # set once the window exists (an underscore: not offered to the page)

    def open(self, path):
        """A page the browser opens in a new tab (the question paper, a reading document)."""
        import webbrowser
        webbrowser.open(self.base + path)

    def copy(self, text):
        cmd = (["pbcopy"] if sys.platform == "darwin" else ["clip"] if os.name == "nt"
               else ["xclip", "-selection", "clipboard"])
        subprocess.run(cmd, input=text.encode("utf-16" if os.name == "nt" else "utf-8"), check=True)
        return True

    def theme(self, rgb, dark, system=False):
        """The page's top bar colour and light or dark: the title bar takes them, so it reads as
        part of the top bar (macOS; elsewhere the system title bar stays). With the theme 自动
        (system) the window keeps following the system's appearance."""
        if sys.platform != "darwin" or not self._window or not self._window.native:
            return
        import AppKit
        from PyObjCTools import AppHelper

        def apply():
            w = self._window.native
            color = AppKit.NSColor.colorWithSRGBRed_green_blue_alpha_(*(c / 255 for c in rgb[:3]), 1.0)
            w.setTitlebarAppearsTransparent_(True)
            w.setTitleVisibility_(AppKit.NSWindowTitleHidden)
            w.setBackgroundColor_(color)
            # pywebview paints the title bar view with the system colour; it takes the page's
            bar = w.contentView().superview().subviews().lastObject()
            if bar is not None and bar.respondsToSelector_("setBackgroundColor:"):
                bar.setBackgroundColor_(color)
            w.setAppearance_(None if system else AppKit.NSAppearance.appearanceNamed_(
                AppKit.NSAppearanceNameDarkAqua if dark else AppKit.NSAppearanceNameAqua))
        AppHelper.callAfter(apply)


def window(port):
    try:
        import webview
    except ImportError as e:
        need(e)
    from manager import __version__
    stop = None
    if not _serving(port):
        try:
            from manager.server import start
        except ImportError as e:
            need(e)
        stop = start(port)
    base = f"http://localhost:{port}"
    print(f"数据管理页 {__version__}: {base}/(窗口关闭后停止;iPad 白板外壳的来源填 @qb-manage)")
    webview.settings["ALLOW_DOWNLOADS"] = True
    bridge = Bridge(base)
    bridge._window = webview.create_window("AL 题库", base + "/", width=1440, height=900, min_size=(1280, 800),
                                           js_api=bridge)
    # private_mode=False keeps the page's own settings (the theme) between launches
    webview.start(private_mode=False, storage_path=os.path.join(paths.WORK, "webview"))
    if stop:
        stop()


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
    sub.add_parser("window").add_argument("--port", type=int, default=argparse.SUPPRESS)
    sub.add_parser("auto").add_argument("--force", action="store_true")
    a = p.parse_args()
    if a.cmd == "window":
        window(a.port)
    elif a.cmd == "auto":
        auto(a.force)
    else:
        serve(a.port, not a.no_open)


if __name__ == "__main__":
    main()
