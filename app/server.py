"""The practice server: the page, the questions, the attempts and the handwriting.

    python3 qb.py serve [--port 8900]

Everything the page needs comes from this one server, as inksync requires
(docs/external/inksync-2.0-interface.zh-CN.md, 4.5 and section 2):

  /                      the page (app/web/)
  /vendor/               KaTeX (assets/vendor/)
  /q/<imgNNNN>/<file>    question crops, from data/ (paths.resolve), and the
                         answer-space crops in imgNNNN_ans/ the board is laid over
  /api/filters           subjects, papers, topics and years for the filters
  /api/questions         the question list, with each question's last attempt
  /api/question/<id>     one question: text, image, parts and what to tick,
                         scheme, worked explanation, attempts
  /api/attempt           POST {qid, new: true} starts an attempt on a new board;
                         POST {id, marks, score, max, seconds} records its marking
  /api/review            lost marks item by item, and the marked attempts
  /ws, /inksync/         inksync: the boards' sync and the pad's script

inksync 2.0 is not released yet. Until it is installed the server serves a
stand-in pad with the same interface at /inksync/inkpad.js (app/web/inksync-
stub/), which keeps the boards in the browser only; the page does not change
when 2.0 arrives. The boards and attempts live in paths.WORK, outside data/.
"""
import json
import os
import re
import struct

from aiohttp import web

from lib import db, paths
from app import marking, store

WEB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")
IMG_DIRS = ("img9709", "img9231", "img9618", "img_adm", "img_tara",
            "img9709" + paths.ANS_SUFFIX, "img9231" + paths.ANS_SUFFIX, "img9618" + paths.ANS_SUFFIX)
BOARD_WIDTH = 800          # board units the question image spans
EXAMS = {"9709": "Mathematics", "9231": "Further Mathematics", "9618": "Computer Science",
         "TMUA": "TMUA", "TSA": "TSA", "BMAT": "BMAT"}
# Minutes allowed for each paper, from the syllabuses (CAIE 2020-on; admissions
# tests as last set). The page divides them by the paper's marks to give each
# question a time budget.
MINUTES = {
    "9709": {"1": 110, "2": 75, "3": 110, "4": 75, "5": 75, "6": 75},
    "9231": {"1": 120, "2": 120, "3": 90, "4": 90},
    "9618": {"1": 90, "2": 120, "3": 90, "4": 150},
    "TMUA": {"1": 75, "2": 75},
    "TSA": {"1": 90},
    "BMAT": {"1": 60},
}


def png_size(path):
    with open(path, "rb") as f:
        head = f.read(24)
    if head[:8] == b"\x89PNG\r\n\x1a\n":
        return struct.unpack(">II", head[16:24])
    return None


# ------------------------------------------------------------------ routes

async def filters(request):
    con = db.connect()
    rows = con.execute(
        "SELECT syllabus, component, component_name, year, topic, topic_name, COUNT(*) AS n "
        "FROM questions GROUP BY syllabus, component, year, topic").fetchall()
    out = {}
    for r in rows:
        s = out.setdefault(r["syllabus"], {"name": EXAMS.get(r["syllabus"], r["syllabus"]),
                                           "components": {}, "years": set(), "topics": {},
                                           "minutes": MINUTES.get(r["syllabus"], {})})
        s["components"][r["component"]] = r["component_name"]
        s["years"].add(r["year"])
        if r["topic"]:
            s["topics"][r["topic"]] = r["topic_name"]
    for s in out.values():
        s["years"] = sorted(y for y in s["years"] if y)
    return web.json_response(out)


async def questions(request):
    q = request.query
    where, args = ["syllabus = ?"], [q.get("syllabus", "9709")]
    for key, col in (("component", "component"), ("year", "year"), ("topic", "topic")):
        if q.get(key):
            where.append(f"{col} = ?")
            args.append(q[key])
    if q.get("text"):
        where.append("id IN (SELECT id FROM q_fts WHERE q_fts MATCH ?)")
        args.append(q["text"])
    con = db.connect()
    try:
        rows = con.execute(
            "SELECT id, paper, series, component, variant, session, year, q, marks, topic, "
            "topic_name, q_quality "
            f"FROM questions WHERE {' AND '.join(where)} ORDER BY year DESC, series, paper, q",
            args).fetchall()
    except Exception:                          # a search the full-text index cannot parse
        rows = []
    done = store.summary(store.connect())
    status = q.get("status")
    out = []
    for r in rows:
        d = dict(r)
        d["attempt"] = done.get(r["id"])
        if status == "new" and d["attempt"]:
            continue
        if status == "done" and not d["attempt"]:
            continue
        if status == "wrong" and not (d["attempt"] and d["attempt"]["score"] is not None
                                      and d["attempt"]["score"] < (d["attempt"]["max"] or 0)):
            continue
        out.append(d)
    return web.json_response(out)


def image_info(path, image_prefix):
    size = png_size(path) if path and path.endswith(".png") else None
    rel = paths.relative_to_data(path) if path else None
    return {"src": image_prefix + rel, "width": size[0], "height": size[1]} if size and rel else None


def detail(r, attempts, current, image_prefix="/q/"):
    """The page's view of one question row: text, image, parts and what to
    tick, scheme, explanation and attempts (also used by app/preview.py).

    image is the question crop; board_image the crop with the answer rows
    below every part, when the question crop leaves them out. A new board is
    laid over board_image, so each part has its answer space where the paper
    has it."""
    img = paths.resolve(r["image"])
    return {
        "id": r["id"], "syllabus": r["syllabus"], "paper": r["paper"], "session": r["session"],
        "q": r["q"], "marks": r["marks"], "topic": r["topic"], "topic_name": r["topic_name"],
        "text": r["question_latex"] or r["question_text"], "q_quality": r["q_quality"],
        "image": image_info(img, image_prefix),
        "board_image": image_info(paths.answer_space(r["image"]), image_prefix),
        "board_width": BOARD_WIDTH,
        "parts": marking.parts(r),
        "scheme": r["ms_latex"] or r["ms_text"],
        "explanation": json.loads(r["explanation"]) if "explanation" in r.keys()
        and r["explanation"] else None,
        "attempts": attempts,
        "current": current,
    }


async def question(request):
    qid = request.match_info["qid"]
    con = db.connect()
    r = con.execute("SELECT * FROM questions WHERE id = ?", (qid,)).fetchone()
    if not r:
        raise web.HTTPNotFound()
    st = store.connect()
    return web.json_response(detail(r, store.for_question(st, qid), store.current(st, qid)))


async def attempt(request):
    body = await request.json()
    st = store.connect()
    if body.get("new"):
        if not store.for_question(st, body["qid"]):
            store.start(st, body["qid"])       # the first board was in use unsaved
        return web.json_response(store.start(st, body["qid"]))
    aid = body.get("id")
    return web.json_response(store.mark(st, int(aid) if aid else None, body.get("marks"),
                                        body.get("score"), body.get("max"), body.get("note"),
                                        qid=body.get("qid"), seconds=body.get("seconds")))


async def review(request):
    """Lost marks of the latest marked attempt at each question of one exam,
    item by item, and the marked attempts newest first."""
    syl = request.query.get("syllabus", "9709")
    st = store.connect()
    con = db.connect()
    rows = {}

    def question_row(qid):
        if qid not in rows:
            rows[qid] = con.execute("SELECT * FROM questions WHERE id = ?", (qid,)).fetchone()
        return rows[qid]

    lost, history = [], []
    for a in store.latest_marked(st):
        r = question_row(a["qid"])
        if not r or r["syllabus"] != syl:
            continue
        items = marking.lost(marking.parts(r), a["marks"])
        if items:
            lost.append({"qid": a["qid"], "n": a["n"], "marked": a["marked"],
                         "score": a["score"], "max": a["max"], "items": items})
    for a in store.history(st):
        r = question_row(a["qid"])
        if r and r["syllabus"] == syl:
            history.append({k: a[k] for k in ("qid", "n", "marked", "score", "max", "seconds")})
    return web.json_response({"lost": lost, "history": history})


async def image(request):
    rel = request.match_info["path"]
    if not rel.split("/")[0] in IMG_DIRS or ".." in rel:
        raise web.HTTPNotFound()
    path = paths.resolve(rel)
    if not path:
        raise web.HTTPNotFound()
    return web.FileResponse(path, headers={"Cache-Control": "max-age=86400"})


async def index(request):
    return web.FileResponse(os.path.join(WEB, "index.html"),
                            headers={"Cache-Control": "no-cache"})


# ------------------------------------------------------------------ inksync

def setup_ink(app, port):
    """inksync 2.0 when installed; otherwise the stand-in pad (browser only)."""
    try:
        import inksync
        v2 = hasattr(inksync, "serve_sdk")
    except ImportError:
        inksync, v2 = None, False
    if v2:
        from inksync import DefaultPolicy, FileStorage, Hub, mount, serve_sdk
        os.makedirs(paths.INK, exist_ok=True)
        # one user: every device on the network may open and write the boards
        hub = Hub(FileStorage(paths.INK), policy=DefaultPolicy())
        mount(app, hub, path="/ws")
        serve_sdk(app, prefix="/inksync/")
        mode = f"inksync {inksync.__version__}(同步,存储 {paths.INK})"
    else:
        stub = os.path.join(WEB, "inksync-stub")
        os.makedirs(stub, exist_ok=True)
        app.router.add_static("/inksync/", stub)
        mode = "替身手写板(inksync 2.0 未安装:笔迹只存在各自浏览器中)"
    try:
        from inksync.netinfo import advertise
        advertise(app, port=port, source="qb", path="/")
        mode += ";已注册 Bonjour 服务 qb(iPad 外壳「来源」填 @qb)"
    except Exception:
        pass
    return mode


def make_app(port=8900):
    app = web.Application()
    app.router.add_get("/", index)
    app.router.add_get("/api/filters", filters)
    app.router.add_get("/api/questions", questions)
    app.router.add_get(r"/api/question/{qid}", question)
    app.router.add_post("/api/attempt", attempt)
    app.router.add_get("/api/review", review)
    app.router.add_get(r"/q/{path:.+}", image)
    app.router.add_static("/static/", WEB)
    app.router.add_static("/vendor/", os.path.join(paths.ASSETS, "vendor"))
    app["ink_mode"] = setup_ink(app, port)
    return app


def run(port=8900):
    app = make_app(port)
    print(f"刷题页: http://localhost:{port}/\n手写板: {app['ink_mode']}\n"
          f"记录: {paths.WORK}\n按 Ctrl-C 停止")
    web.run_app(app, port=port, print=None)
