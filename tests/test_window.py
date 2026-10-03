"""The macOS window of manage.py (python3 manage.py window), with AppKit and pywebview
stood in for: these only run on a Mac, so the tests check what manage.py asks of them.
What only a Mac shows (the drag itself, the loader in the title bar) is in the release
notes' checklist (docs/releases/v1.0.0.md).
"""
import contextlib
import importlib
import io
import os
import sys
import types
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
importlib.import_module("support")   # the temporary folders, before manage imports lib

import manage  # noqa: E402


class Rect:
    def __init__(self, x, y, w, h):
        self.x, self.y, self.w, self.h = x, y, w, h


def fake_appkit():
    ak = mock.MagicMock()
    ak.NSWindowStyleMaskFullScreen = 1 << 14
    ak.NSWindowStyleMaskFullSizeContentView = 1 << 15
    ak.NSInsetRect = lambda r, dx, dy: Rect(r.x + dx, r.y + dy, r.w - 2 * dx, r.h - 2 * dy)
    ak.NSPointInRect = lambda p, r: r.x <= p.x <= r.x + r.w and r.y <= p.y <= r.y + r.h
    ak.NSUserDefaults.standardUserDefaults.return_value.stringForKey_.return_value = None
    return ak


class Window(unittest.TestCase):
    def setUp(self):
        self.ak = fake_appkit()
        self.cocoa = types.ModuleType("webview.platforms.cocoa")
        self.cocoa.BrowserView = mock.MagicMock()
        self.helper = types.ModuleType("PyObjCTools.AppHelper")
        self.helper.callAfter = lambda f, *a: f(*a)
        tools = types.ModuleType("PyObjCTools")
        tools.AppHelper = self.helper
        mods = {"AppKit": self.ak, "PyObjCTools": tools, "PyObjCTools.AppHelper": self.helper,
                "webview": types.ModuleType("webview"),
                "webview.platforms": types.ModuleType("webview.platforms"), "webview.platforms.cocoa": self.cocoa}
        patcher = mock.patch.dict(sys.modules, mods)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.win = mock.MagicMock(uid="master")
        self.native = self.win.native
        self.native.styleMask.return_value = 0
        self.native.frame.return_value.size.height = 900
        self.view = self.cocoa.BrowserView.instances["master"].webview
        self.view.window.return_value = None
        button = mock.MagicMock()                     # the close button, at the top left
        button.convertRect_toView_.return_value = Rect(7, 878, 14, 14)
        self.native.standardWindowButton_.side_effect = lambda kind: button if kind == self.ak.NSWindowCloseButton else None

    def press(self, y, x=600, clicks=1, window=None):
        handler = self.ak.NSEvent.addLocalMonitorForEventsMatchingMask_handler_.call_args[0][1]
        e = mock.MagicMock()
        e.window.return_value = window or self.native
        e.locationInWindow.return_value = types.SimpleNamespace(x=x, y=y)
        e.clickCount.return_value = clicks
        return e, handler(e)

    def test_full_size_window(self):
        """The page fills the title bar, the web view is in the window before it is shown,
        without a background of its own, and presses are watched."""
        manage._full_size(self.win)
        self.native.setStyleMask_.assert_called_with(1 << 15)
        self.native.setTitlebarAppearsTransparent_.assert_called_with(True)
        self.native.setContentView_.assert_called_with(self.view)
        self.view.setValue_forKey_.assert_called_with(False, "drawsBackground")
        self.ak.NSEvent.addLocalMonitorForEventsMatchingMask_handler_.assert_called_once()

    def test_view_already_in_window(self):
        self.view.window.return_value = self.native
        manage._full_size(self.win)
        self.native.setContentView_.assert_not_called()

    def test_title_bar_drags(self):
        manage._full_size(self.win)
        e, out = self.press(y=890)                      # 10 points below the top edge
        self.assertIsNone(out)
        self.native.performWindowDragWithEvent_.assert_called_with(e)

    def test_presses_that_pass(self):
        """Below the title bar, on a window button, in another window, in full screen: the
        press goes on to the page or the system."""
        manage._full_size(self.win)
        for kw in ({"y": 800}, {"y": 885, "x": 12}, {"y": 890, "window": mock.MagicMock()}):
            e, out = self.press(**kw)
            self.assertIs(out, e, kw)
        self.native.styleMask.return_value = self.ak.NSWindowStyleMaskFullScreen
        e, out = self.press(y=890)
        self.assertIs(out, e)
        self.native.performWindowDragWithEvent_.assert_not_called()

    def test_press_activates_an_inactive_app(self):
        """Started from Finder the app may not be active: a press makes it active, its
        window key, and still reaches the page."""
        manage._full_size(self.win)
        app = self.ak.NSApplication.sharedApplication.return_value
        app.isActive.return_value = True
        self.press(y=500)
        self.native.makeKeyAndOrderFront_.assert_not_called()
        app.isActive.return_value = False
        e, out = self.press(y=500)
        self.assertIs(out, e)
        app.setActivationPolicy_.assert_called_with(self.ak.NSApplicationActivationPolicyRegular)
        self.native.makeKeyAndOrderFront_.assert_called_once()

    def test_double_click_follows_system_setting(self):
        manage._full_size(self.win)
        prefs = self.ak.NSUserDefaults.standardUserDefaults.return_value.stringForKey_
        self.press(y=890, clicks=2)
        self.native.performZoom_.assert_called_once()
        prefs.return_value = "Minimize"
        self.press(y=890, clicks=2)
        self.native.performMiniaturize_.assert_called_once()
        prefs.return_value = "None"
        self.press(y=890, clicks=2)
        self.assertEqual((self.native.performZoom_.call_count, self.native.performMiniaturize_.call_count), (1, 1))

    def test_window_command(self):
        """manage.py window: starts the server when none is running, opens the page with
        the title bar's height on macOS, and stops the server when the window closes."""
        webview = sys.modules["webview"]
        webview.settings = {}
        class Hook(list):
            def __iadd__(self, f):
                self.append(f)
                return self
        made = mock.MagicMock()
        made.events = types.SimpleNamespace(before_show=Hook(), shown=Hook())
        webview.create_window = mock.MagicMock(return_value=made)
        webview.start = mock.MagicMock()
        stop = mock.MagicMock()
        with mock.patch.object(manage, "_serving", return_value=False), \
                mock.patch("manager.server.start", return_value=stop) as start, \
                mock.patch.object(manage.sys, "platform", "darwin"), \
                contextlib.redirect_stdout(io.StringIO()):
            manage.window(8999)
        start.assert_called_once_with(8999)
        url = webview.create_window.call_args[0][1]
        self.assertEqual(url, f"http://localhost:8999/?titlebar={manage.TITLEBAR}")
        self.assertTrue(webview.settings["ALLOW_DOWNLOADS"])
        stop.assert_called_once()
        self.assertEqual((len(made.events.before_show), len(made.events.shown)), (1, 1))
        made.events.shown[0]()                       # shown: the app is made active, its window key
        made.native.makeKeyAndOrderFront_.assert_called_once()


if __name__ == "__main__":
    unittest.main()
