"""The data manager's pages in a browser (Playwright, Chromium): each page's main path,
clicked through as a person would, with no script error, no failed request and no error
message on the way.

    pip install playwright && playwright install chromium     (once)
    python3 -m unittest tests.test_pages

Skipped when Playwright or data/ is missing. QB_CHROMIUM names a Chromium to use in
place of Playwright's own. Like test_manager.py, it writes only to temporary folders
(support.py).
"""
import asyncio
import os
import sys
import re
import socket
import threading
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from support import HAVE_DATA, questions  # noqa: E402

try:
    from playwright.sync_api import expect, sync_playwright
except ImportError:
    sync_playwright = None

READY = sync_playwright is not None and HAVE_DATA
SERVER = BROWSER = PW = None


def _serve():
    """The server on a thread of its own, on a free port, without the automatic flows."""
    from aiohttp import web
    from manager import server
    app = server.make_app()
    del app.cleanup_ctx[app.cleanup_ctx.index(server.watch_bank)]
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    loop = asyncio.new_event_loop()
    runner = web.AppRunner(app)
    loop.run_until_complete(runner.setup())
    loop.run_until_complete(web.TCPSite(runner, "127.0.0.1", port).start())
    threading.Thread(target=loop.run_forever, daemon=True).start()

    def stop():
        asyncio.run_coroutine_threadsafe(runner.cleanup(), loop).result(30)
        loop.call_soon_threadsafe(loop.stop)
    return f"http://127.0.0.1:{port}", stop


def setUpModule():
    global SERVER, BROWSER, PW
    if not READY:
        return
    SERVER = _serve()
    PW = sync_playwright().start()
    exe = os.environ.get("QB_CHROMIUM")
    try:
        BROWSER = PW.chromium.launch(executable_path=exe) if exe else PW.chromium.launch()
    except Exception:
        if not os.path.exists("/opt/pw-browsers/chromium"):
            raise
        BROWSER = PW.chromium.launch(executable_path="/opt/pw-browsers/chromium")


def tearDownModule():
    if BROWSER:
        BROWSER.close()
    if PW:
        PW.stop()
    if SERVER:
        SERVER[1]()


def make_set(name, items):
    from manager import sets
    return sets.create(name, items)["id"]


@unittest.skipUnless(READY, "needs Playwright and data/")
class Page(unittest.TestCase):
    """A fresh page per test; every script error, failed request and error toast is kept
    and the test fails on any of them."""
    def setUp(self):
        self.base = SERVER[0]
        self.ctx = BROWSER.new_context(viewport={"width": 1440, "height": 900}, accept_downloads=True)
        self.page = self.ctx.new_page()
        self.problems = []
        p = self.page
        p.on("pageerror", lambda e: self.problems.append(f"script: {e}"))
        p.on("console", lambda m: m.type == "error" and not m.text.startswith("Failed to load resource")
             and self.problems.append(f"console: {m.text}"))
        p.on("response", lambda r: r.status >= 400 and r.url not in self.allowed
             and self.problems.append(f"{r.status} {r.request.method} {r.url[len(self.base):]}"))
        self.allowed = set()
        p.set_default_timeout(30000)
        expect.set_options(timeout=30000)

    def tearDown(self):
        try:
            errors = self.page.locator(".toast--error").all_inner_texts()
        except Exception:
            errors = []
        self.ctx.close()
        problems = self.problems + [f"toast: {t}" for t in errors]
        self.assertEqual(problems, [])

    def go(self, hash_):
        self.page.goto(f"{self.base}/#/{hash_}")
        expect(self.page.locator("#boot")).to_have_count(0)      # the loader has finished
        self.page.mouse.move(1430, 890)                          # off the sidebar

    def button(self, name, **kw):
        return self.page.get_by_role("button", name=name, exact=True, **kw)

    def toast_ok(self):
        expect(self.page.locator(".toast--success").last).to_be_visible()


class QueryPage(Page):
    def test_pick_and_add(self):
        """Narrow the table, open a question, pick two, add them to a new set, then search."""
        p = self.page
        self.go("query")
        rows = p.locator("table tbody tr[data-k]")
        expect(rows.first).to_be_visible()
        head = p.locator(".headline")
        one = head.inner_text()
        p.locator(".dm-cond label.check", has_text="Paper 3").click()   # Paper 1 and 3
        expect(head).not_to_have_text(one)
        total = head.inner_text()
        rows.nth(0).click()
        expect(p.locator(".detail .qimg").first).to_be_visible()
        rows.nth(1).click(modifiers=["Shift"])
        expect(p.locator(".selbar b")).to_have_text("2")
        self.button("加入题组").click()
        dlg = p.get_by_role("dialog")
        dlg.get_by_label("名称").fill("测试 查询页")
        dlg.get_by_role("button", name="加入题组").click()
        self.toast_ok()
        from manager import sets
        self.assertEqual([len(s["items"]) for s in sets.all_sets() if s["name"] == "测试 查询页"], [2])
        p.get_by_label("搜索题目").fill("integration")
        expect(head).not_to_have_text(total)
        p.locator(".dm-cond .select").first.click()
        p.get_by_role("option", name="9618 Computer Science").click()
        expect(head).not_to_have_text(total)
        expect(rows.first).to_be_visible()



class SearchPage(Page):
    def test_search_narrow_and_add(self):
        """Keywords, then the advanced conditions on the left, a result opened with its
        words marked, picked and added to a set; the search is kept among the recent ones."""
        p = self.page
        self.go("search")
        p.locator(".sp-box input").fill("integration")
        p.locator(".sp-box input").press("Enter")
        hits, head = p.locator(".hit"), p.locator(".sp-main .headline")
        expect(hits.first).to_be_visible()
        n = head.inner_text()
        p.locator(".sp-left label.check", has_text="9231").click()
        expect(head).not_to_have_text(n)
        p.locator(".sp-left .mpick .select").click()
        p.locator(".sp-left .mpick .menu-item").first.click()
        p.mouse.click(1000, 40)
        expect(p.locator(".sp-left .mpick .tag").first).to_be_visible()
        p.get_by_label("不包含词语").fill("parts")
        p.locator(".sp-left label.check", has_text="评分细则").click()
        p.locator(".sp-left .more-h").click()
        p.locator(".sp-left .select", has_text="不限").click()
        p.get_by_role("option", name="有详解").click()
        p.locator(".sp-main .selbar").get_by_text("年份", exact=True).click()
        hits.first.click()
        expect(p.locator(".detail .qimg").first).to_be_visible()
        hits.first.locator("label.check").click()
        self.button("加入题组").click()
        dlg = p.get_by_role("dialog")
        dlg.get_by_label("名称").fill("测试 搜索页")
        dlg.get_by_role("button", name="加入题组").click()
        self.toast_ok()
        p.locator(".sp-box input").fill("")
        expect(p.locator(".sp-recent .rec").first).to_be_visible()

    def test_paper_code(self):
        p = self.page
        self.go("search")
        p.locator(".sp-box input").fill("9709/32/O/N/24")
        expect(p.locator(".hit").first).to_be_visible()



class SetsPage(Page):
    def open_set(self, name):
        self.page.locator(".setlist").get_by_text(name, exact=True).click()
        expect(self.page.locator(".sd-head h1")).to_have_text(name)

    def test_make_edit_output_delete(self):
        """New set named in place; an existing set: its paper, reordering, 输出, export and
        import of its JSON, then deleting it."""
        from manager import sets
        p = self.page
        items = questions(n=4)
        sid = make_set("测试 题组页", items)
        self.go("sets")
        self.button("新建题组").click()
        p.locator("input.title-edit").fill("测试 新建")
        p.locator("input.title-edit").press("Enter")
        expect(p.locator(".setlist")).to_contain_text("测试 新建")

        self.open_set("测试 题组页")
        expect(p.locator("img.sheet").first).to_have_js_property("complete", True)
        self.assertGreater(p.locator("img.sheet").first.evaluate("i => i.naturalWidth"), 0)
        self.button("编辑").click()
        p.locator(".sd-paper tbody tr[data-k], .dm-tablebox tbody tr[data-k]").first.click()
        self.button("下移题目").click()
        self.button("完成编辑").click()
        self.assertEqual(sets.get(sid)["items"][:2], [items[1], items[0]])

        self.button("输出").click()
        dlg = p.get_by_role("dialog")
        expect(dlg.locator(".op-file").first).to_be_visible()
        dlg.get_by_role("button", name="调整格式与内容").click()
        with p.expect_download() as d:
            dlg.get_by_role("button", name=re.compile("下载")).click()
        self.assertGreater(os.path.getsize(d.value.path()), 0)
        expect(dlg).to_have_count(0)

        p.locator(".sd-acts").get_by_role("button", name="更多操作").click()
        with p.expect_download() as d:
            p.get_by_role("menuitem", name="导出 JSON").click()
        exported = d.value.path()
        p.locator("input[type=file]").set_input_files(exported)
        self.toast_ok()
        self.assertEqual(sum(s["items"] == [items[1], items[0]] + items[2:] for s in sets.all_sets()), 2)

        row = p.locator(".setlist [role=option], .setlist li").filter(has_text="测试 题组页").first
        row.get_by_role("button", name="更多操作").click()
        p.get_by_role("menuitem", name="删除题组").click()
        p.get_by_role("dialog").get_by_role("button", name="删除题组").click()
        expect(p.locator(".setlist").get_by_text("测试 题组页", exact=True)).to_have_count(0)
        self.assertNotIn(sid, [s["id"] for s in sets.all_sets()])

    def test_board(self):
        """打开白板 shows the paper in the board; 完成 goes back to the set."""
        p = self.page
        sid = make_set("测试 白板", questions(n=3))
        self.go(f"sets/{sid}")
        self.button("打开白板").click()
        expect(p).to_have_url(re.compile(f"#/sets/{sid}/board/"))
        frame = p.frame_locator(".board-frame iframe")
        expect(frame.locator("canvas").first).to_be_visible()
        expect(p.locator(".board-at")).to_contain_text("第")
        self.button("完成").click()
        expect(p).to_have_url(re.compile(f"#/sets/{sid}$"))



def eventually(test, timeout=10):
    """Wait for a change the page saves on its own (after a short pause)."""
    import time
    end = time.time() + timeout
    while not test():
        if time.time() > end:
            raise AssertionError("not saved")
        time.sleep(0.2)


class TemplatesPage(Page):
    def test_make_change_delete(self):
        """A built-in template is read-only; a new one is named, changed (saved as it is
        changed), previewed with a set, then deleted."""
        from manager import templates
        p = self.page
        make_set("测试 模板预览", questions(n=2))
        self.go("templates")
        expect(p.locator(".lock-note")).to_be_visible()
        self.button("新建模板").click()
        self.button("重命名模板").click()
        p.locator("input.title-edit").fill("测试 模板")
        p.locator("input.title-edit").press("Enter")
        p.locator(".tpl-opts").get_by_text("ZIP", exact=True).click()
        p.locator(".tpl-opts label.check", has_text="题干文字").click()
        p.locator("textarea.tpl-src").fill("测试说明")
        eventually(lambda: any(t["name"] == "测试 模板" and "text" in t["settings"]["per_question"]
                               and t["body"].startswith("测试说明") for t in templates.all_templates()))
        p.get_by_role("tab", name="预览").click()
        expect(p.locator(".ex-docbody")).to_contain_text("测试说明")
        row = p.locator(".tpl-list [role=option], .tpl-list li").filter(has_text="测试 模板").first
        row.get_by_role("button", name="更多操作").click()
        p.get_by_role("menuitem", name="删除模板").click()
        p.get_by_role("dialog").get_by_role("button", name="删除模板").click()
        expect(p.locator(".tpl-list").get_by_text("测试 模板", exact=True)).to_have_count(0)
        self.assertFalse([t for t in templates.all_templates() if t["name"] == "测试 模板"])


class SettingsPage(Page):
    def test_options(self):
        """Footer options and 版面 change the preview and are saved; 配色 changes the page."""
        from manager import settings
        p = self.page
        make_set("测试 设置", questions())
        self.go("settings")
        sheet = p.locator(".sd-sheets img.sheet").first
        expect(sheet).to_be_visible()
        src = sheet.get_attribute("src")
        p.locator("label.check", has_text="页码").click()
        expect(sheet).not_to_have_attribute("src", src)
        p.locator(".space-cell").nth(0).click()
        p.locator("[role=slider]").press("ArrowRight")
        eventually(lambda: settings.load()["space"] == 1 and not settings.load()["footer_page"])
        p.locator(".dm-col, main").get_by_text("深色", exact=True).click()
        expect(p.locator("html")).to_have_attribute("data-theme", "dark")
        eventually(lambda: settings.load()["theme"] == "dark")



class FlowsPage(Page):
    def drag(self, src, dst_x, dst_y):
        box = src.bounding_box()
        self.page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
        self.page.mouse.down()
        self.page.mouse.move(dst_x, dst_y, steps=8)
        self.page.mouse.up()

    def wire(self, a, b):
        """From node a's first output to node b's first input."""
        nodes = self.page.locator(".fl-in .nd")
        self.drag(nodes.nth(a).locator(".pt.r").first, *self.centre(nodes.nth(b).locator(".pt.l").first))

    def centre(self, el):
        box = el.bounding_box()
        return box["x"] + box["width"] / 2, box["y"] + box["height"] / 2

    def test_build_run_rename_delete(self):
        """A new flow built in the editor (题库 → 限制数量 → 新建题组), run there, renamed,
        run again from its overview, then deleted."""
        from manager import flow, sets
        p = self.page
        self.go("templates/flows")
        self.button("新建流程").click()
        expect(p).to_have_url(re.compile("#/flows/"))
        fid = p.url.rsplit("/", 1)[1]
        canvas = p.locator(".fl").bounding_box()
        for i, label in enumerate(("题库", "限制数量", "新建题组")):
            p.locator(".fl-pal").get_by_role("button", name=label, exact=True).click()
            node = p.locator(".fl-in .nd").nth(i)
            expect(node).to_be_visible()
            self.drag(node.locator(".nd-h"), canvas["x"] + 120 + 230 * i, canvas["y"] + 200)
        self.wire(0, 1)
        self.wire(1, 2)
        p.locator(".fl-in .nd").nth(1).locator(".nd-h").click()
        p.locator(".fl-insp").get_by_label("条数").fill("3")
        self.button("运行流程").click()
        expect(p.locator(".outs .fo-row").first).to_contain_text("3 题")
        p.locator(".fl-bar").get_by_role("button", name="更多操作").click()
        p.get_by_role("menuitem", name="重命名").click()
        dlg = p.get_by_role("dialog")
        dlg.get_by_label("名称").fill("测试 流程")
        dlg.get_by_role("button", name="重命名").click()
        self.button("完成").click()
        expect(p).to_have_url(re.compile(f"#/templates/flows/{fid}$"))
        expect(p.locator(".fo-head h1")).to_have_text("测试 流程")
        self.assertEqual(flow.get(fid)["name"], "测试 流程")
        self.button("运行流程").click()
        expect(p.locator(".fo-sec .fo-row").first).to_contain_text("3 题")
        self.assertEqual([len(x["items"]) for x in sets.all_sets() if x.get("flow") == fid], [3])
        row = p.locator(".tpl-list [role=option], .tpl-list li").filter(has_text="测试 流程").first
        row.get_by_role("button", name="更多操作").click()
        p.get_by_role("menuitem", name="删除流程").click()
        p.get_by_role("dialog").get_by_role("button", name="删除流程").click()
        expect(p.locator(".tpl-list").get_by_text("测试 流程", exact=True)).to_have_count(0)

    def test_builtin_runs_and_is_locked(self):
        """A built-in flow runs from its overview; its editor cannot change it."""
        p = self.page
        self.go("templates/flows/example-shuffle")
        self.button("运行流程").click()
        expect(p.locator(".fo-sec .fo-row").first).to_be_visible(timeout=120000)
        self.button("编辑流程").click()
        expect(p.locator(".fl-pal button").first).to_be_disabled()
        p.locator(".fl-in .nd").first.locator(".nd-h").click()
        expect(p.locator(".fl-insp .lock-note")).to_be_visible()


if __name__ == "__main__":
    unittest.main()
