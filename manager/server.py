"""The data manager's server (docs/data-manager.md). Read-only on the bank; question
sets, templates, flows, boards and outputs live in paths.WORK.

    python3 manage.py [--port 8910]          in the browser
    python3 manage.py window [--port 8910]   in a window of its own (pywebview)

  /                      the page (manager/web/index.html)
  /static/               the page's scripts and styles (manager/web/); /static/ds/: ENDFIELD React,
                         component bundle, tokens, fonts
  /board/                the writing page's own files (manager/web/board/)
  /vendor/               KaTeX (assets/vendor/)
  /q/<imgdir>/<file>     question crops from data/
  /paper/<qid>[?kind=ms] the original question paper PDF (opened at the question's page), or its mark scheme
  /api/meta              exams, papers, topics, years with counts
  /api/questions?exam=   every question of one exam (the query filters in the page)
  /api/search?exam=&q=   ids whose text or mark scheme matches (the query page)
  /api/find              POST the search page's conditions: matches with snippets (manager/search.py)
  /api/question/<id>     one question: images, mark scheme rows, text, explanation
  /api/sets              GET list, POST create {name, items, source}
  /api/sets/<id>         GET, PATCH {name, items, add}, DELETE
  /api/sets/<id>/export  alevel-question-set/v1
  /api/sets/import       POST an alevel-question-set/v1 document
  /api/sets/<id>/paper   {pages}: the practice paper (F4), built on demand
  /api/sets/<id>/paper/<n>.png  a page of it
  /doc/<id>/scheme, /doc/<id>/explanation   reading documents (F6); ?download=1 to save
  /api/settings          GET, PUT {footer_*, theme, space}
  /api/settings/preview/<key>[/<n>.png]    the settings page's preview: footer options and 版面 ("1013")
  /api/templates         GET list, POST create {name, settings, body}
  /api/templates/<id>    PUT {name, settings, body}, DELETE (built-in ones are read-only)
  /api/sets/<id>/zip/preview  POST {template} or {settings, body}, and space (版面, 0-3): files, sizes, README (F7)
  /api/sets/<id>/output       POST the same: one PDF or a ZIP, by the template's format (the set page's 输出)
  /api/sets/<id>/board   POST: open (make) the writing board for the set's question paper (F5)
  /api/sets/<id>/boards  GET the set's boards with their stroke counts
  /api/boards/current    the board the Mac opened last (the iPad follows it)
  /api/boards/<id>/page/<n>?w=   a page of a board's paper
  /api/boards/<id>/export     POST {name, scheme, explanation}: the paper with the ink (PDF, or ZIP)
  /api/flows            GET list, POST save as new {graph}; /api/flows/catalog: node types and fields (F9)
  /api/flows/<id>        GET, PUT save, DELETE (built-in graphs are read-only: saving makes a copy)
  /api/flows/eval        POST {graph}: every port's count and the node details, no outputs
  /api/flows/<id>/run    POST {graph}: the same, and the output nodes make their files and sets
  /api/flows/<id>/last   the last run: {ran, errors, outputs}
  /api/flows/<id>/out/<file>?name=   a file a run made
  /write/<board id>      the writing page (white-board's toolbar and pen tray, manager/web/board/); makes it current
  /ipad                  the iPad shell's page: the writing page following the current board, or a wait
  /ws, /inksync/         ink sync and its front end (manager/vendor/inksync, from white-board)
"""
import os
import re

from aiohttp import web

from lib import paths
import asyncio
import threading
import urllib.parse

from manager import __version__, bank, board, docs, export, flow, paper, sets, settings, templates
from manager import search as search_page   # the module; search() below is the query page's handler
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
    """A set with what the page shows next to its name: its question count, and which
    reading documents it has."""
    return {**s, "count": len(s["items"]), "docs": docs.counts(s)}


async def meta(request):
    return web.json_response(bank.meta())


async def questions(request):
    return web.json_response(bank.rows(request.query.get("exam", "9709")))


async def search(request):
    q = request.query
    return web.json_response(bank.search(q.get("exam", "9709"), q.get("q", "")))


async def find(request):
    p = await request.json()
    try:
        return web.json_response(await asyncio.get_running_loop().run_in_executor(None, search_page.find, p))
    except (ValueError, TypeError) as e:
        raise web.HTTPBadRequest(text=str(e))


async def question(request):
    d = bank.detail(request.match_info["qid"])
    if not d:
        raise web.HTTPNotFound()
    return web.json_response(d)


async def set_list(request):
    return web.json_response([_set_view(s) for s in sets.all_sets()])


async def set_create(request):
    body = await request.json()
    known = bank.exists(body.get("items", []))
    items = [q for q in body.get("items", []) if q in known]
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
        ids = sets.parse_import(await request.json())
    except (ValueError, AttributeError) as e:
        raise web.HTTPBadRequest(text=str(e) or "文件无法读取")
    known = bank.exists(ids)
    s = sets.create(sets.import_name(), [q for q in ids if q in known], "import")
    view = _set_view(s)
    view["unknown"] = [q for q in ids if q not in known]
    return web.json_response(view)


async def _paper(request):
    s = _get(request.match_info["sid"])
    try:
        return await asyncio.get_running_loop().run_in_executor(None, paper.build, s), s
    except paper.EmptyPaper as e:
        raise web.HTTPNotFound(text=str(e))


async def paper_info(request):
    path, s = await _paper(request)
    return web.json_response({"pages": paper.page_count(path)})


async def paper_page(request):
    path, s = await _paper(request)
    n = int(request.match_info["n"])
    if not 0 <= n < paper.page_count(path):
        raise web.HTTPNotFound()
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


FOOTER = ("footer_name", "footer_code", "footer_page")
PREVIEW = 6                                  # questions in the settings page's preview: two pages


def _preview(key):
    """The settings page's preview for key: the footer options and 版面 ("1013": name, no
    code, page; 版面 3). The first questions of the first set that has some, each key
    cached apart, so changing an option only reads a file built before."""
    sample = next((x for x in sets.all_sets() if x["items"]), None)
    if not sample or not re.fullmatch(r"[01]{3}[0-3]", key):
        return None
    s = {"id": "preview" + key[:3], "name": sample["name"], "items": sample["items"][:PREVIEW]}
    return paper.build(s, footer={k: b == "1" for k, b in zip(FOOTER, key)}, space=int(key[3]))


async def settings_preview(request):
    loop = asyncio.get_running_loop()
    bits = request.match_info["bits"]
    try:
        path = await loop.run_in_executor(None, _preview, bits)
    except paper.EmptyPaper:
        path = None
    if not path:
        raise web.HTTPNotFound()
    # the keys one click away (another footer option, another 版面), ready for that click
    near = [f"{n:03b}{bits[3]}" for n in range(8)] + [bits[:3] + str(n) for n in range(4)]
    for other in dict.fromkeys(near):
        if other != bits:
            loop.run_in_executor(None, _preview, other)
    return web.json_response({"pages": min(2, paper.page_count(path))})


async def settings_preview_page(request):
    try:
        path = await asyncio.get_running_loop().run_in_executor(None, _preview, request.match_info["bits"])
    except paper.EmptyPaper:
        path = None
    n = int(request.match_info["n"])
    if not path or not 0 <= n < min(2, paper.page_count(path)):
        raise web.HTTPNotFound()
    png = await asyncio.get_running_loop().run_in_executor(None, paper.page_png, path, n)
    return web.Response(body=png, content_type="image/png")


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
    # 版面 is the output's own choice, not the template's: the settings page's default unless
    # the dialog sends another (0 紧凑 .. 3 宽松)
    if isinstance(b.get("space"), int) and 0 <= b["space"] <= 3:
        args = s, {**args[1], "space": b["space"]}, args[2]
    if args[1]["answers"] == "written_pdf":       # the annotated copy as the ink is now
        await board.refresh_answers(request.app[HUB], s)
    return args


async def zip_preview(request):
    args = await _export_args(request)
    return web.json_response(await asyncio.get_running_loop().run_in_executor(None, export.preview, *args))


async def output(request):
    """The set page's 输出: one PDF, or a ZIP, by the template's format."""
    args = await _export_args(request)
    loop = asyncio.get_running_loop()
    if args[1]["format"] == "pdf":
        try:
            path, name = await loop.run_in_executor(None, export.single_pdf, args[0], args[1])
        except paper.EmptyPaper as e:
            raise web.HTTPBadRequest(text=str(e))
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
    try:
        bid = await board.open_for(request.app[HUB], s)
    except (paper.EmptyPaper, board.TooLong) as e:
        raise web.HTTPBadRequest(text=str(e))
    await board.follow(request.app[HUB], bid)
    return web.json_response({"id": bid})


async def board_list(request):
    s = _get(request.match_info["sid"])
    return web.json_response({"boards": await board.boards_with_ink(request.app[HUB], s["id"])})


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
    try:
        flow.get(g["id"])                    # only a flow that exists has an output folder
    except KeyError:
        raise web.HTTPNotFound()
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
    """The question's paper as a PDF: the original question paper, or with ?kind=ms its mark
    scheme (剑桥考试)."""
    from lib import db
    r = db.connect().execute("SELECT * FROM questions WHERE id = ?",
                             (request.match_info["qid"],)).fetchone()
    p = (bank.ms_pdf if request.query.get("kind") == "ms" else bank.paper_pdf)(r) if r else None
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


async def watch_bank(app):
    """Every minute: when the bank changed, run the automatic flows (flow.auto_run), once
    per bank version. First the searches' word list and index are built."""
    async def loop():
        run, tried = asyncio.get_running_loop().run_in_executor, None
        # The query page's word list and the search page's index, ready before the first
        # search (both are also built on first use). A few seconds after start, so that this
        # work, which holds the interpreter, does not slow the first page's own requests.
        await asyncio.sleep(5)
        await run(None, bank._words)
        await run(None, search_page.connect)
        while True:
            try:
                version = await run(None, flow.bank_version)
                if version != tried:
                    tried = version
                    r = await run(None, flow.auto_run)
                    if r is not None:
                        print("题库已更新，自动流程已运行" + ("，有错误" if any(x["errors"] for x in r.values()) else ""))
            except Exception as e:           # the page keeps working when a run fails
                print(f"自动流程未运行：{e}")
            await asyncio.sleep(60)
    task = asyncio.create_task(loop())
    yield
    task.cancel()


def make_app():
    app = web.Application(middlewares=[revalidate])
    app.cleanup_ctx.append(watch_bank)
    app.router.add_get("/", index)
    app.router.add_get("/api/meta", meta)
    app.router.add_get("/api/questions", questions)
    app.router.add_get("/api/search", search)
    app.router.add_get(r"/api/question/{qid}", question)
    app.router.add_post("/api/find", find)
    app.router.add_get("/api/sets", set_list)
    app.router.add_post("/api/sets", set_create)
    app.router.add_post("/api/sets/import", set_import)
    app.router.add_get(r"/api/sets/{sid}", set_get)
    app.router.add_patch(r"/api/sets/{sid}", set_patch)
    app.router.add_delete(r"/api/sets/{sid}", set_delete)
    app.router.add_get(r"/api/sets/{sid}/export", set_export)
    app.router.add_get(r"/api/sets/{sid}/paper", paper_info)
    app.router.add_get(r"/api/sets/{sid}/paper/{n:\d+}.png", paper_page)
    app.router.add_get(r"/doc/{sid}/{kind}", reading)
    app.router.add_post(r"/api/sets/{sid}/zip/preview", zip_preview)
    app.router.add_post(r"/api/sets/{sid}/output", output)
    app.router.add_post(r"/api/sets/{sid}/board", board_open)
    app.router.add_get(r"/api/sets/{sid}/boards", board_list)
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
    app.router.add_get(r"/api/settings/preview/{bits}", settings_preview)
    app.router.add_get(r"/api/settings/preview/{bits}/{n:\d+}.png", settings_preview_page)
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


def _app(port):
    app = make_app()
    advertise(app, port=port, source="qb-manage", path="/ipad")   # the iPad shell opens /ipad (@qb-manage; app/ is @qb)
    return app


def run(port=8910, host="0.0.0.0"):
    print(f"数据管理页 {__version__}: http://localhost:{port}/(在电脑的浏览器中打开;iPad 只用白板外壳,来源填 @qb-manage)\n"
          f"题组: {paths.SETS}\n按 Ctrl-C 停止")
    web.run_app(_app(port), host=host, port=port, print=None)


def start(port=8910, host="0.0.0.0"):
    """The same server on a thread of its own, for the window (manage.py window). Returns
    stop(), which closes it as Ctrl-C would; an automatic run in progress finishes first."""
    loop = asyncio.new_event_loop()
    runner = web.AppRunner(_app(port))
    loop.run_until_complete(runner.setup())
    loop.run_until_complete(web.TCPSite(runner, host, port).start())
    threading.Thread(target=loop.run_forever, daemon=True).start()

    def stop():
        asyncio.run_coroutine_threadsafe(runner.cleanup(), loop).result(30)
        loop.call_soon_threadsafe(loop.stop)
    return stop
