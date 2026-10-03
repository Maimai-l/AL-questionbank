"""Practice papers (docs/data-manager.md, F4; layout in docs/ui-text.md 4.8): a set laid
out on A4 as a PDF, one layout for every exam.

- A set that is exactly one whole paper, in order, is the original PDF from data/papers/
  (unless the paper needs answer lines, below).
- Questions run on from top to bottom in the set's order, 24 pt apart. A question that
  does not fit in the rest of the page starts the next page; only a question taller than
  a whole page is cut, at the whitest row near the page bottom, and continues overleaf.
- CIE questions use the crop with the paper's answer space. Papers answered in a separate
  answer booklet (9709 June 2026 papers 12 and 32) have none: ruled lines are added
  8 pt below the question, two per mark, 24 pt apart.
- Admissions questions use the question crop, spaced the same way.
- The footer holds the set name, paper code and question numbers, and page number,
  each switchable in the settings; 8 pt, its baseline 24 pt above the paper's edge.
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
SIDE, TOP, BOTTOM = 40.0, 40.0, 56.0
GAP = 24.0                               # between questions
LINES_GAP = 8.0                          # between a question and its added answer lines
LINE = 24.0                              # ruled answer lines
FOOT = 24.0                              # footer baseline above the paper's lower edge
CACHE = os.path.join(paths.WORK, "papers")
VERSION = 3                              # part of the cache key: raise when the layout changes
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


_booklet = {}


def booklet(r):
    """True when the paper is answered in a separate answer booklet (no answer space)."""
    name = r["qp_pdf"]
    if name not in _booklet:
        p = bank.paper_pdf(r)
        with pymupdf.open(p) if p else pymupdf.open() as d:
            _booklet[name] = bool(p) and "answer booklet" in d[0].get_text().lower()
    return _booklet[name]


def original_pdf(rows):
    """The original PDF when the paper is used as it is: a whole paper, unless it needs
    answer lines (answered in a booklet)."""
    original = whole_paper(rows)
    if original and booklet(rows[0]):
        return None                      # laid out again, to add the answer lines
    return original


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


def layout(rows):
    """Pages as lists of (png or None for answer lines, y, height, qid, code, q)."""
    width = A4[0] - 2 * SIDE
    room = A4[1] - TOP - BOTTOM
    pages = [[]]
    y = TOP                                  # where the next block goes on the last page

    def new_page():
        nonlocal y
        pages.append([])
        y = TOP

    for r in rows:
        code = bank.paper_code(r)
        cie = r["syllabus"] in bank.CIE
        crop = (paths.answer_space(r["image"]) if cie else None) or paths.resolve(r["image"])
        if not crop:
            continue
        pieces = _slices(crop, width, room, room)
        lines = 2 * (r["marks"] or 2) * LINE if cie and booklet(r) else 0
        height = pieces[0][1] if len(pieces) == 1 else room + 1
        if pages[-1]:
            y += GAP
            need = height + (LINES_GAP + lines if lines else 0)
            if need > room:                  # too tall to keep together: at least three lines with it
                need = height + (LINES_GAP + 3 * LINE if lines else 0)
            if y + need > TOP + room:        # starts the next page rather than being cut
                new_page()
        for i, (png, hpt) in enumerate(pieces):
            if i:
                new_page()
            pages[-1].append((png, y, hpt, r["id"], code, r["q"]))
            y += hpt
        if lines:
            y += LINES_GAP
            while lines >= LINE:
                band = min(lines, (TOP + room - y) // LINE * LINE)
                if band < LINE:
                    new_page()
                    continue
                pages[-1].append((None, y, band, r["id"], code, r["q"]))
                y += band
                lines -= band
    return [p for p in pages if p]


def _lines(page, y, h):
    """Dotted answer lines filling a band of height h from y."""
    x0, x1 = SIDE + 28, A4[0] - SIDE
    for k in range(1, int(h // LINE) + 1):
        yy = y + k * LINE
        page.draw_line((x0, yy), (x1, yy), color=(0.55, 0.55, 0.55), width=0.5, dashes="[1 2] 0")


def _footer(page, n, total, name, items, opts):
    y = A4[1] - FOOT
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


class EmptyPaper(ValueError):
    """The set has no question that can be laid out (no questions, or none with a crop)."""


def build(s):
    """Path of the set's question paper PDF, building it if the cache is stale. Raises
    EmptyPaper when there is nothing to lay out."""
    opts = settings.load()
    rows = _rows(s["items"])

    def stamp(r):                        # rebuilt when a crop is redone
        out = []
        for p in (paths.resolve(r["image"]), paths.answer_space(r["image"])):
            out.append(int(os.path.getmtime(p)) if p else 0)
        return out
    key = hashlib.sha1(json.dumps([VERSION, s["name"], s["items"], {k: opts[k] for k in opts if k != "theme"},
                                   [stamp(r) for r in rows]], ensure_ascii=False).encode()).hexdigest()[:12]
    os.makedirs(CACHE, exist_ok=True)
    out = os.path.join(CACHE, f'{s["id"]}-{key}.pdf')
    if os.path.exists(out):
        return out
    for f in os.listdir(CACHE):
        if f.startswith(s["id"] + "-") and f.endswith(".pdf"):
            try:
                os.remove(os.path.join(CACHE, f))
            except OSError:
                pass
    original = original_pdf(rows)
    if original:
        doc = pymupdf.open(original)
    else:
        doc = pymupdf.open()
        pages = layout(rows)
        if not pages:
            raise EmptyPaper("题组中没有可排版的题目")
        width = A4[0] - 2 * SIDE
        for n, items in enumerate(pages, 1):
            page = doc.new_page(width=A4[0], height=A4[1])
            for png, y, hpt, *_ in items:
                if png is None:
                    _lines(page, y, hpt)
                else:
                    page.insert_image(pymupdf.Rect(SIDE, y, SIDE + width, y + hpt), stream=png)
            _footer(page, n, len(pages), s["name"], [(None, None) + tuple(it[3:]) for it in items], opts)
    tmp = f"{out}.{os.getpid()}.tmp"       # written whole, then put in place: never a half-written PDF
    doc.save(tmp, garbage=3, deflate=True)
    os.replace(tmp, out)
    return out


def page_count(path):
    with pymupdf.open(path) as d:
        return d.page_count


def page_png(path, n, width=800):
    with pymupdf.open(path) as d:
        page = d[n]
        zoom = width / page.rect.width
        return page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), colorspace=pymupdf.csGRAY).tobytes("png")
