"""Practice papers (docs/data-manager.md, F4; layout in docs/ui-text.md 4.8): a set laid
out on A4 as a PDF, one layout for every exam, its answer space set by 版面 (SPACE).

- 版面 runs from 紧凑 (0) to 原卷 (3): the questions alone; a quarter, a half or all of
  the original paper's answer space below each. The settings page holds the default; an
  export may choose another.
- At the original amount, a set that is exactly one whole paper, in order, is the
  original PDF from data/papers/ (unless the paper needs answer lines, below).
- Questions run on from top to bottom in the set's order, 24 pt apart (12 pt with no
  answer space). A question that does not fit in the rest of the page starts the next
  page; only a question taller than a whole page is cut: in its answer space where it
  can be, else at the whitest row near the page bottom; it continues overleaf.
- CIE questions use the crop with the paper's answer space; the space is the rows the
  question crop leaves out and the dotted lines between parts, found in the picture.
- Papers answered in a separate answer booklet (9709 June 2026 papers 12 and 32) have none: ruled lines are added
  8 pt below the question, two per mark at the original amount, 24 pt apart.
- Admissions questions, answered by a letter, get blank space to work in instead.
- The footer holds the set name, paper code and question numbers, and page number,
  each switchable in the settings; 8 pt, its baseline 24 pt above the paper's edge.
The result is cached in paths.WORK/papers/ under a hash of the set, the settings and 版面.
"""
import hashlib
import json
import os
import re
import threading
import zlib

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
VERSION = 10                             # part of the cache key: raise when the layout changes
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


_booklet = None
BOOKLET = os.path.join(CACHE, "booklet.json")   # {question paper PDF: answered in a booklet}


def booklet(r):
    """True when the paper is answered in a separate answer booklet (no answer space). Read
    from the paper's first page once, then kept in BOOKLET."""
    global _booklet
    if _booklet is None:
        try:
            with open(BOOKLET, encoding="utf-8") as f:
                _booklet = json.load(f)
        except (OSError, ValueError):
            _booklet = {}
    name = r["qp_pdf"]
    if name not in _booklet:
        p = bank.paper_pdf(r)
        if not p:
            return False                     # not kept: the PDF may be added later
        with pymupdf.open(p) as d:
            _booklet[name] = "answer booklet" in d[0].get_text().lower()
        os.makedirs(CACHE, exist_ok=True)
        with open(BOOKLET + ".tmp", "w", encoding="utf-8") as f:
            json.dump(_booklet, f)
        os.replace(BOOKLET + ".tmp", BOOKLET)
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
    band = gray[start:end].astype(np.float32)
    mean = band.mean(axis=1)
    white = np.where(mean >= mean.max() - 0.5)[0]
    return start + int(white[-1]) + 1


# The answer space a question gets, from 紧凑 (0) to 原卷 (3): the share of the original
# paper's answer space kept below the question.
SPACE = [0, 1 / 4, 1 / 2, 1]
SPACE_DEFAULT = 3
GAP_TIGHT = 12.0                         # between questions with no answer space
LINES, BLANK = "lines", "blank"          # answer space in a page's items: ruled, or left blank


def _grey(path):
    return np.asarray(Image.open(path).convert("L"))


def _slices(pixels, width_pt, first_room, room, free=None):
    """Cut rows into pieces that fit: [(grey rows, height in points)]. free marks the rows
    of answer space: a cut falls there when the stretch where it may fall has any, so a
    question's text is cut only when there is no answer space to cut instead."""
    h, w = pixels.shape
    scale = width_pt / w
    out, top, fit = [], 0, first_room
    while top < h:
        limit = int(fit / scale)
        if h - top <= limit:
            end = h
        else:
            lo, hi = top + int(limit * 0.5), top + limit
            spare = np.flatnonzero(free[lo:hi]) if free is not None else []
            if len(spare):                   # the lowest row of answer space in reach
                end = lo + int(spare[-1]) + 1
                run = end - 1                # its stretch of space: where it starts
                while run > top and free[run - 1]:
                    run -= 1
                # a part's text with less than three lines of space under it at the page
                # bottom: cut above that text instead, at the end of the space before it
                if (end - run) * scale < 3 * LINE:
                    before = np.flatnonzero(free[lo:run])
                    if len(before):
                        end = lo + int(before[-1]) + 1
            else:
                end = _cut_row(pixels, top + int(limit * 0.75), hi)
        out.append((pixels[top:end], (end - top) * scale))
        top, fit = end, room
        rest = free[top:] if free is not None else None
        if rest is not None and len(rest) and rest.all() and len(rest) * scale < 3 * LINE:
            break                            # only a little answer space left: not a page of its own
    return out


def _space_rows(q, a):
    """Which rows of the crop with answer space (a) are answer space: the question crop (q)
    is the same crop with its answer space taken out, row for row, so the rows of a that
    the rows of q do not match in order are the space."""
    free = np.ones(a.shape[0], dtype=bool)
    j = 0
    for row in q:
        while j < a.shape[0] and not np.array_equal(row, a[j]):
            j += 1
        if j == a.shape[0]:
            break
        free[j] = False
        j += 1
    return free


def _ruled_rows(px):
    """Which rows are written answer lines: stretches of dotted lines with only white
    between them, from a little above the first line to the last. A question crop keeps
    the lines between its parts (the crop runs on from part to part); only the space
    after the last part is left out of it, so the lines must be found in the picture.
    A dotted line is a band at most 3 rows thick (and a fainter row at either edge),
    white above and below, of many short marks across at least half the width."""
    h, w = px.shape
    dark = px < 200
    edges = np.diff(np.pad(dark.astype(np.int8), ((0, 0), (1, 1))), axis=1)
    band = np.zeros(h, dtype=bool)
    for y in np.flatnonzero((edges == 1).sum(1) >= max(40, w // 20)):
        starts, ends = np.flatnonzero(edges[y] == 1), np.flatnonzero(edges[y] == -1)
        band[y] = (ends - starts).max() <= 5 and ends[-1] - starts[0] >= w / 2
    blank = dark.sum(1) <= 2
    lines = []                               # (top, bottom) of each dotted line
    e = np.flatnonzero(np.diff(np.concatenate([[0], band.astype(np.int8), [0]])))
    count = dark.sum(1)
    for a, b in zip(e[::2], e[1::2]):
        if b - a > 3:
            continue
        faint = count[a:b].min() // 4         # a row of the dots' soft edge counts as the line's
        if a > 0 and 2 < count[a - 1] <= faint:
            a -= 1
        if b < h and 2 < count[b] <= faint:
            b += 1
        if a >= 4 and b + 4 <= h and blank[a - 4:a].all() and blank[b:b + 4].all():
            lines.append((a, b))
    out = np.zeros(h, dtype=bool)
    i = 0
    while i < len(lines):
        j = i                                # the lines of one stretch: only white between them
        while j + 1 < len(lines) and blank[lines[j][1]:lines[j + 1][0]].all():
            j += 1
        top, bottom = lines[i][0], lines[j][1]
        step = (bottom - top) // (j - i) if j > i else 40
        above = top
        while above > 0 and blank[above - 1] and top - above < step // 2:
            above -= 1
        out[above:min(h, bottom + 2)] = True
        i = j + 1
    return out


WORK_AREA = 192.0                        # an admissions question's blank working space at the original amount


def _block(r, space):
    """A question as laid out: (grey rows, which of them are answer space, space below in
    points, ruled: the space has answer lines, else it is blank). CIE questions keep a share of each stretch
    of their original answer space, each part's (cut at a white row, between its lines),
    every part's text kept whole; papers answered in a booklet get lines, two per mark at
    the original amount; admissions questions, answered by a letter, get blank space to
    work in."""
    share = SPACE[space]
    q = paths.resolve(r["image"])
    if not q:
        return None
    cie = r["syllabus"] in bank.CIE
    a = paths.answer_space(r["image"]) if cie and not booklet(r) else None
    lines_of = lambda pt: pt // LINE * LINE
    if not cie or booklet(r):
        px = _grey(q)
        if share == 0:
            return px, None, 0, False
        each = 2 * (r["marks"] or 1) * LINE if cie else WORK_AREA
        return px, None, lines_of(each * share), cie
    # the crop with the space after the last part (when the paper has any there), and in
    # it the space: the rows the question crop leaves out, and the lines between parts
    qx = _grey(q)
    px = _grey(a) if a else qx
    free = (_space_rows(qx, px) if a else np.zeros(px.shape[0], dtype=bool)) | _ruled_rows(px)
    if share == 0:
        return px[~free], None, 0, False
    if share == 1:
        return px, free, 0, True
    keep = np.ones(px.shape[0], dtype=bool)  # each stretch of space: its first share, ended at a white row
    edges = np.flatnonzero(np.diff(np.concatenate([[0], free.astype(np.int8), [0]])))
    for start, end in zip(edges[::2], edges[1::2]):
        n = end - start
        upto = start + int(n * share)
        if upto > start:
            upto = _cut_row(px, max(start, upto - int(n * 0.15)), upto + 1)
        keep[upto:end] = False
    return px[keep], free[keep], 0, True


def layout(rows, space=SPACE_DEFAULT):
    """Pages as lists of (grey rows, or LINES / BLANK for answer space, y, height, qid, code, q). A
    question that does not fit in the rest of the page starts the next one; only a question
    taller than a whole page is cut, below the question where it can be."""
    width = A4[0] - 2 * SIDE
    room = A4[1] - TOP - BOTTOM
    gap = GAP if space else GAP_TIGHT
    pages = [[]]
    y = TOP                                  # where the next block goes on the last page

    def new_page():
        nonlocal y
        pages.append([])
        y = TOP

    for r in rows:
        code = bank.paper_code(r)
        b = _block(r, space)
        if not b:
            continue
        px, free, lines, ruled = b
        mark = LINES if ruled else BLANK
        pieces = _slices(px, width, room, room, free)
        height = pieces[0][1] if len(pieces) == 1 else room + 1
        if pages[-1]:
            y += gap
            need = height + (LINES_GAP + lines if lines else 0)
            if need > room:                  # too tall to keep together: at least three lines with it
                need = height + (LINES_GAP + 3 * LINE if lines else 0)
            if y + need > TOP + room:        # starts the next page rather than being cut
                new_page()
        for i, (part, hpt) in enumerate(pieces):
            if i:
                new_page()
            pages[-1].append((part, y, hpt, r["id"], code, r["q"]))
            y += hpt
        if lines:
            y += LINES_GAP
            while lines >= LINE:
                band = min(lines, (TOP + room - y) // LINE * LINE)
                if band < LINE:
                    new_page()
                    continue
                pages[-1].append((mark, y, band, r["id"], code, r["q"]))
                y += band
                lines -= band
    return [p for p in pages if p]


def _image(doc, pixels):
    """The xref of a grey image made from the rows, compressed here once. Inserting a PNG
    instead makes PyMuPDF decode it and store it raw, and saving then compresses every
    image again: ten times slower for a long set."""
    h, w = pixels.shape
    xref = doc.get_new_xref()
    doc.update_object(xref, f"<</Type/XObject/Subtype/Image/Width {w}/Height {h}/ColorSpace/DeviceGray/BitsPerComponent 8>>")
    doc.update_stream(xref, zlib.compress(np.ascontiguousarray(pixels).tobytes(), 6), compress=False)
    doc.xref_set_key(xref, "Filter", "/FlateDecode")
    return xref


def _font(doc, page, name, xref):
    """Put a font the document already has into the page's resources: insert_text then
    uses it instead of adding the CJK font to the file once per page."""
    kind, value = doc.xref_get_key(page.xref, "Resources")
    obj, path = (int(value.split()[0]), "Font") if kind == "xref" else (page.xref, "Resources/Font")
    kind, value = doc.xref_get_key(obj, path)
    if kind == "xref":                       # the font dictionary is an object of its own
        doc.xref_set_key(int(value.split()[0]), name, f"{xref} 0 R")
    else:
        doc.xref_set_key(obj, f"{path}/{name}", f"{xref} 0 R")


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


def build(s, footer=None, space=None):
    """Path of the set's question paper PDF, building it if the cache is stale. Raises
    EmptyPaper when there is nothing to lay out. footer: footer options in place of the
    saved ones (the settings page's preview); space: the answer space, 0 to 3 (SPACE), in
    place of the saved default (an export's own choice)."""
    opts = {**settings.load(), **(footer or {})}
    space = opts["space"] if space is None else max(0, min(len(SPACE) - 1, int(space)))
    rows = _rows(s["items"])

    def stamp(r):                        # rebuilt when a crop is redone
        out = []
        for p in (paths.resolve(r["image"]), paths.answer_space(r["image"])):
            out.append(int(os.path.getmtime(p)) if p else 0)
        return out
    key = hashlib.sha1(json.dumps([VERSION, s["name"], s["items"], {k: opts[k] for k in opts if k not in ("theme", "space")}, SPACE[space],
                                   [stamp(r) for r in rows]], ensure_ascii=False).encode()).hexdigest()[:12]
    os.makedirs(CACHE, exist_ok=True)
    base = f'{s["id"]}-s{space}-'           # each answer space kept apart: an export may differ from the default
    out = os.path.join(CACHE, base + key + ".pdf")
    if os.path.exists(out):
        return out
    for f in os.listdir(CACHE):
        if f.startswith(base) and f.endswith(".pdf"):
            try:
                os.remove(os.path.join(CACHE, f))
            except OSError:
                pass
    original = original_pdf(rows) if space == SPACE_DEFAULT else None   # the original paper has the original space
    if original:
        doc = pymupdf.open(original)
    else:
        doc = pymupdf.open()
        pages = layout(rows, space)
        if not pages:
            raise EmptyPaper("题组中没有可排版的题目")
        width = A4[0] - 2 * SIDE
        fonts = {}                           # resource name -> xref: one font object for every page
        for n, items in enumerate(pages, 1):
            page = doc.new_page(width=A4[0], height=A4[1])
            for name, xref in fonts.items():
                _font(doc, page, name, xref)
            for px, y, hpt, *_ in items:
                if isinstance(px, str):
                    if px == LINES:
                        _lines(page, y, hpt)
                else:
                    page.insert_image(pymupdf.Rect(SIDE, y, SIDE + width, y + hpt), xref=_image(doc, px))
            _footer(page, n, len(pages), s["name"], [(None, None) + tuple(it[3:]) for it in items], opts)
            fonts.update((f[4], f[0]) for f in page.get_fonts())
    tmp = f"{out}.{os.getpid()}.{threading.get_ident()}.tmp"   # written whole, then put in place: never a half-written PDF;
                                                                # per thread, as two requests may build the same paper
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
