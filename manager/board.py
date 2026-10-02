"""Writing boards for question papers (docs/data-manager.md, F5).

A board (stored in paths.BOARDS) is white-board's document board: the pages of a question paper laid out top
to bottom (manager/whiteboard/docs.py), ink stored as vectors by inksync and synced
between the Mac and the iPad. One board per version of a set's question paper: its
id is the paper's cache name (<set id>-<key>, manager/paper.py), and the paper is
copied next to the board when the board is made, so later changes to the set leave
the board and its pages as they were.

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


def pdf_of(bid):
    return os.path.join(PDFS, bid + ".pdf")


def _labels(s, path):
    """For each page of the paper, the questions on it: ["9709/12/M/J/23 Q5", ...]."""
    rows = paper._rows(s["items"])
    if paper.whole_paper(rows) and path.endswith(".pdf"):
        by = {}
        for r in rows:
            for n in json.loads(r["qp_pages"] or "[]"):
                by.setdefault(n - 1, []).append(f"{bank.paper_code(r)} Q{r['q']}")
        return [" ".join(by.get(i, [])) for i in range(paper.page_count(path))]
    out = []
    for items in paper.layout(rows, paper.settings.load()):
        codes = list(dict.fromkeys(it[3] for it in items))
        qs = " ".join(dict.fromkeys(f"Q{it[4]}" for it in items))
        out.append(f"{' '.join(codes)} {qs}".strip())
    return out


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
