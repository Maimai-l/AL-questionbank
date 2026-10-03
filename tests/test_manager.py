"""Tests for the data manager (manager/): the server's pages and the paths a person takes
through them, the practice paper's 版面 steps and the writing board.

    python3 -m unittest discover tests

They read the bank in data/ (python3 sync.py pull) and write only to temporary folders:
QB_WORK and CAIE_EXPORTS point there before anything is imported.
"""
import json
import os
import shutil
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TMP = tempfile.mkdtemp(prefix="qb-test-")
os.environ["QB_WORK"] = os.path.join(TMP, "work")
os.environ["CAIE_EXPORTS"] = os.path.join(TMP, "exports")
sys.path.insert(0, ROOT)

from lib import paths  # noqa: E402

HAVE_DATA = os.path.exists(paths.DB)
NEED = unittest.skipUnless(HAVE_DATA, "needs data/ (python3 sync.py pull)")


def tearDownModule():
    shutil.rmtree(TMP, ignore_errors=True)


def p3_questions(n):
    """The first n 9709 Paper 3 questions of the bank."""
    from manager import bank
    return [r["id"] for r in bank.rows("9709") if r["component"] == "3"][:n]


@NEED
class Paper(unittest.TestCase):
    def test_steps_grow(self):
        """Each 版面 step has at least as many pages as the one before it."""
        from manager import paper, sets
        s = sets.create("测试 版面", p3_questions(6))
        counts = []
        for space in range(len(paper.SPACE)):
            with paper.pymupdf.open(paper.build(s, space=space)) as d:
                counts.append(d.page_count)
        self.assertEqual(counts, sorted(counts))
        self.assertLess(counts[0], counts[-1])

    def test_compact_has_no_answer_lines(self):
        """紧凑 leaves out the lines between parts as well as those after the last part."""
        from manager import paper
        rows = [r for r in paper._rows(p3_questions(40)) if r["syllabus"] == "9709"]
        checked = 0
        for r in rows:
            b = paper._block(r, 0)
            if b and paper._ruled_rows(paper._grey(paths.resolve(r["image"]))).any():
                self.assertFalse(paper._ruled_rows(b[0]).any(), r["id"])
                checked += 1
        self.assertGreater(checked, 0)

    def test_no_step_past_original(self):
        from manager import paper, settings
        self.assertEqual(paper.SPACE[-1], 1)
        os.makedirs(paths.WORK, exist_ok=True)
        with open(settings.PATH, "w", encoding="utf-8") as f:
            json.dump({"space": 4}, f)              # a fifth step was saved once
        self.assertEqual(settings.load()["space"], 3)


@NEED
class Server(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        import asyncio
        asyncio.get_running_loop().set_debug(False)   # the test case turns it on: slow-task notices
        from aiohttp.test_utils import TestClient, TestServer
        from manager import server
        app = server.make_app()
        del app.cleanup_ctx[app.cleanup_ctx.index(server.watch_bank)]   # no automatic flows here
        self.client = TestClient(TestServer(app))
        await self.client.start_server()

    async def asyncTearDown(self):
        await self.client.close()

    async def call(self, method, url, body=None, status=200):
        r = await self.client.request(method, url, json=body)
        if r.status != status:
            self.fail(f"{method} {url}: {r.status} {(await r.read())[:300]!r}")
        return r

    async def make_set(self, items):
        r = await self.call("POST", "/api/sets", {"name": "测试", "items": items})
        return (await r.json())["id"]

    async def test_pages_load(self):
        for url in ("/", "/api/meta", "/api/sets", "/api/templates", "/api/settings", "/api/flows",
                    "/api/questions?exam=9709", "/ipad"):
            await self.call("GET", url)

    async def test_settings_preview_every_step(self):
        await self.make_set(p3_questions(6))
        for step in range(4):
            r = await self.call("GET", f"/api/settings/preview/111{step}")
            self.assertGreater((await r.json())["pages"], 0)
            await self.call("GET", f"/api/settings/preview/111{step}/0.png")
        await self.call("GET", "/api/settings/preview/1114", status=404)

    async def test_search(self):
        r = await self.call("POST", "/api/find", {"q": "integration", "exams": ["9709"]})
        self.assertGreater((await r.json())["total"], 0)

    async def test_board_for_long_set(self):
        """A set whose paper is longer than inksync's own bound (about 115 pages) opens,
        takes ink on its last pages and exports it."""
        sid = await self.make_set(p3_questions(160))
        r = await self.call("POST", f"/api/sets/{sid}/board")
        bid = (await r.json())["id"]
        await self.call("GET", f"/write/{bid}")
        from manager.server import HUB
        meta = self.client.app[HUB].board_meta(bid)
        pages = meta["data"]["doc"]["pages"]
        self.assertGreater(len(pages), 115)
        self.assertEqual(len(meta["data"]["labels"]), len(pages))
        await self.call("GET", f"/api/boards/{bid}/page/{len(pages) - 1}?w=600")
        r = await self.call("GET", f"/api/sets/{sid}/boards")
        self.assertEqual((await r.json())["boards"][0]["pages"], len(pages))
        await self.call("POST", f"/api/boards/{bid}/export", {})


if __name__ == "__main__":
    unittest.main()
