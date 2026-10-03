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
    sys.exit(f"缺少依赖:{e.name}。运行 pip install {PIP.get(e.name, e.name)}"
             "(全部依赖:pip install -r manager/requirements.txt)")


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

    def open(self, path):
        """A page the browser opens in a new tab (the question paper, a reading document)."""
        import webbrowser
        webbrowser.open(self.base + path)

    def copy(self, text):
        cmd = (["pbcopy"] if sys.platform == "darwin" else ["clip"] if os.name == "nt"
               else ["xclip", "-selection", "clipboard"])
        subprocess.run(cmd, input=text.encode("utf-16" if os.name == "nt" else "utf-8"), check=True)
        return True


TITLEBAR = 28                            # macOS title bar height in points: the page leaves it free for the window buttons


_monitor = None


def _title_bar_drag(w):
    """Presses in the title bar's height move the window. With the page under the title
    bar, the view under the pointer there is the web view, which does not let a press move
    the window; and a view laid over it does not hold: pywebview makes the web view the
    window's content view when the page first loads, which can put it above such a view.
    So the window's own presses are looked at before any view gets them: one within the
    title bar's height, outside the window buttons, starts a window drag; a double click
    does what the system setting for title bars says (zoom by default). The first press on
    an inactive window moves it too."""
    global _monitor
    import AppKit

    buttons = [w.standardWindowButton_(b) for b in
               (AppKit.NSWindowCloseButton, AppKit.NSWindowMiniaturizeButton, AppKit.NSWindowZoomButton)]

    def on_button(point):
        for b in buttons:
            if b is not None:
                r = b.convertRect_toView_(b.bounds(), None)
                if AppKit.NSPointInRect(point, AppKit.NSInsetRect(r, -4, -4)):
                    return True
        return False

    def press(event):
        if event.window() != w or w.styleMask() & AppKit.NSWindowStyleMaskFullScreen:
            return event
        point = event.locationInWindow()
        if w.frame().size.height - point.y > TITLEBAR or on_button(point):
            return event
        if event.clickCount() == 2:
            act = AppKit.NSUserDefaults.standardUserDefaults().stringForKey_("AppleActionOnDoubleClick")
            if act == "Minimize":
                w.performMiniaturize_(None)
            elif act != "None":
                w.performZoom_(None)
        else:
            w.performWindowDragWithEvent_(event)
        return None

    _monitor = AppKit.NSEvent.addLocalMonitorForEventsMatchingMask_handler_(AppKit.NSEventMaskLeftMouseDown, press)


def _full_size(window):
    """macOS, before the window is first shown (events.before_show runs on the main
    thread): the page also fills the title bar, which keeps only the window buttons, so the
    top bar and the opening loader reach the top edge of the window; presses in that height
    still move the window (_title_bar_drag).

    pywebview puts the web view into the window only when the page has loaded (all its
    scripts and fonts), and until then the window shows its bare background. The web view
    goes in here instead, without a background of its own, so the page's loader is seen
    from its first paint."""
    import AppKit
    from webview.platforms.cocoa import BrowserView

    w = window.native
    w.setStyleMask_(w.styleMask() | getattr(AppKit, "NSWindowStyleMaskFullSizeContentView", 1 << 15))
    w.setTitlebarAppearsTransparent_(True)
    w.setTitleVisibility_(AppKit.NSWindowTitleHidden)
    bar = w.contentView().superview().subviews().lastObject()   # the title bar, over the content
    # pywebview paints the title bar with the system colour; it is left clear
    if bar is not None and bar.respondsToSelector_("setBackgroundColor:"):
        bar.setBackgroundColor_(AppKit.NSColor.clearColor())
    view = BrowserView.instances[window.uid].webview
    if not view.window():
        try:
            view.setValue_forKey_(False, "drawsBackground")   # the window's colour until the page paints
        except Exception:
            pass
        w.setContentView_(view)
        w.makeFirstResponder_(view)
    _title_bar_drag(w)


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
    mac = sys.platform == "darwin"
    # the page leaves the title bar's height free (index.html, ?titlebar=); #141414 is the
    # opening loader's colour, shown until the page draws
    w = webview.create_window("AL 题库", base + (f"/?titlebar={TITLEBAR}" if mac else "/"), width=1440, height=900,
                              min_size=(1280, 800), background_color="#141414", js_api=Bridge(base))
    if mac:
        w.events.before_show += lambda: _full_size(w)
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
