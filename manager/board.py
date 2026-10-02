"""Writing boards for question papers (docs/data-manager.md, F5).

A board (stored in paths.BOARDS) is white-board's document board: the pages of a question paper laid out top
to bottom (manager/whiteboard/docs.py), ink stored as vectors by inksync and synced
between the Mac and the iPad. One board per version of a set's question paper: its
id is the paper's cache name (<set id>-<key>, manager/paper.py), and the paper is
copied next to the board when the board is made, so later changes to the set leave
the board and its pages as they were.

The Mac opens a board; the iPad page (/ipad, which the iPad shell opens) follows it:
it shows whichever board the Mac opened last and switches when the Mac opens another.

Exported ink is appended to that copy (docs.export_pdf); the latest export of a set
is kept as paths.WORK/answers/<set id>.pdf, which the ZIP export picks up (F7).
"""
import asyncio
import io
import json
import os
import shutil
import time
import zipfile

import pymupdf

from lib import paths
from manager import bank, docs as reading, export, paper
from manager.whiteboard import docs

ROOT = paths.BOARDS
PDFS = os.path.join(ROOT, "papers")


CURRENT = os.path.join(ROOT, "current.json")


def current():
    """The board the Mac opened last: the one the iPad page (/ipad) shows."""
    try:
        with open(CURRENT, encoding="utf-8") as f:
            bid = json.load(f).get("board")
    except (OSError, ValueError):
        return None
    return bid if bid and os.path.isfile(pdf_of(bid)) else None


async def hello(conn, msg):
    """inksync's hello for a page that follows (the iPad page): the current board."""
    conn.ext["follow"] = True
    return current()


async def follow(hub, bid):
    """Make `bid` the current board and move every following page (the iPad) to it."""
    os.makedirs(ROOT, exist_ok=True)
    with open(CURRENT + ".tmp", "w", encoding="utf-8") as f:
        json.dump({"board": bid}, f)
    os.replace(CURRENT + ".tmp", CURRENT)
    for c in hub.connections():
        if c.ext.get("follow") and c.board != bid:
            await hub.open(c, bid, "switch")


def pdf_of(bid):
    return os.path.join(PDFS, bid + ".pdf")


def _labels(s, path):
    """For each page of the paper, the questions on it: ["9709/12/M/J/23 Q5", ...]."""
    rows = paper._rows(s["items"])
    opts = paper.settings.load()

    def label(pairs):                     # [(code, q)] -> "9709/12/M/J/23 Q5 Q6"
        by = {}
        for code, q in pairs:
            by.setdefault(code, []).append(f"Q{q}")
        return " ".join(f"{c} {' '.join(dict.fromkeys(qs))}" for c, qs in by.items())
    if paper.original_pdf(rows, opts):
        by = {}
        for r in rows:
            for n in json.loads(r["qp_pages"] or "[]"):
                by.setdefault(n - 1, []).append((bank.paper_code(r), r["q"]))
        return [label(by.get(i, [])) for i in range(paper.page_count(path))]
    return [label([(it[3], it[4]) for it in items]) for items in paper.layout(rows, opts)]


async def open_for(hub, s):
    """The board for the set's current question paper, made if it does not exist."""
    loop = asyncio.get_running_loop()
    path = await loop.run_in_executor(None, paper.build, s)
    bid = os.path.basename(path)[:-4]
    if hub.board_meta(bid):
        return bid
    os.makedirs(PDFS, exist_ok=True)
    shutil.copyfile(path, pdf_of(bid))
    pages = docs.probe(pdf_of(bid))
    labels = await loop.run_in_executor(None, _labels, s, path)
    await hub.create_board(bid, {
        "name": s["name"][:64],
        "canvas": docs.canvas(pages),
        "background": {"pattern": "blank"},
        "layers": docs.layers(pages, f"/api/boards/{bid}/page/{{n}}?w={{w}}"),
        "data": {"set": s["id"], "labels": labels if len(labels) == len(pages) else [],
                 "doc": {"type": "pdf", "name": s["name"][:64] + ".pdf", "ext": ".pdf", "pages": pages}},
    })
    return bid


def boards_of(hub, sid):
    """The set's boards, newest first: [{id, updated, pages}]."""
    out = []
    for m in hub.list_boards(prefix=sid + "-", limit=None, order="updated"):
        if os.path.isfile(pdf_of(m["id"])):
            out.append({"id": m["id"], "pages": len(((m.get("data") or {}).get("doc") or {}).get("pages") or []),
                        "updated": time.strftime("%Y-%m-%d %H:%M", time.localtime(m["updated"]))})
    return out


async def boards_with_ink(hub, sid):
    """boards_of with the number of strokes on each, so the set page can tell written from blank."""
    out = boards_of(hub, sid)
    for b in out:
        b["strokes"] = len(await hub.strokes(b["id"]) or [])
    return out


async def refresh_answers(hub, s):
    """Write the set's annotated copy from its newest board that has ink, so an export
    always carries the ink as it is now. Does nothing when no board has ink."""
    out = os.path.join(export.ANSWERS, s["id"] + ".pdf")
    for b in boards_of(hub, s["id"]):
        strokes = await hub.strokes(b["id"])
        if strokes:
            meta = hub.board_meta(b["id"]) or {}
            if os.path.isfile(out) and os.path.getmtime(out) >= meta.get("updated", 0):
                return out                           # written after the last stroke: still current
            os.makedirs(export.ANSWERS, exist_ok=True)
            tmp = out + ".tmp.pdf"
            await asyncio.get_running_loop().run_in_executor(None, docs.export_pdf, pdf_of(b["id"]), strokes, tmp)
            os.replace(tmp, out)
            return out
    return None


def page_png(bid, n, width):
    width = max(160, min(2400, int(width)))
    with pymupdf.open(pdf_of(bid)) as d:
        page = d[n]
        zoom = width / page.rect.width
        return page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), colorspace=pymupdf.csGRAY).tobytes("png")


def answers_info(s):
    p = export.answer_pdf(s)
    if not p:
        return None
    with pymupdf.open(p) as d:
        n = d.page_count
    return {"updated": time.strftime("%Y-%m-%d %H:%M", time.localtime(os.path.getmtime(p))), "pages": n}


async def export_board(hub, s, bid, name, scheme=False, explanation=False):
    """(bytes, file name): the paper with the ink as a PDF, or a ZIP with the reading
    documents when they are asked for. The PDF also becomes the set's answer PDF."""
    strokes = await hub.strokes(bid)
    if strokes is None:
        raise KeyError(bid)
    os.makedirs(export.ANSWERS, exist_ok=True)
    out = os.path.join(export.ANSWERS, s["id"] + ".pdf")
    tmp = out + ".tmp.pdf"
    await asyncio.get_running_loop().run_in_executor(None, docs.export_pdf, pdf_of(bid), strokes, tmp)
    os.replace(tmp, out)
    with open(out, "rb") as f:
        pdf = f.read()
    if not (scheme or explanation):
        return pdf, name + ".pdf"
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr(zipfile.ZipInfo(name + ".pdf", export.STAMP), pdf)
        if scheme:
            z.writestr(zipfile.ZipInfo(f"{name} 评分细则.html", export.STAMP), reading.scheme(s).encode(),
                       compress_type=zipfile.ZIP_DEFLATED)
        if explanation:
            z.writestr(zipfile.ZipInfo(f"{name} 详解.html", export.STAMP), reading.explanation(s).encode(),
                       compress_type=zipfile.ZIP_DEFLATED)
    return buf.getvalue(), name + ".zip"
