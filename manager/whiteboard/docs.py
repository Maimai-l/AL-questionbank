"""Question paper boards: page layout and PDF export, after white-board's whiteboard/docs.py.

Pages sit top to bottom in board coordinates (PDF points), centred on the widest
page, PAGE_GAP apart, exactly as white-board lays out a document board; strokes are
assigned to the page under their centre. Export appends one new content stream per
written page and leaves the page's own streams untouched, so the file grows only by
the ink (white-board does this with pypdf; here it is PyMuPDF).
"""
from __future__ import annotations

import math
import re
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple

import pymupdf

from . import inkpdf

PAGE_GAP = 24.0


def probe(path: str | Path) -> List[List[float]]:
    """Page sizes [width, height] as shown (rotation applied), in points."""
    with pymupdf.open(str(path)) as doc:
        return [[round(p.rect.width, 2), round(p.rect.height, 2)] for p in doc]


def layout(pages: Sequence[Sequence[float]], gap: float = PAGE_GAP) -> List[Dict[str, float]]:
    """Pages top to bottom, centred on the widest one."""
    if not pages:
        return []
    widest = max(float(p[0]) for p in pages)
    boxes, y = [], 0.0
    for w, h in pages:
        boxes.append({"x": (widest - float(w)) / 2, "y": y, "w": float(w), "h": float(h)})
        y += float(h) + gap
    return boxes


def canvas(pages: Sequence[Sequence[float]], gap: float = PAGE_GAP) -> Dict[str, Any]:
    widest = max(float(p[0]) for p in pages)
    height = sum(float(p[1]) for p in pages) + gap * (len(pages) - 1)
    return {"mode": "fixed", "width": widest, "height": height}


def layers(pages: Sequence[Sequence[float]], src: str, gap: float = PAGE_GAP) -> List[Dict[str, Any]]:
    """One sheet layer per page; `src` has {n} for the page index (and may have {w})."""
    return [{"src": src.replace("{n}", str(i)), "x": round(b["x"], 2), "y": round(b["y"], 2),
             "width": b["w"], "height": b["h"], "sheet": True} for i, b in enumerate(layout(pages, gap))]


def _center(stroke: Dict[str, Any]) -> Tuple[float, float]:
    flat = stroke.get("p") or []
    if not flat:
        return 0.0, 0.0
    xs, ys = flat[0::3], flat[1::3]
    return (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2


def group_by_page(strokes: Sequence[Dict[str, Any]], boxes: Sequence[Dict[str, float]]) -> List[List[Dict[str, Any]]]:
    """By the stroke's centre; strokes in a gap go to the nearest page."""
    groups: List[List[Dict[str, Any]]] = [[] for _ in boxes]
    for stroke in strokes:
        _, cy = _center(stroke)
        best, best_d = 0, math.inf
        for i, b in enumerate(boxes):
            if b["y"] <= cy <= b["y"] + b["h"]:
                best = i
                break
            d = min(abs(cy - b["y"]), abs(cy - b["y"] - b["h"]))
            if d < best_d:
                best, best_d = i, d
        groups[best].append(stroke)
    return groups


def _inherited(doc, xref: int, key: str):
    """A page attribute, following /Parent (Rotate, MediaBox and CropBox inherit)."""
    for _ in range(32):
        kind, value = doc.xref_get_key(xref, key)
        if kind != "null":
            return value
        kind, parent = doc.xref_get_key(xref, "Parent")
        if kind != "xref":
            return None
        xref = int(parent.split()[0])
    return None


class _Box:
    def __init__(self, nums):
        x0, y0, x1, y1 = nums
        self.left, self.bottom = min(x0, x1), min(y0, y1)
        self.width, self.height = abs(x1 - x0), abs(y1 - y0)


def page_geometry(doc, page) -> Tuple[List[float], float, float]:
    """inkpdf.page_geometry for a PyMuPDF page: the cm matrix from shown coordinates."""
    raw = _inherited(doc, page.xref, "CropBox") or _inherited(doc, page.xref, "MediaBox") or "[0 0 612 792]"
    nums = [float(v) for v in re.findall(r"-?[\d.]+", raw)[:4]]
    rot = _inherited(doc, page.xref, "Rotate")
    return inkpdf.page_matrix(int(float(rot)) if rot else 0, _Box(nums))


def _new_stream(doc, data: bytes) -> int:
    xref = doc.get_new_xref()
    doc.update_object(xref, "<<>>")
    doc.update_stream(xref, data, compress=True)
    return xref


def export_pdf(src: str | Path, strokes: Sequence[Dict[str, Any]], out: str | Path) -> Path:
    """The source PDF with the ink appended to each written page as vector paths."""
    doc = pymupdf.open(str(src))
    boxes = layout([[p.rect.width, p.rect.height] for p in doc])
    groups = group_by_page(strokes, boxes)
    for i, page in enumerate(doc):
        if not groups[i]:
            continue
        matrix, _, _ = page_geometry(doc, page)
        raw, alphas = inkpdf.content_stream(groups[i], origin=(boxes[i]["x"], boxes[i]["y"]), matrix=matrix)
        if not raw:
            continue
        kind, contents = doc.xref_get_key(page.xref, "Contents")
        old = re.findall(r"\d+ 0 R", contents) if kind in ("array", "xref") else []
        refs = [f"{_new_stream(doc, b'q')} 0 R"] + old + [f"{_new_stream(doc, b'Q')} 0 R", f"{_new_stream(doc, raw)} 0 R"]
        doc.xref_set_key(page.xref, "Contents", "[" + " ".join(refs) + "]")
        if alphas:
            kind, res = doc.xref_get_key(page.xref, "Resources")
            if kind == "xref":
                rx = int(res.split()[0])
            else:                            # inline or inherited: give the page its own copy
                rx = doc.get_new_xref()
                inherited = _inherited(doc, page.xref, "Resources") or "<<>>"
                if re.fullmatch(r"\d+ 0 R", inherited.strip()):
                    inherited = doc.xref_object(int(inherited.split()[0]), compressed=True)
                doc.update_object(rx, inherited)
                doc.xref_set_key(page.xref, "Resources", f"{rx} 0 R")
            for a in sorted(alphas):
                doc.xref_set_key(rx, f"ExtGState/WBa{a}", f"<</Type/ExtGState/ca {a / 100:.2f}/CA {a / 100:.2f}>>")
    out = Path(out)
    doc.save(str(out), garbage=0, deflate=False)
    doc.close()
    return out
