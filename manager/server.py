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
  /api/sets/<id>/paper   {pages, whole}: the question paper (F4), built on demand
  /api/sets/<id>/paper.pdf, /api/sets/<id>/paper/<n>.png
  /doc/<id>/scheme, /doc/<id>/explanation   reading documents (F6); ?download=1 to save
  /api/settings          GET, PUT {footer_*, theme}
  /api/templates         GET list, POST create {name, settings, body}
  /api/templates/<id>    PUT {name, settings, body}, DELETE (built-in ones are read-only)
  /api/sets/<id>/zip/preview  POST {template} or {settings, body}: files, sizes, README (F7)
  /api/sets/<id>/zip          POST the same: the ZIP
  /api/sets/<id>/output       POST the same: one PDF or a ZIP, by the template's format (the set page's 输出)
  /api/sets/<id>/board   POST: open (make) the writing board for the set's question paper (F5)
  /api/sets/<id>/boards  GET the set's boards (with their stroke counts) and its latest answer PDF
  /api/sets/<id>/answers.pdf  the latest exported answer PDF
  /api/boards/<id>/page/<n>?w=   a page of a board's paper
  /api/boards/<id>/export     POST {name, scheme, explanation}: the paper with the ink (PDF, or ZIP)
  /api/flows            GET list, POST save as new {graph}; /api/flows/catalog: node types and fields (F9)
  /api/flows/<id>        GET, PUT save, DELETE (built-in graphs are read-only: saving makes a copy)
  /api/flows/eval        POST {graph}: every port's count and the node details, no outputs
  /api/flows/<id>/run    POST {graph}: the same, and the output nodes make their files and sets
  /api/flows/<id>/out/<file>?name=   a file a run made
  /write/<board id>      the writing page (white-board's toolbar and pen tray, manager/web/board/); makes it current
  /ipad                  the iPad shell's page: the writing page following the current board, or a wait
  /ws, /inksync/         ink sync and its front end (manager/vendor/inksync, from white-board)
"""
import json
import os

from aiohttp import web

from lib import paths
import asyncio
import urllib.parse

from manager import __version__, bank, board, docs, export, flow, paper, sets, settings, templates
from manager.vendor.inksync import DefaultPolicy, FileStorage, Hub, mount, serve_sdk
from manager.vendor.inksync.netinfo import advertise

WEB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")
HUB = web.AppKey("hub", Hub)


class BoardPolicy(DefaultPolicy):
    """Boards are made by the server from a set; pages can write and clear, not rename."""

    def can_create(self, who, board_id, spec):
        return False

    def can_edit_meta(self, who, meta, patch):
        return False
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
            "missing": [q for q in s["items"] if q not in rows], "docs": docs.counts(s)}


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
        "Content-Disposition": "attachment; filename*=UTF-8''" + urllib.parse.quote(s["name"] + ".json")})


async def set_import(request):
    try:
        ids, title = sets.parse_import(await request.json())
    except (ValueError, AttributeError) as e:
        raise web.HTTPBadRequest(text=str(e) or "文件无法读取")
    known = bank.exists(ids)
    s = sets.create(sets.import_name(), [q for q in ids if q in known], "import")
    view = _set_view(s)
    view["unknown"] = [q for q in ids if q not in known]
    return web.json_response(view)


async def _paper(request):
    s = _get(request.match_info["sid"])
    return await asyncio.get_running_loop().run_in_executor(None, paper.build, s), s


async def paper_info(request):
    path, s = await _paper(request)
    return web.json_response({"pages": paper.page_count(path), "whole": bool(paper.whole_paper(paper._rows(s["items"])))})


async def paper_pdf(request):
    path, s = await _paper(request)
    return web.FileResponse(path, headers={
        "Content-Type": "application/pdf",
        "Content-Disposition": "inline; filename*=UTF-8''" + urllib.parse.quote(s["name"] + ".pdf")})


async def paper_page(request):
    path, s = await _paper(request)
    n = int(request.match_info["n"])
    png = await asyncio.get_running_loop().run_in_executor(None, paper.page_png, path, n)
    return web.Response(body=png, content_type="image/png", headers={"Cache-Control": "no-cache"})


async def reading(request):
    s = _get(request.match_info["sid"])
    kind = request.match_info["kind"]
    if kind not in ("scheme", "explanation"):
        raise web.HTTPNotFound()
    page = docs.scheme(s) if kind == "scheme" else docs.explanation(s)
    headers = {}
    if request.query.get("download"):
        name = s["name"] + (" 评分细则" if kind == "scheme" else " 详解") + ".html"
        headers["Content-Disposition"] = "attachment; filename*=UTF-8''" + urllib.parse.quote(name)
    return web.Response(text=page, content_type="text/html", headers=headers)


async def settings_get(request):
    return web.json_response(settings.load())


async def settings_put(request):
    return web.json_response(settings.save(await request.json()))


async def template_list(request):
    return web.json_response(templates.all_templates())


async def template_create(request):
    b = await request.json()
    return web.json_response(templates.create(b.get("name", ""), b.get("settings"), b.get("body", "")))


async def template_put(request):
    b = await request.json()
    try:
        return web.json_response(templates.update(request.match_info["tid"], b.get("name"),
                                                  b.get("settings"), b.get("body")))
    except KeyError:
        raise web.HTTPNotFound()
    except PermissionError:
        raise web.HTTPForbidden()


async def template_delete(request):
    try:
        templates.delete(request.match_info["tid"])
    except KeyError:
        raise web.HTTPNotFound()
    except PermissionError:
        raise web.HTTPForbidden()
    return web.json_response({"ok": True})


async def _export_args(request):
    s = _get(request.match_info["sid"])
    b = await request.json()
    if b.get("template"):
        try:
            t = templates.get(b["template"])
        except KeyError:
            raise web.HTTPNotFound()
        args = s, t["settings"], t["body"]
    else:
        args = s, templates.clean(b.get("settings")), b.get("body", "")
    if args[1]["answers"] == "written_pdf":       # the annotated copy as the ink is now
        await board.refresh_answers(request.app[HUB], s)
    return args


async def zip_preview(request):
    args = await _export_args(request)
    return web.json_response(await asyncio.get_running_loop().run_in_executor(None, export.preview, *args))


async def zip_download(request):
    args = await _export_args(request)
    data = await asyncio.get_running_loop().run_in_executor(None, export.zip_bytes, *args)
    return web.Response(body=data, content_type="application/zip", headers={
        "Content-Disposition": "attachment; filename*=UTF-8''" + urllib.parse.quote(export.zip_name(args[0]))})


async def output(request):
    """The set page's 输出: one PDF, or a ZIP, by the template's format."""
    args = await _export_args(request)
    loop = asyncio.get_running_loop()
    if args[1]["format"] == "pdf":
        path, name = await loop.run_in_executor(None, export.single_pdf, args[0], args[1])
        return web.FileResponse(path, headers={
            "Content-Type": "application/pdf",
            "Content-Disposition": "attachment; filename*=UTF-8''" + urllib.parse.quote(name)})
    data = await loop.run_in_executor(None, export.zip_bytes, *args)
    return web.Response(body=data, content_type="application/zip", headers={
        "Content-Disposition": "attachment; filename*=UTF-8''" + urllib.parse.quote(export.zip_name(args[0]))})


async def board_open(request):
    s = _get(request.match_info["sid"])
    if not s["items"]:
        raise web.HTTPBadRequest(text="题组中没有题目")
    bid = await board.open_for(request.app[HUB], s)
    await board.follow(request.app[HUB], bid)
    return web.json_response({"id": bid})


async def board_list(request):
    s = _get(request.match_info["sid"])
    return web.json_response({"boards": await board.boards_with_ink(request.app[HUB], s["id"]), "answers": board.answers_info(s)})


async def answers_pdf(request):
    s = _get(request.match_info["sid"])
    p = export.answer_pdf(s)
    if not p:
        raise web.HTTPNotFound()
    return web.FileResponse(p, headers={
        "Content-Type": "application/pdf",
        "Content-Disposition": "attachment; filename*=UTF-8''" + urllib.parse.quote(s["name"] + " 批注版.pdf")})


def _board(request):
    bid = request.match_info["bid"]
    meta = request.app[HUB].board_meta(bid)
    if not meta or not os.path.isfile(board.pdf_of(bid)):
        raise web.HTTPNotFound()
    return bid, meta


async def board_page(request):
    bid, meta = _board(request)
    n = int(request.match_info["n"])
    if n >= len(meta["layers"]):
        raise web.HTTPNotFound()
    png = await asyncio.get_running_loop().run_in_executor(
        None, board.page_png, bid, n, request.query.get("w", "1024"))
    return web.Response(body=png, content_type="image/png", headers={"Cache-Control": "max-age=31536000, immutable"})


async def board_export(request):
    bid, meta = _board(request)
    s = _get(meta["data"]["set"])
    b = await request.json()
    name = (b.get("name") or "").strip().replace("/", "-") or s["name"].replace("/", "-") + " 批注版"
    data, fname = await board.export_board(request.app[HUB], s, bid, name, bool(b.get("scheme")), bool(b.get("explanation")))
    return web.Response(body=data, content_type="application/zip" if fname.endswith(".zip") else "application/pdf",
                        headers={"Content-Disposition": "attachment; filename*=UTF-8''" + urllib.parse.quote(fname)})


async def write_page(request):
    bid, _ = _board(request)
    await board.follow(request.app[HUB], bid)
    return web.FileResponse(os.path.join(WEB, "board", "write.html"), headers={"Cache-Control": "no-cache"})


async def ipad_page(request):
    """The iPad's page: the writing page following the Mac's current board, or a wait."""
    name = "write.html" if board.current() else "wait.html"
    return web.FileResponse(os.path.join(WEB, "board", name), headers={"Cache-Control": "no-cache"})


async def current_board(request):
    return web.json_response({"id": board.current()})


async def flow_list(request):
    return web.json_response([{**{k: g[k] for k in ("id", "name", "builtin")}, "summary": flow.summary(g)}
                              for g in flow.all_flows()])


async def flow_catalog(request):
    return web.json_response(flow.catalog())


async def flow_get(request):
    try:
        g = flow.get(request.match_info["fid"])
        return web.json_response({**g, "summary": flow.summary(g)})
    except KeyError:
        raise web.HTTPNotFound()


async def flow_create(request):
    return web.json_response(flow.save(await request.json(), new=True))


async def flow_put(request):
    g = await request.json()
    g["id"] = request.match_info["fid"]
    try:
        g["builtin"] = flow.get(g["id"])["builtin"]
    except KeyError:
        raise web.HTTPNotFound()
    return web.json_response(flow.save(g))


async def flow_delete(request):
    try:
        flow.delete(request.match_info["fid"])
    except KeyError:
        raise web.HTTPNotFound()
    except PermissionError:
        raise web.HTTPForbidden()
    return web.json_response({"ok": True})


async def _flow_view(g, make):
    try:
        return web.json_response(await asyncio.get_running_loop().run_in_executor(None, flow.view, g, make))
    except flow.FlowError as e:
        raise web.HTTPBadRequest(text=str(e))


async def flow_eval(request):
    g = await request.json()
    g["id"] = g.get("id") or "draft"
    return await _flow_view(g, False)


async def flow_run(request):
    g = await request.json()
    g["id"] = request.match_info["fid"]
    return await _flow_view(g, True)


async def flow_last(request):
    return web.json_response(flow.last_run(request.match_info["fid"]))


async def flow_out(request):
    p = flow.output_file(request.match_info["fid"], request.match_info["name"])
    if not p:
        raise web.HTTPNotFound()
    name = request.query.get("name") or os.path.basename(p)
    return web.FileResponse(p, headers={"Content-Disposition": "attachment; filename*=UTF-8''" + urllib.parse.quote(name)})


async def image(request):
    rel = request.match_info["path"]
    if rel.split("/")[0] not in IMG_DIRS or ".." in rel:
        raise web.HTTPNotFound()
    path = paths.resolve(rel)
    if not path:
        raise web.HTTPNotFound()
    return web.FileResponse(path, headers={"Cache-Control": "max-age=86400"})


async def original(request):
    from lib import db
    r = db.connect().execute("SELECT * FROM questions WHERE id = ?",
                             (request.match_info["qid"],)).fetchone()
    p = bank.paper_pdf(r) if r else None
    if not p:
        raise web.HTTPNotFound()
    return web.FileResponse(p, headers={"Content-Type": "application/pdf"})


async def index(request):
    return web.FileResponse(os.path.join(WEB, "index.html"), headers={"Cache-Control": "no-cache"})


# The page's own scripts and styles change with the code: the browser checks them on every
# load (a 304 when unchanged) instead of running a copy it kept from an older version.
FRESH = ("/static/", "/board/", "/inksync/")


@web.middleware
async def revalidate(request, handler):
    resp = await handler(request)
    if request.path.startswith(FRESH) and "Cache-Control" not in resp.headers:
        resp.headers["Cache-Control"] = "no-cache"
    return resp


def make_app():
    app = web.Application(middlewares=[revalidate])
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
    app.router.add_get(r"/api/sets/{sid}/paper", paper_info)
    app.router.add_get(r"/api/sets/{sid}/paper.pdf", paper_pdf)
    app.router.add_get(r"/api/sets/{sid}/paper/{n:\d+}.png", paper_page)
    app.router.add_get(r"/doc/{sid}/{kind}", reading)
    app.router.add_post(r"/api/sets/{sid}/zip/preview", zip_preview)
    app.router.add_post(r"/api/sets/{sid}/zip", zip_download)
    app.router.add_post(r"/api/sets/{sid}/output", output)
    app.router.add_post(r"/api/sets/{sid}/board", board_open)
    app.router.add_get(r"/api/sets/{sid}/boards", board_list)
    app.router.add_get(r"/api/sets/{sid}/answers.pdf", answers_pdf)
    app.router.add_get(r"/api/boards/{bid}/page/{n:\d+}", board_page)
    app.router.add_post(r"/api/boards/{bid}/export", board_export)
    app.router.add_get(r"/write/{bid}", write_page)
    app.router.add_get("/ipad", ipad_page)
    app.router.add_get("/api/boards/current", current_board)
    app.router.add_get("/api/flows", flow_list)
    app.router.add_post("/api/flows", flow_create)
    app.router.add_get("/api/flows/catalog", flow_catalog)
    app.router.add_post("/api/flows/eval", flow_eval)
    app.router.add_get(r"/api/flows/{fid}", flow_get)
    app.router.add_put(r"/api/flows/{fid}", flow_put)
    app.router.add_delete(r"/api/flows/{fid}", flow_delete)
    app.router.add_post(r"/api/flows/{fid}/run", flow_run)
    app.router.add_get(r"/api/flows/{fid}/last", flow_last)
    app.router.add_get(r"/api/flows/{fid}/out/{name}", flow_out)
    app.router.add_get("/api/templates", template_list)
    app.router.add_post("/api/templates", template_create)
    app.router.add_put(r"/api/templates/{tid}", template_put)
    app.router.add_delete(r"/api/templates/{tid}", template_delete)
    app.router.add_get("/api/settings", settings_get)
    app.router.add_put("/api/settings", settings_put)
    app.router.add_get(r"/q/{path:.+}", image)
    app.router.add_get(r"/paper/{qid}", original)
    app.router.add_static("/static/", WEB)
    app.router.add_static("/vendor/", os.path.join(paths.ASSETS, "vendor"))
    app.router.add_static("/board/", os.path.join(WEB, "board"))
    hub = Hub(FileStorage(board.ROOT), policy=BoardPolicy())
    hub.set_hello(board.hello)
    app[HUB] = hub
    mount(app, hub, path="/ws")
    serve_sdk(app, prefix="/inksync/")
    return app


def run(port=8910, host="0.0.0.0"):
    print(f"数据管理页 {__version__}: http://localhost:{port}/(在电脑的浏览器中打开;iPad 只用白板外壳,来源填 @qb-manage)\n"
          f"题组: {paths.SETS}\n按 Ctrl-C 停止")
    app = make_app()
    advertise(app, port=port, source="qb-manage", path="/ipad")   # the iPad shell opens /ipad (@qb-manage; app/ is @qb)
    web.run_app(app, host=host, port=port, print=None)
