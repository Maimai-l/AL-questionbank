#!/usr/bin/env python3
"""Split CAIE question papers into individual questions (9709 / 9231 / 9618).

Relies on the very regular layout of CAIE papers:
  * question-number blocks sit at the left margin (x0 < ~60)
  * question body sits indented (x0 ~ 73)
  * answer space is rows of dot leaders
  * running header/footer live outside the text band
Emits one record per question with text, mark tariff, and page/bbox span
so the question can also be cropped to an image.
"""
import json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))
import pymupdf as fitz  # noqa: E402

from pipeline.split import furniture  # noqa: E402

LEFT_MARGIN = 62          # question numbers start left of this
# The text band (below the page number, above the footer) is measured on each
# page by furniture.py. Fixed limits used to live here (50 and 790); they cut
# the last line off every page of the 865pt-tall 2024+ layout.
QNUM_RE = re.compile(r"^(\d{1,2})(?:\s|$)")
MARKS_RE = re.compile(r"\[(\d{1,2})\]")
# a superscript or the foot of a fraction can share the tariff's visual line:
# "... A^n = PDP^-1  [6]" reads "[6] 1" in 9231_s24_23 q8(d), and "x/(x-3) ...
# no solution. [1]" reads "[1] c" in 9231_w21_12 q6(d)(ii)
MARKS_END_RE = re.compile(r"(?:^|[\s.])\[(\d{1,2})\](?:\s+-?[0-9A-Za-z])?\s*$")
INDEX_RE = re.compile(r"\[\d{1,2}\]\s*$")
TARIFF_X1 = 530           # tariffs are right-aligned; every real one lands at x1 ~ 545
# Case-sensitive on purpose: the cover page says "Any blank pages are
# indicated", which must not be mistaken for a blank page.
BLANK_RE = re.compile(r"BLANK PAGE|ADDITIONAL PAGE")
# End-matter that follows the last question: answer-booklet furniture and the
# copyright block. Left in, it bloats the final crop with a page of ruled lines
# and pollutes the extracted text with boilerplate.
# End matter only — a mid-booklet BLANK PAGE is *not* end matter, it is a page
# to skip. Conflating the two truncates any question that spans one.
TAIL_RE = re.compile(
    r"Additional page|If you use the following|"
    r"Permission to reproduce items|To avoid the issue of disclosure|"
    r"Cambridge Assessment International Education is part of|"
    r"copyright acknowledgements are reproduced", re.I)
# Mirror-site watermarks leave stray fragments in the text layer — commas plus
# raw control bytes, which render as a thin sliver if they anchor a crop.
CTRL_RE = re.compile(r"[\x00-\x1f\x7f]")
JUNK_RE = re.compile(r"^[\s,.;:_|·•\-]*$")


def is_junk(txt):
    return bool(JUNK_RE.match(CTRL_RE.sub("", txt)))


def tail_start(page):
    """y of the first end-matter line on this page, or None.

    Detected on the *raw* text, before filtering, because the block that gives
    the game away ("Additional page") is exactly the one the filter removes —
    and its continuation lines ("shown.", "publisher will be pleased to ...")
    are not individually recognisable.
    """
    ys = []
    for blk in page.get_text("dict")["blocks"]:
        if blk.get("type") != 0:
            continue
        for ln in blk["lines"]:
            txt = "".join(sp["text"] for sp in ln["spans"])
            if TAIL_RE.search(txt):
                ys.append(ln["bbox"][1])
    return min(ys) if ys else None


def is_dots(t):
    s = t.replace(".", "").replace(" ", "").replace("\n", "")
    return len(s) < 3 and t.count(".") > 20


def clean(t):
    t = " ".join(t.split())
    t = re.sub(r"\.{5,}", " ", t)
    return t.strip()


LINE_TOL = 7.0    # points; two fragments this close vertically are one line


_BAND = {}


def page_furniture(page):
    """(top, bottom, furniture items) for this page, computed once."""
    key = (page.parent.name, page.number)
    if key not in _BAND:
        items = furniture.furniture(page)
        top, bottom = furniture.band(page, items)
        _BAND[key] = (top, bottom, [r for _, r in items])
    return _BAND[key]


def in_furniture(r, furn):
    r = fitz.Rect(r)
    return any((r & f).get_area() > 0.5 * max(r.get_area(), 1e-6) for f in furn)


def page_blocks(page):
    """Text fragments in reading order, header/footer/dot-leaders dropped.

    Works at PyMuPDF *line* granularity, not block granularity. Inline maths
    is emitted as its own block whose top edge sits a few points above the
    surrounding prose, so block-level y-ordering interleaves a question's
    formulae with the previous question's text. Grouping fragments into visual
    lines first, then ordering lines by y and fragments by x, restores true
    reading order and keeps question boundaries on line edges.
    """
    top, bottom, furn = page_furniture(page)
    frags = []
    for blk in page.get_text("dict")["blocks"]:
        if blk.get("type") != 0:
            continue
        for ln in blk["lines"]:
            txt = "".join(sp["text"] for sp in ln["spans"])
            x0, y0, x1, y1 = ln["bbox"]
            if y1 <= top or y0 >= bottom or in_furniture(ln["bbox"], furn):
                continue
            if furniture.glyph_soup(txt):       # barcode font; its loose box escapes in_furniture
                continue
            if not txt.strip() or is_dots(txt):
                continue
            if "dynamicpapers" in txt or "UCLES" in txt:
                continue
            if TAIL_RE.search(txt) or is_junk(txt):
                continue
            frags.append([x0, y0, x1, y1, txt])
    if not frags:
        return []

    frags.sort(key=lambda f: ((f[1] + f[3]) / 2, f[0]))
    lines, cur = [], [frags[0]]
    for f in frags[1:]:
        ref = sum((g[1] + g[3]) / 2 for g in cur) / len(cur)
        if abs((f[1] + f[3]) / 2 - ref) <= LINE_TOL:
            cur.append(f)
        else:
            lines.append(cur)
            cur = [f]
    lines.append(cur)

    out = []
    for ln in lines:
        ln.sort(key=lambda f: f[0])
        out.append((min(f[0] for f in ln), min(f[1] for f in ln),
                    max(f[2] for f in ln), max(f[3] for f in ln),
                    " ".join(f[4] for f in ln)))
    return out


def drawing_boxes(page):
    """Bounding boxes of vector graphics inside the text band: diagrams, tables,
    answer boxes and graph-paper grids.

    Hairlines count. A grid for "draw a histogram" is hundreds of zero-height
    rules; skipping thin shapes cut every such grid off the crop. Page
    furniture (corner marks, margin strips) is excluded by position.
    """
    top, bottom, furn = page_furniture(page)
    boxes = []
    for d in page.get_drawings():
        r = furniture.fat(d["rect"])
        if r.width < 3 and r.height < 3:
            continue
        if r.y0 < top or r.y1 > bottom or in_furniture(r, furn):
            continue
        boxes.append(r)
    return boxes


def heading_top(blocks, y0, y1, min_overlap=3, touch=3.5):
    """Top of the question's first line, not just of its number.

    A first line carrying a built-up fraction is set taller than the number
    beside it and sorts as a separate line starting a few points higher
    (9709_s21_31_q02: "Find the real root of the equation 2e^x + e^-x ..."), and
    the top row of a column vector or an integral's upper limit sits wholly
    above it, touching (9709_m25_32_q08, 9709_s25_31_q09). Cut at the number's
    own top, those went to the previous question. Consecutive questions are
    separated by far more than `touch`, so the previous question's last line
    is never pulled in."""
    top = y0
    for b in blocks:
        if min(y1, b[3]) - max(y0, b[1]) >= min_overlap:
            top = min(top, b[1])
    grew = True
    while grew:
        grew = False
        for b in blocks:
            if b[0] >= LEFT_MARGIN and b[1] < top and 0 <= top - b[3] < touch:
                top, grew = b[1], True
    return top


def split_paper(path):
    doc = fitz.open(path)
    stem = os.path.basename(path).replace(".pdf", "")
    subject, series, _, comp = stem.split("_")

    # Collect every left-margin block that opens with a number, then walk the
    # candidates expecting 1, 2, 3, ...  A stray number inside a diagram never
    # matches the expected value, and one missed heading no longer cascades.
    cand = []     # (page, y0, qnum)
    for pno in range(doc.page_count):
        page = doc[pno]
        if BLANK_RE.search(page.get_text()[:400]):
            continue
        blocks = page_blocks(page)
        for x0, y0, x1, y1, txt in blocks:
            if x0 < LEFT_MARGIN:
                m = QNUM_RE.match(" ".join(txt.split()))
                if m:
                    cand.append((pno, heading_top(blocks, y0, y1), int(m.group(1))))

    # Walk expecting 1, 2, 3, ...  Tolerate one missing heading (a question
    # number that got merged into a formula block); the preceding record then
    # absorbs the orphaned question and is flagged.
    starts, expect = [], 1
    for pno, y0, n in cand:
        if n == expect:
            starts.append((pno, y0, n, False))
            expect = n + 1
        elif n == expect + 1:
            if starts:
                starts[-1] = starts[-1][:3] + (True,)
            starts.append((pno, y0, n, False))
            expect = n + 1
    if not starts:
        return []

    questions = []
    for i, (pno, y0, qnum, merged) in enumerate(starts):
        end_page, end_y = (starts[i + 1][0], starts[i + 1][1]) if i + 1 < len(starts) \
            else (doc.page_count - 1, page_furniture(doc[-1])[1])

        parts, spans = [], []
        for p in range(pno, end_page + 1):
            page = doc[p]
            top, bottom, _ = page_furniture(page)
            lo = y0 if p == pno else top
            hi = end_y if p == end_page else bottom
            if BLANK_RE.search(page.get_text()[:400]):
                continue                      # mid-booklet blank page: skip, don't stop
            # everything below the first end-matter marker is answer booklet
            ts = tail_start(page)
            if ts is not None:
                hi = min(hi, ts - 12)             # and the rule drawn just above it
            # on a continuation page page_blocks has already dropped the lines
            # above the band; a line whose loose box starts a few points above
            # the page number's foot ("(b) Hence find ... [5]" at y 48, band top
            # 51.7, 9709_m21_qp_22) belongs to the question, tariff included
            floor = lo - 2 if p == pno else -1
            blocks = [b for b in page_blocks(page) if floor <= b[1] < hi]
            if not blocks:
                # the last question's span runs to the end of the booklet; once
                # a page has no real content left, everything after it is
                # end matter, so stop rather than cropping blank pages in
                if spans:
                    break
                continue
            parts += [(clean(b[4]), b[2]) for b in blocks if clean(b[4])]
            # crop extent: last text block or diagram inside the span
            bottom = max(b[3] for b in blocks)
            for r in drawing_boxes(page):
                if lo - 2 <= r.y0 < hi:
                    bottom = max(bottom, r.y1)
            spans.append({"page": p, "y0": max(lo - 6, 0), "y1": min(bottom + 8, hi)})

        text = " ".join(t for t, _ in parts)
        # A mark tariff is right-aligned at the end of the part, so it ends a
        # visual line. Scanning the whole blob instead picks up bracketed
        # numbers inside tables and pseudocode (row numbers, array subscripts),
        # which is how a 7-mark question ends up "worth" 114.
        # ...and it is right-aligned to the margin, which a trace-table column
        # header like "[10]" at the end of a row is not.
        marks = []
        for t, x1 in parts:
            m = MARKS_END_RE.search(t)
            # the last index of an array header ("[9] [10]", 9618_s25_33 q13)
            if m and INDEX_RE.search(t[:m.start(1) - 1]):
                m = None
            if m and x1 >= TARIFF_X1:
                marks.append(int(m.group(1)))
        if not marks:
            marks = [int(m) for m in MARKS_RE.findall(text)]
        questions.append({
            "subject": subject,
            "paper": f"{subject}/{comp}",
            "series": series,
            "component": comp[0],
            "variant": comp[1],
            "q": qnum,
            "text": text,
            "marks_parts": marks,
            "marks": sum(marks) if marks else None,
            "spans": spans,
            "source": os.path.basename(path),
            "absorbed_next": merged,
        })
    return questions


if __name__ == "__main__":
    pdfs = sorted(f for f in os.listdir(sys.argv[1]) if "_qp_" in f)
    allq, failed = [], []
    for f in pdfs:
        try:
            qs = split_paper(os.path.join(sys.argv[1], f))
            if len(qs) < 4:
                failed.append((f, len(qs)))
            allq += qs
        except Exception as e:
            failed.append((f, f"{type(e).__name__}: {e}"))
    json.dump(allq, open(sys.argv[2], "w"), ensure_ascii=False, indent=1)
    print(f"papers={len(pdfs)}  questions={len(allq)}  suspicious={len(failed)}")
    for f, why in failed[:15]:
        print("  ", f, why)
