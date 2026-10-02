"""The data manager's server (docs/data-manager.md). Read-only on the bank; question
sets and later outputs live in paths.WORK.

    python3 qb.py manage [--port 8910]

  /                      the page (manager/web/)
  /ds/                   ENDFIELD React: React, component bundle, tokens, fonts
  /vendor/               KaTeX (assets/vendor/)
  /q/<imgdir>/<file>     question crops from data/
  /paper/<qid>           the original question paper PDF, opened at the question's page
  /api/meta              exams, papers, topics, years with counts
  /api/questions?exam=   every question of one exam (the query filters in the page)
  /api/search?exam=&q=   ids whose text or mark scheme matches
  /api/question/<id>     one question: images, mark scheme rows, text, explanation
  /api/sets              GET list, POST create {name, items, source}
  /api/sets/<id>         GET, PATCH {name, items, add}, DELETE
  /api/sets/<id>/export  alevel-question-set/v1
  /api/sets/import       POST an alevel-question-set/v1 document
"""
import json
import os

from aiohttp import web

from lib import paths
from manager import bank, sets

WEB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")
IMG_DIRS = {"img9709", "img9231", "img9618", "img_adm", "img_tara",
            "img9709" + paths.ANS_SUFFIX, "img9231" + paths.ANS_SUFFIX, "img9618" + paths.ANS_SUFFIX}


def _set_view(s):
    """A set with the numbers the page shows next to its name."""
    rows = {}
    if s["items"]:
        from lib import db
        con = db.connect()
        ids = s["items"]
        for i in range(0, len(ids), 500):
            chunk = ids[i:i + 500]
            for r in con.execute(f"SELECT id, marks FROM questions WHERE id IN "
                                 f"({','.join('?' * len(chunk))})", chunk):
                rows[r["id"]] = r["marks"] or 0
    return {**s, "count": len(s["items"]), "marks": sum(rows.values()),
            "missing": [q for q in s["items"] if q not in rows]}


async def meta(request):
    return web.json_response(bank.meta())


async def questions(request):
    return web.json_response(bank.rows(request.query.get("exam", "9709")))


async def search(request):
    q = request.query
    return web.json_response(bank.search(q.get("exam", "9709"), q.get("q", "")))


async def question(request):
    d = bank.detail(request.match_info["qid"])
    if not d:
        raise web.HTTPNotFound()
    return web.json_response(d)


async def set_list(request):
    return web.json_response([_set_view(s) for s in sets.all_sets()])


async def set_create(request):
    body = await request.json()
    items = [q for q in body.get("items", []) if q in bank.exists(body.get("items", []))]
    return web.json_response(_set_view(sets.create(body.get("name", ""), items,
                                                   body.get("source", "manual"))))


def _get(sid):
    try:
        return sets.get(sid)
    except (KeyError, FileNotFoundError):
        raise web.HTTPNotFound()


async def set_get(request):
    return web.json_response(_set_view(_get(request.match_info["sid"])))


async def set_patch(request):
    sid = request.match_info["sid"]
    _get(sid)
    body = await request.json()
    known = bank.exists((body.get("items") or []) + (body.get("add") or []))
    items = [q for q in body["items"] if q in known] if "items" in body else None
    add = [q for q in body.get("add") or [] if q in known]
    return web.json_response(_set_view(sets.update(sid, body.get("name"), items, add)))


async def set_delete(request):
    sid = request.match_info["sid"]
    _get(sid)
    sets.delete(sid)
    return web.json_response({"ok": True})


async def set_export(request):
    s = _get(request.match_info["sid"])
    return web.json_response(sets.export(s), headers={
        "Content-Disposition": "attachment; filename*=UTF-8''"
        + __import__("urllib.parse").parse.quote(s["name"] + ".json")})


async def set_import(request):
    try:
        ids, title = sets.parse_import(await request.json())
    except (ValueError, AttributeError) as e:
        raise web.HTTPBadRequest(text=str(e) or "无法读取")
    known = bank.exists(ids)
    s = sets.create(sets.import_name(), [q for q in ids if q in known], "import")
    view = _set_view(s)
    view["unknown"] = [q for q in ids if q not in known]
    return web.json_response(view)


async def image(request):
    rel = request.match_info["path"]
    if rel.split("/")[0] not in IMG_DIRS or ".." in rel:
        raise web.HTTPNotFound()
    path = paths.resolve(rel)
    if not path:
        raise web.HTTPNotFound()
    return web.FileResponse(path, headers={"Cache-Control": "max-age=86400"})


async def paper(request):
    from lib import db
    r = db.connect().execute("SELECT * FROM questions WHERE id = ?",
                             (request.match_info["qid"],)).fetchone()
    p = bank.paper_pdf(r) if r else None
    if not p:
        raise web.HTTPNotFound()
    return web.FileResponse(p, headers={"Content-Type": "application/pdf"})


async def index(request):
    return web.FileResponse(os.path.join(WEB, "index.html"), headers={"Cache-Control": "no-cache"})


def make_app():
    app = web.Application()
    app.router.add_get("/", index)
    app.router.add_get("/api/meta", meta)
    app.router.add_get("/api/questions", questions)
    app.router.add_get("/api/search", search)
    app.router.add_get(r"/api/question/{qid}", question)
    app.router.add_get("/api/sets", set_list)
    app.router.add_post("/api/sets", set_create)
    app.router.add_post("/api/sets/import", set_import)
    app.router.add_get(r"/api/sets/{sid}", set_get)
    app.router.add_patch(r"/api/sets/{sid}", set_patch)
    app.router.add_delete(r"/api/sets/{sid}", set_delete)
    app.router.add_get(r"/api/sets/{sid}/export", set_export)
    app.router.add_get(r"/q/{path:.+}", image)
    app.router.add_get(r"/paper/{qid}", paper)
    app.router.add_static("/static/", WEB)
    app.router.add_static("/vendor/", os.path.join(paths.ASSETS, "vendor"))
    return app


def run(port=8910, host="0.0.0.0"):
    print(f"数据管理页: http://localhost:{port}/(局域网内的 iPad 用本机地址访问)\n"
          f"题组: {paths.SETS}\n按 Ctrl-C 停止")
    web.run_app(make_app(), host=host, port=port, print=None)
