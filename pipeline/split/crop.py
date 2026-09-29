#!/usr/bin/env python3
"""Render each question's page region to a PNG.

The text layer of a CAIE maths paper loses superscripts, fraction bars and
diagrams. The crop is the loss-free fallback: whatever the text says, the image
is what the candidate actually saw.

    python3 pipeline/split/crop.py questions.json <pdfdir> <outdir>

The clip for each span is the span itself, narrowed to the part of the page
that carries questions: below the page number and top barcode, above the
footer and bottom barcode, and inside the "DO NOT WRITE IN THIS MARGIN"
columns. Blank pages contribute nothing. These limits come from furniture.py,
which is also what audit_crops.py checks the result against.
"""
import json, os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))
import pymupdf as fitz  # noqa: E402

from pipeline.split import furniture, split_qp  # noqa: E402

DPI = 150
ZOOM = DPI / 72.0
PAD_X_OLD = 6        # the original rule: full page width minus 6pt; audit only
EDGE = 18            # without margin furniture, keep this far from the page edge;
                     # 9618 tables run out to x≈28 and x≈567, so 40 is too tight
MIN_HEIGHT = 8


def qid(q):
    subject = q.get("subject") or q["source"].split("_")[0]
    return f"{subject}_{q['series']}_{q['component']}{q['variant']}_q{q['q']:02d}"


def page_limits(page, items=None):
    """Rect of the page that may appear in a crop."""
    items = furniture.furniture(page) if items is None else items
    top, bottom = furniture.band(page, items)
    left, right = furniture.columns(page, items)
    W = page.rect.width
    return fitz.Rect(max(left, EDGE), top, min(right, W - EDGE), bottom)


DOTS = set(". …")
TOL = 2.0           # pt a line box may poke past a clip edge: line boxes include leading


def material(page, items=None):
    """(label, rect) for everything on the page that is question material:
    text lines and vector drawings that are not furniture, junk or dot leaders."""
    items = furniture.furniture(page) if items is None else items
    furn = [r for _, r in items]
    tail = split_qp.tail_start(page)     # copyright block / additional page

    def is_furn(r):
        return any((fitz.Rect(r) & f).get_area() > 0.5 * max(r.get_area(), 1e-6) for f in furn)
    out = []

    def keep(r):
        return tail is None or r.y0 < tail - 12
    for txt, r, _ in furniture.lines(page):
        if not keep(r):
            continue
        if split_qp.is_junk(txt) or set(txt.replace(" ", "")) <= DOTS or is_furn(r):
            continue
        out.append((txt[:40], r))
    for d in page.get_drawings():
        r = furniture.fat(d["rect"])
        if r.width < 3 and r.height < 3:
            continue
        if keep(r) and not is_furn(r):
            out.append(("<drawing>", r))
    return out



def clips(q, doc):
    """(page number, clip rect) for each part of the question that gets rendered."""
    for sp in q["spans"]:
        page = doc[sp["page"]]
        items = furniture.furniture(page)
        if furniture.is_blank(page, items):
            continue
        lim = page_limits(page, items)
        clip = fitz.Rect(lim.x0, max(sp["y0"], lim.y0), lim.x1, min(sp["y1"], lim.y1))
        # split_qp stops spans at fixed y limits; a line or diagram that straddles
        # the edge belongs to the question, so widen the clip to take all of it,
        # never past the furniture band
        mat = [r for _, r in material(page, items)]
        grown = True
        while grown:
            grown = False
            for r in mat:
                if r.x1 <= clip.x0 or r.x0 >= clip.x1:
                    continue
                if r.y0 < clip.y1 < r.y1 and r.y1 <= lim.y1 + TOL:
                    y1 = min(r.y1 + 1, lim.y1)
                    if y1 > clip.y1:
                        clip.y1, grown = y1, True
                if r.y0 < clip.y0 < r.y1 and r.y0 >= lim.y0 - TOL:
                    y0 = max(r.y0 - 1, lim.y0)
                    if y0 < clip.y0:
                        clip.y0, grown = y0, True
        if clip.height >= MIN_HEIGHT:
            yield sp["page"], clip


def whiteout(pix, page, clip, items=None):
    """Paint every piece of furniture that falls inside the clip white.

    The band keeps page number, footer and barcodes out; this catches what a
    band cannot, such as the corner marks beside a tariff on the last line."""
    items = furniture.furniture(page) if items is None else items
    for _, r in items:
        r = fitz.Rect(r) & clip
        if r.is_empty:
            continue
        # the pixmap's origin is the clip's position on the page, not (0, 0)
        box = fitz.IRect(pix.x + int((r.x0 - clip.x0) * ZOOM) - 1, pix.y + int((r.y0 - clip.y0) * ZOOM) - 1,
                         pix.x + int((r.x1 - clip.x0) * ZOOM) + 2, pix.y + int((r.y1 - clip.y0) * ZOOM) + 2)
        box &= pix.irect
        if not box.is_empty:
            pix.set_rect(box, (255,) * pix.n)
    return pix


def render(q, pdfdir, outdir):
    path = os.path.join(pdfdir, q["source"])
    doc = fitz.open(path)
    tiles = []
    for p, clip in clips(q, doc):
        pix = doc[p].get_pixmap(matrix=fitz.Matrix(ZOOM, ZOOM), clip=clip, alpha=False)
        tiles.append(whiteout(pix, doc[p], clip))
    doc.close()
    if not tiles:
        return None

    w = max(t.width for t in tiles)
    h = sum(t.height for t in tiles)
    out = fitz.Pixmap(fitz.csGRAY, fitz.IRect(0, 0, w, h), False)
    out.clear_with(255)
    y = 0
    for t in tiles:
        g = fitz.Pixmap(fitz.csGRAY, t) if t.n > 1 else t
        g.set_origin(0, y)
        out.copy(g, g.irect)
        y += t.height
    name = qid(q) + ".png"
    out.save(os.path.join(outdir, name))
    return name


if __name__ == "__main__":
    qs = json.load(open(sys.argv[1]))
    pdfdir, outdir = sys.argv[2], sys.argv[3]
    os.makedirs(outdir, exist_ok=True)
    fails = 0
    for i, q in enumerate(qs, 1):
        try:
            q["image"] = render(q, pdfdir, outdir)
        except Exception:
            q["image"] = None
            fails += 1
        if i % 250 == 0:
            print(f"  {i}/{len(qs)}", flush=True)
    json.dump(qs, open(sys.argv[1], "w"), ensure_ascii=False, indent=1)
    got = sum(1 for q in qs if q.get("image"))
    print(f"rendered {got}/{len(qs)}  failures={fails}")
