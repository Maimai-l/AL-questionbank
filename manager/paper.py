"""Question papers (docs/data-manager.md, F4 and section 6): a set laid out on A4 as a PDF.

- A set that is exactly one whole paper, in order, is the original PDF from data/papers/.
- A CIE question starts a new page; a crop taller than a page is cut at the whitest row
  near the page bottom and continues on the next page.
- Admissions questions go two to a page, half a page each (the space below the
  question is for working), or one after another ("flow"), per the settings.
- The footer holds the set name, paper code and question numbers, and page number,
  each switchable in the settings.
The result is cached in paths.WORK/papers/ under a hash of the set and the settings.
"""
import hashlib
import io
import json
import os
import re

import numpy as np
import pymupdf
from PIL import Image

from lib import db, paths
from manager import bank, settings

A4 = (595.0, 842.0)
SIDE, TOP, BOTTOM = 40.0, 40.0, 52.0
GAP = 14.0
CACHE = os.path.join(paths.WORK, "papers")
FONT = "china-s"
LATIN = "helv"
CJK = re.compile(r"([\u2e80-\u9fff\u3000-\u303f\uff00-\uffef]+)")


def _runs(text):
    """(text, font) runs: Chinese in the CJK font, everything else in Helvetica."""
    return [(t, FONT if i % 2 else LATIN) for i, t in enumerate(CJK.split(text)) if t]


def _width(text, size):
    return sum(pymupdf.Font(f).text_length(t, fontsize=size) for t, f in _runs(text))


def _text(page, x, y, text, size, color):
    for t, f in _runs(text):
        page.insert_text((x, y), t, fontname=f, fontsize=size, color=color)
        x += pymupdf.Font(f).text_length(t, fontsize=size)


def _rows(ids):
    con = db.connect()
    by = {}
    for i in range(0, len(ids), 500):
        chunk = ids[i:i + 500]
        for r in con.execute(f"SELECT * FROM questions WHERE id IN ({','.join('?' * len(chunk))})", chunk):
            by[r["id"]] = r
    return [by[q] for q in ids if q in by]


def whole_paper(rows):
    """The original PDF when the rows are exactly one paper's questions in order."""
    if not rows or len({(r["paper"], r["series"]) for r in rows}) != 1:
        return None
    r0 = rows[0]
    con = db.connect()
    all_q = [x[0] for x in con.execute("SELECT id FROM questions WHERE paper = ? AND series = ? ORDER BY q",
                                       (r0["paper"], r0["series"]))]
    if all_q != [r["id"] for r in rows]:
        return None
    return bank.paper_pdf(r0)


def _cut_row(gray, start, end):
    """Row in [start, end) to cut at: the lowest of the whitest rows."""
    if end <= start:
        return end
    band = gray[start:end]
    mean = band.mean(axis=1)
    white = np.where(mean >= mean.max() - 0.5)[0]
    return start + int(white[-1]) + 1


def _slices(path, width_pt, first_room, room):
    """Cut a crop into pieces that fit: [(png bytes, height in points)]."""
    im = Image.open(path)
    gray = np.asarray(im.convert("L"), dtype=np.float32)
    h, w = gray.shape
    scale = width_pt / w
    out, top, fit = [], 0, first_room
    while top < h:
        limit = int(fit / scale)
        if h - top <= limit:
            end = h
        else:
            end = _cut_row(gray, top + int(limit * 0.75), top + limit)
        piece = im.crop((0, top, w, end))
        buf = io.BytesIO()
        piece.save(buf, "PNG", optimize=True)
        out.append((buf.getvalue(), (end - top) * scale))
        top, fit = end, room
    return out


def layout(rows, opts):
    """Pages as lists of (png, height, qid, code, q)."""
    width = A4[0] - 2 * SIDE
    room = A4[1] - TOP - BOTTOM
    pages, cur, used, kind = [], None, 0.0, None

    def new_page(k):
        nonlocal cur, used, kind
        cur, used, kind = [], 0.0, k
        pages.append(cur)

    half = (room - GAP) / 2
    for r in rows:
        code = bank.paper_code(r)
        cie = r["syllabus"] in bank.CIE
        crop = paths.answer_space(r["image"]) if cie and opts["cie_space"] else None
        crop = crop or paths.resolve(r["image"])
        if not crop:
            continue
        if cie:
            new_page("cie")
            for i, (png, hpt) in enumerate(_slices(crop, width, room, room)):
                if i:
                    new_page("cie")
                cur.append((png, hpt, r["id"], code, r["q"]))
                used += hpt
            continue
        pieces = _slices(crop, width, room, room)
        if opts["adm_layout"] == "two":
            png, hpt = pieces[0][0], min(pieces[0][1], half)
            if kind != "two" or len(cur) >= 2:
                new_page("two")
            cur.append((png, hpt, r["id"], code, r["q"], half))
            used += half + GAP
        else:
            hpt = pieces[0][1]
            if kind != "flow" or used + hpt > room:
                new_page("flow")
            cur.append((pieces[0][0], min(hpt, room), r["id"], code, r["q"]))
            used += min(hpt, room) + GAP
    return pages


def _footer(page, n, total, name, items, opts):
    y = A4[1] - 28
    size = 8
    color = (0.35, 0.35, 0.35)
    page.draw_line((SIDE, y - 12), (A4[0] - SIDE, y - 12), color=(0.82, 0.82, 0.82), width=0.6)
    if opts["footer_name"]:
        _text(page, SIDE, y, name, size, color)
    right = []
    if opts["footer_code"] and items:
        codes = list(dict.fromkeys(i[3] for i in items))
        qs = "、".join(dict.fromkeys(f"Q{i[4]}" for i in items))
        right.append(f"{'、'.join(codes)} {qs}" if len(codes) == 1 else "、".join(f"{i[3]} Q{i[4]}" for i in items))
    if opts["footer_page"]:
        right.append(f"{n} / {total}")
    text = "    ".join(right)
    if text:
        _text(page, A4[0] - SIDE - _width(text, size), y, text, size, color)


def build(s):
    """Path of the set's question paper PDF, building it if the cache is stale."""
    opts = settings.load()
    rows = _rows(s["items"])

    def stamp(r):                        # rebuilt when a crop is redone
        out = []
        for p in (paths.resolve(r["image"]), paths.answer_space(r["image"])):
            out.append(int(os.path.getmtime(p)) if p else 0)
        return out
    key = hashlib.sha1(json.dumps([s["name"], s["items"], {k: opts[k] for k in opts if k != "theme"},
                                   [stamp(r) for r in rows]], ensure_ascii=False).encode()).hexdigest()[:12]
    os.makedirs(CACHE, exist_ok=True)
    out = os.path.join(CACHE, f'{s["id"]}-{key}.pdf')
    if os.path.exists(out):
        return out
    for f in os.listdir(CACHE):
        if f.startswith(s["id"] + "-"):
            os.remove(os.path.join(CACHE, f))
    original = whole_paper(rows)
    if original:
        doc = pymupdf.open(original)
    else:
        doc = pymupdf.open()
        pages = layout(rows, opts)
        for n, items in enumerate(pages, 1):
            page = doc.new_page(width=A4[0], height=A4[1])
            y = TOP
            for it in items:
                png, hpt = it[0], it[1]
                width = A4[0] - 2 * SIDE
                page.insert_image(pymupdf.Rect(SIDE, y, SIDE + width, y + hpt), stream=png)
                y += (it[5] if len(it) > 5 else hpt) + GAP
            _footer(page, n, len(pages), s["name"], items, opts)
    doc.save(out, garbage=3, deflate=True)
    return out


def page_count(path):
    with pymupdf.open(path) as d:
        return d.page_count


def page_png(path, n, width=800):
    with pymupdf.open(path) as d:
        page = d[n]
        zoom = width / page.rect.width
        return page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), colorspace=pymupdf.csGRAY).tobytes("png")
