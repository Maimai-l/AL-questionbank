"""Tests for the data manager (manager/): what each page asks of the server along the
paths a person takes through it, the practice paper's 版面 steps and the writing board.

    python3 -m unittest discover tests

They read the bank in data/ (python3 sync.py pull) and write only to temporary folders
(support.py). The pages themselves, in a browser, are in test_pages.py.
"""
import io
import json
import os
import sys
import unittest
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from support import HAVE_DATA, paths, questions  # noqa: E402

NEED = unittest.skipUnless(HAVE_DATA, "needs data/ (python3 sync.py pull)")


@NEED
class Paper(unittest.TestCase):
    def test_steps_grow(self):
        """Each 版面 step has at least as many pages as the one before it."""
        from manager import paper, sets
        s = sets.create("测试 版面", questions())
        counts = []
        for space in range(len(paper.SPACE)):
            with paper.pymupdf.open(paper.build(s, space=space)) as d:
                counts.append(d.page_count)
        self.assertEqual(counts, sorted(counts))
        self.assertLess(counts[0], counts[-1])

    def test_compact_has_no_answer_lines(self):
        """紧凑 leaves out the lines between parts as well as those after the last part."""
        from manager import paper
        checked = 0
        for r in paper._rows(questions(n=40)):
            b = paper._block(r, 0)
            if b and paper._ruled_rows(paper._grey(paths.resolve(r["image"]))).any():
                self.assertFalse(paper._ruled_rows(b[0]).any(), r["id"])
                checked += 1
        self.assertGreater(checked, 0)

    def test_every_exam_lays_out(self):
        """A set mixing every exam (CIE with answer space, admissions with blank space)
        builds at every step."""
        from manager import bank, paper, sets
        items = [r["id"] for e in bank.meta() for r in bank.rows(e["exam"])[:2]]
        s = sets.create("测试 各考试", items)
        for space in range(len(paper.SPACE)):
            self.assertGreater(paper.page_count(paper.build(s, space=space)), 0)

    def test_no_step_past_original(self):
        from manager import paper, settings
        self.assertEqual(paper.SPACE[-1], 1)
        os.makedirs(paths.WORK, exist_ok=True)
        with open(settings.PATH, "w", encoding="utf-8") as f:
            json.dump({"space": 4}, f)              # a fifth step was saved once
        self.assertEqual(settings.load()["space"], 3)
        os.remove(settings.PATH)


class Api(unittest.IsolatedAsyncioTestCase):
    """The server in this process, without the minute-by-minute automatic flows."""

    def _setupAsyncioRunner(self):
        super()._setupAsyncioRunner()
        self._asyncioRunner.get_loop().set_debug(False)   # the test case turns it on: slow-task notices

    async def asyncSetUp(self):
        from aiohttp.test_utils import TestClient, TestServer
        from manager import server
        app = server.make_app()
        del app.cleanup_ctx[app.cleanup_ctx.index(server.watch_bank)]
        self.client = TestClient(TestServer(app))
        await self.client.start_server()

    async def asyncTearDown(self):
        await self.client.close()

    async def call(self, method, url, body=None, status=200):
        r = await self.client.request(method, url, json=body)
        if r.status != status:
            self.fail(f"{method} {url}: {r.status} {(await r.read())[:300]!r}")
        return r

    async def json(self, method, url, body=None, status=200):
        return await (await self.call(method, url, body, status)).json()

    async def make_set(self, items, name="测试"):
        return (await self.json("POST", "/api/sets", {"name": name, "items": items}))["id"]


@NEED
class QueryPage(Api):
    async def test_every_exam(self):
        """The page's first load, then each exam's table and its search box."""
        for url in ("/", "/api/meta", "/api/sets", "/api/templates", "/api/settings"):
            await self.call("GET", url)
        exams = [m["exam"] for m in await self.json("GET", "/api/meta")]
        self.assertIn("9709", exams)
        for exam in exams:
            rows = await self.json("GET", f"/api/questions?exam={exam}")
            self.assertTrue(rows, exam)
            await self.json("GET", f"/api/search?exam={exam}&q=the")

    async def test_question_detail(self):
        """A question's panel: its text, images, mark scheme and original paper."""
        for exam, component in (("9709", "3"), ("9618", "1"), ("TMUA", "1")):
            qid = questions(exam, component, 1)[0]
            d = await self.json("GET", f"/api/question/{qid}")
            await self.call("GET", d["image"]["src"])
            if d.get("image_space"):
                await self.call("GET", d["image_space"]["src"])
            if d.get("paper_pdf"):
                await self.call("GET", f"/paper/{qid}")
        await self.call("GET", "/api/question/nope", status=404)
        await self.call("GET", "/q/../caie.db", status=404)

    async def test_add_to_set(self):
        """Picked rows go into a new set, then more into it; unknown ids are left out."""
        a, b = questions(n=4)[:2], questions(n=4)[2:]
        sid = await self.make_set(a + ["nope"])
        s = await self.json("GET", f"/api/sets/{sid}")
        self.assertEqual(s["items"], a)
        s = await self.json("PATCH", f"/api/sets/{sid}", {"add": b + a[:1]})
        self.assertEqual(s["items"], a + b)


@NEED
class SearchPage(Api):
    async def find(self, **p):
        return await self.json("POST", "/api/find", p)

    async def test_conditions(self):
        """Keywords alone, then narrowed by exam, paper, topic, year, where to look, part
        type and explanation; each narrowing never finds more."""
        all_ = await self.find(q="integration")
        self.assertGreater(all_["total"], 0)
        exam = await self.find(q="integration", exams=["9709"])
        self.assertLessEqual(exam["total"], all_["total"])
        for extra in ({"comps": ["3"]}, {"from": 2022, "to": 2024}, {"cols": ["stem"]},
                      {"expl": "y"}, {"expl": "n"}, {"sort": "year"}, {"topics": ["9709:3.5"]}):
            r = await self.find(q="integration", exams=["9709"], **extra)
            self.assertLessEqual(r["total"], exam["total"], extra)

    async def test_query_forms(self):
        """Phrases, OR, NOT, word forms and text that is not a query at all."""
        for q in ('"partial fractions"', "integration OR differentiation", "integration -parts",
                  "integrating", "x-axis", 'unbalanced "quote', "((", "*", "", "AND OR NOT"):
            r = await self.find(q=q, exams=["9709"])
            self.assertIn("total", r, q)

    async def test_needs_keywords(self):
        """Without keywords the page lists nothing (browsing is the query page's), but a
        paper code alone finds that paper."""
        self.assertEqual((await self.find(exams=["9231"]))["total"], 0)
        self.assertGreater((await self.find(q="9709/32/O/N/24"))["total"], 0)


@NEED
class SetsPage(Api):
    async def test_life_of_a_set(self):
        """Make, rename, reorder, remove, export and import back, delete."""
        items = questions(n=5)
        sid = await self.make_set(items, "测试 题组")
        self.assertIn(sid, [s["id"] for s in await self.json("GET", "/api/sets")])
        s = await self.json("PATCH", f"/api/sets/{sid}", {"name": "测试 改名"})
        self.assertEqual(s["name"], "测试 改名")
        s = await self.json("PATCH", f"/api/sets/{sid}", {"items": items[::-1]})
        self.assertEqual(s["items"], items[::-1])
        s = await self.json("PATCH", f"/api/sets/{sid}", {"items": items[1:]})
        self.assertEqual(s["count"], 4)
        exported = await self.json("GET", f"/api/sets/{sid}/export")
        back = await self.json("POST", "/api/sets/import", exported)
        self.assertEqual(back["items"], items[1:])
        await self.call("POST", "/api/sets/import", {"nothing": True}, status=400)
        await self.json("DELETE", f"/api/sets/{sid}")
        await self.call("GET", f"/api/sets/{sid}", status=404)

    async def test_set_page(self):
        """The set page: its practice paper, its pages, its reading documents."""
        sid = await self.make_set(questions(n=3))
        pages = (await self.json("GET", f"/api/sets/{sid}/paper"))["pages"]
        for n in range(pages):
            await self.call("GET", f"/api/sets/{sid}/paper/{n}.png")
        await self.call("GET", f"/api/sets/{sid}/paper/{pages}.png", status=404)
        for kind in ("scheme", "explanation"):
            await self.call("GET", f"/doc/{sid}/{kind}")
            r = await self.call("GET", f"/doc/{sid}/{kind}?download=1")
            self.assertIn("attachment", r.headers["Content-Disposition"])
        await self.call("GET", f"/doc/{sid}/other", status=404)
        empty = await self.make_set([])
        await self.call("GET", f"/api/sets/{empty}/paper", status=404)
        await self.call("POST", f"/api/sets/{empty}/board", status=400)

    async def test_output(self):
        """输出 with each built-in template, with each format and 版面, and its preview."""
        sid = await self.make_set(questions(n=3))
        for t in await self.json("GET", "/api/templates"):
            if not t["builtin"]:
                continue
            await self.json("POST", f"/api/sets/{sid}/zip/preview", {"template": t["id"]})
            r = await self.call("POST", f"/api/sets/{sid}/output", {"template": t["id"]})
            data = await r.read()
            if t["settings"]["format"] == "pdf":
                self.assertTrue(data.startswith(b"%PDF"), t["id"])
            else:
                self.assertTrue(zipfile.ZipFile(io.BytesIO(data)).namelist(), t["id"])
        for fmt in ("pdf", "zip", "images"):
            for space in (0, 3):
                body = {"settings": {"format": fmt, "documents": ["question_paper"]}, "body": "", "space": space}
                await self.call("POST", f"/api/sets/{sid}/output", body)
        await self.call("POST", f"/api/sets/{sid}/output", {"template": "nope"}, status=404)


@NEED
class Board(Api):
    async def test_long_set(self):
        """A set whose paper is longer than inksync's own bound (about 115 pages) opens,
        takes ink on its last page, and its export carries that ink."""
        import pymupdf
        from manager.server import HUB
        sid = await self.make_set(questions(n=160))
        bid = (await self.json("POST", f"/api/sets/{sid}/board"))["id"]
        await self.call("GET", f"/write/{bid}")
        self.assertEqual((await self.json("GET", "/api/boards/current"))["id"], bid)
        hub = self.client.app[HUB]
        pages = hub.board_meta(bid)["data"]["doc"]["pages"]
        self.assertGreater(len(pages), 115)
        self.assertEqual(len(hub.board_meta(bid)["data"]["labels"]), len(pages))
        await self.call("GET", f"/api/boards/{bid}/page/{len(pages) - 1}?w=600")
        y = sum(h for _, h in pages[:-1]) + 24 * (len(pages) - 1) + 400
        _, err = hub.board(bid).apply({"op": "add", "strokes": [{"id": "t1", "p": [100, y, .5, 300, y + 20, .5]}]})
        self.assertIsNone(err)
        boards = (await self.json("GET", f"/api/sets/{sid}/boards"))["boards"]
        self.assertEqual((boards[0]["pages"], boards[0]["strokes"]), (len(pages), 1))
        r = await self.call("POST", f"/api/boards/{bid}/export", {})
        with pymupdf.open(stream=await r.read(), filetype="pdf") as out, \
                pymupdf.open(os.path.join(paths.BOARDS, "papers", bid + ".pdf")) as plain:
            inked = [i for i in range(out.page_count)
                     if len(out[i].get_drawings()) != len(plain[i].get_drawings())]
        self.assertEqual(inked, [len(pages) - 1])
        r = await self.call("POST", f"/api/sets/{sid}/output",
                            {"settings": {"format": "zip", "answers": "written_pdf"}, "body": ""})
        self.assertTrue(any("批注" in n for n in zipfile.ZipFile(io.BytesIO(await r.read())).namelist()))

    async def test_whole_paper_labels_follow_layout(self):
        """A whole paper is the original PDF only at 宽松; at another step the board's page
        labels come from the layout, one per page."""
        import pymupdf
        from manager import bank, paper, settings
        from manager.server import HUB
        rows = sorted((r for r in bank.rows("9709") if r["code"] == "9709/32/O/N/24"), key=lambda r: int(r["q"]))
        sid = await self.make_set([r["id"] for r in rows])
        self.assertTrue(paper.original_pdf(paper._rows([r["id"] for r in rows])))
        before = settings.load()["space"]
        try:
            for space in (0, 3):
                settings.save({"space": space})
                bid = (await self.json("POST", f"/api/sets/{sid}/board"))["id"]
                meta = self.client.app[HUB].board_meta(bid)
                with pymupdf.open(os.path.join(paths.BOARDS, "papers", bid + ".pdf")) as d:
                    self.assertEqual(len(meta["data"]["labels"]), d.page_count, space)
                if space == 0:                       # laid out again: the last page ends with the last question
                    self.assertTrue(meta["data"]["labels"][-1].endswith(f"Q{rows[-1]['q']}"), meta["data"]["labels"])
        finally:
            settings.save({"space": before})


@NEED
class TemplatesPage(Api):
    async def test_life_of_a_template(self):
        builtin = [t for t in await self.json("GET", "/api/templates") if t["builtin"]]
        self.assertTrue(builtin)
        t = await self.json("POST", "/api/templates", {"name": "测试 模板", "settings": {"format": "pdf"}, "body": "说明"})
        self.assertEqual(t["settings"]["format"], "pdf")
        t2 = await self.json("POST", "/api/templates", {"name": "测试 模板", "settings": {}, "body": ""})
        self.assertNotEqual(t2["name"], t["name"])           # names stay apart
        t = await self.json("PUT", f"/api/templates/{t['id']}",
                            {"name": "测试 改名", "settings": {"format": "zip", "per_question": ["image", "text"]}})
        self.assertEqual((t["name"], t["settings"]["per_question"]), ("测试 改名", ["image", "text"]))
        sid = await self.make_set(questions(n=2))
        await self.call("POST", f"/api/sets/{sid}/output", {"template": t["id"]})
        await self.json("DELETE", f"/api/templates/{t['id']}")
        await self.call("DELETE", f"/api/templates/{t['id']}", status=404)
        await self.call("PUT", f"/api/templates/{builtin[0]['id']}", {"name": "x"}, status=403)
        await self.call("DELETE", f"/api/templates/{builtin[0]['id']}", status=403)


def flow_graph(name):
    """题库 → 筛选 (Paper 1, 6 marks or more) → 限制数量 3 → 新建题组, 导出, 练习卷."""
    node = lambda nid, kind, **params: {"id": nid, "type": kind, "x": 0, "y": 0, "params": params}
    link = lambda a, b, i=0: {"from": [a, 0], "to": [b, i]}
    return {"name": name, "nodes": [
        node("bank", "bank", exam="9709"),
        node("filter", "filter", conds=[{"field": "component", "op": "=", "value": "1"},
                                        {"field": "marks", "min": "6", "max": ""}]),
        node("take", "take", n=3),
        node("set", "newset"), node("out", "export", template="default"), node("paper", "paper")],
        "links": [link("bank", "filter"), link("filter", "take"), link("take", "set"),
                  link("take", "out"), link("take", "paper")]}


@NEED
class FlowsPage(Api):
    async def test_builtin_flows_evaluate(self):
        catalog = await self.json("GET", "/api/flows/catalog")
        self.assertIn("filter", catalog["nodes"])
        flows = await self.json("GET", "/api/flows")
        self.assertTrue(any(f["builtin"] for f in flows))
        for f in flows:
            g = await self.json("GET", f"/api/flows/{f['id']}")
            r = await self.json("POST", "/api/flows/eval", g)
            self.assertEqual(r["errors"], {}, f["name"])

    async def test_life_of_a_flow(self):
        """Make, run (a set, a ZIP and a practice paper), run again (the same set), rename,
        delete; a cycle and a missing input are reported, not raised."""
        g = await self.json("POST", "/api/flows", flow_graph("测试 流程"))
        r = await self.json("POST", "/api/flows/eval", g)
        self.assertEqual(r["errors"], {})
        self.assertEqual(r["ports"]["take"][0]["count"], 3)
        r = await self.json("POST", f"/api/flows/{g['id']}/run", g)
        self.assertEqual(r["errors"], {})
        kinds = sorted(o["kind"] for o in r["outputs"])
        self.assertEqual(kinds, ["pdf", "set", "zip"])
        for o in r["outputs"]:
            if o.get("file"):
                await self.call("GET", f"/api/flows/{g['id']}/out/{o['file']}")
        sid = next(o["set"] for o in r["outputs"] if o["kind"] == "set")
        self.assertEqual((await self.json("GET", f"/api/sets/{sid}"))["count"], 3)
        self.assertIsNotNone(await self.json("GET", f"/api/flows/{g['id']}/last"))
        g = await self.json("PUT", f"/api/flows/{g['id']}", {**g, "name": "测试 改名"})
        r = await self.json("POST", f"/api/flows/{g['id']}/run", g)
        self.assertEqual(next(o["set"] for o in r["outputs"] if o["kind"] == "set"), sid)
        bad = dict(g, links=g["links"] + [{"from": ["take", 0], "to": ["filter", 0]}])
        await self.call("POST", "/api/flows/eval", bad, status=400)
        loose = dict(g, links=[l for l in g["links"] if l["to"][0] != "filter"])
        self.assertIn("filter", (await self.json("POST", "/api/flows/eval", loose))["errors"])
        await self.call("GET", f"/api/flows/{g['id']}/out/..%2Fx", status=404)
        await self.json("DELETE", f"/api/flows/{g['id']}")
        await self.call("GET", f"/api/flows/{g['id']}", status=404)

    def test_season_is_written_as_the_papers_write_it(self):
        from manager import flow
        g = {"nodes": [{"id": "f", "type": "filter", "params": {"conds": [{"field": "season", "op": "=", "value": "6"}]}}]}
        self.assertIn("考季 = M/J", flow.summary(g))
        self.assertNotIn("月", flow.summary(g))

    async def test_builtin_is_copied_not_changed(self):
        flows = await self.json("GET", "/api/flows")
        b = next(f for f in flows if f["builtin"])
        g = await self.json("GET", f"/api/flows/{b['id']}")
        saved = await self.json("PUT", f"/api/flows/{b['id']}", g)
        self.assertNotEqual(saved["id"], b["id"])
        await self.call("DELETE", f"/api/flows/{b['id']}", status=403)
        await self.json("DELETE", f"/api/flows/{saved['id']}")


@NEED
class SettingsPage(Api):
    async def test_options_and_preview(self):
        """Each option is saved and read back; a value of the wrong kind is ignored; the
        preview follows every footer combination and step."""
        await self.make_set(questions())
        before = await self.json("GET", "/api/settings")
        s = await self.json("PUT", "/api/settings", {"footer_name": False, "theme": "dark", "space": 1})
        self.assertEqual((s["footer_name"], s["theme"], s["space"]), (False, "dark", 1))
        s = await self.json("PUT", "/api/settings", {"space": "wide", "unknown": 1})
        self.assertEqual(s["space"], 1)
        self.assertNotIn("unknown", s)
        s = await self.json("PUT", "/api/settings", {"space": 9})
        self.assertEqual(s["space"], 3)
        for bits in ("000", "101", "111"):
            for step in range(4):
                key = bits + str(step)
                self.assertGreater((await self.json("GET", f"/api/settings/preview/{key}"))["pages"], 0)
                await self.call("GET", f"/api/settings/preview/{key}/0.png")
        await self.call("GET", "/api/settings/preview/1114", status=404)
        await self.json("PUT", "/api/settings", before)


@NEED
class Ipad(Api):
    async def test_shell_pages(self):
        await self.call("GET", "/ipad")
        await self.call("GET", "/board/write.html")
        await self.call("GET", "/inksync/inkpad.js")


if __name__ == "__main__":
    unittest.main()
