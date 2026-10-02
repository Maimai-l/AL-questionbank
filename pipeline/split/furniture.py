#!/usr/bin/env python3
"""Page furniture on a CAIE question paper: everything printed on the page
that is not part of any question.

CAIE papers share one template, so the furniture is a short, closed list:

  page number     centred digits above the text band        (all years)
  footer          "© UCLES 2023", "9709/12/M/J/25", "[Turn over"
  watermark       "www.dynamicpapers.com" on mirrored copies
  barcode text    "* 0000800000007 *" at the top, and a block of glyph
                  soup at the bottom that renders as the 2D barcode (2025+)
  margin text     vertical "DO NOT WRITE IN THIS MARGIN" at both edges (2025+)
  corner marks    short hairlines in the bottom corners (2025+)
  blank page      "BLANK PAGE" alone on a page

Each item comes back as (kind, fitz.Rect). A crop is clean exactly when its
clip rectangle intersects none of them; audit_crops.py checks that for every
question, and crop.py derives its clip from the same list.
"""
import re

import pymupdf as fitz

FOOTER_RE = re.compile(r"©\s*UCLES|^\d{4}/\d{2}/\s*[A-Z]|\[Turn over")
WATERMARK_RE = re.compile(r"dynamicpapers|www\.", re.I)
BARCODE_RE = re.compile(r"^\*\s*\d{8,}\s*\*$")
PAGENO_RE = re.compile(r"^\d{1,2}$")
BLANK_RE = re.compile(r"^\s*(BLANK PAGE|ADDITIONAL PAGE)\s*$")
# a pointer, not question material: "Question 5(c) is printed on the next page."
NAV_RE = re.compile(r"is printed on the next page|continued on the (next|following) page", re.I)
CTRL_RE = re.compile(r"[\x00-\x1f\x7f]")
TIGHT = fitz.TEXTFLAGS_DICT | fitz.TEXT_ACCURATE_BBOXES
# 9231 June 2021 Papers 3 and 4 print the footer at y≈761 on an 842pt page,
# 81pt from the bottom; everywhere else it sits within 60pt. A 70pt limit left
# those footers inside the text band, in the crops and in the question text.
FOOTER_H = 100
MARGIN_W = 35      # the vertical "DO NOT WRITE IN THIS MARGIN" sits within 35pt of the edge
STRIP_W = 24       # its grey background strip is 21pt wide; 9618 tables start at x≈32


# Typography that is question content, not barcode: the ellipsis leaders of a
# fill-in-the-blank pseudocode line ("RETURN ……………"), arrows, maths symbols,
# the "●●●●" of a masked password, and Symbol-font glyphs (U+F0xx, decoded by
# clean_encoding.py). Counting these as odd dropped 40 lines from 9618 papers.
TYPO_RE = re.compile(r"[\u2000-\u206f\u2190-\u21ff\u2200-\u22ff"
                     r"\u25a0-\u25ff\uf000-\uf0ff]")


def glyph_soup(txt):
    """Text drawn in a barcode font: mostly non-ASCII letters or control bytes."""
    t = txt.strip()
    if len(t) < 6:
        return False
    odd = sum(1 for c in t
              if (ord(c) > 0x7e and not TYPO_RE.match(c)) or CTRL_RE.match(c))
    return odd / len(t) > 0.5


def lines(page):
    """(text, rect, horizontal) for every text line on the page."""
    out = []
    # glyph-tight boxes: the default line box includes the font's leading, which
    # makes a bottom tariff "[5]" overlap "[Turn over" although the ink does not
    for blk in page.get_text("dict", flags=TIGHT)["blocks"]:
        if blk.get("type") != 0:
            continue
        for ln in blk["lines"]:
            txt = "".join(sp["text"] for sp in ln["spans"])
            if not txt.strip():
                continue
            horizontal = abs(ln["dir"][0] - 1) < 1e-3
            out.append((txt.strip(), fitz.Rect(ln["bbox"]), horizontal))
    return out


def furniture(page):
    """List of (kind, rect) for the page furniture on this page."""
    W, H = page.rect.width, page.rect.height
    items = []
    for txt, r, horizontal in lines(page):
        if not horizontal:
            # only at the page edges: a rotated label inside a diagram
            # ("1.2 m" along a slope) is question content
            if r.x1 < MARGIN_W or r.x0 > W - MARGIN_W:
                items.append(("margin", r))
        elif FOOTER_RE.search(txt) and r.y0 > H - FOOTER_H:
            items.append(("footer", r))
        elif WATERMARK_RE.search(txt) and r.y1 < 60:
            items.append(("watermark", r))
        elif r.y1 < 30:
            items.append(("header", r))          # barcode caption, print codes above the page number
        elif BARCODE_RE.match(txt) or (glyph_soup(txt) and (r.y1 < 62 or r.y0 > H - 70)):
            items.append(("barcode", r))
        elif PAGENO_RE.match(txt) and r.y0 < 52 and r.y1 < 62 and abs((r.x0 + r.x1) / 2 - W / 2) < 30:
            items.append(("pageno", r))
        elif BLANK_RE.match(txt):
            items.append(("blank", r))
        elif NAV_RE.search(txt):
            items.append(("nav", r))
    for d in page.get_drawings():
        # the path rect of a stroked line has no width; the ink is as wide as the pen
        pen = (d.get("width") or 0) / 2
        r = fat(d["rect"]) + (-pen, -pen, pen, pen)
        if (r.y0 > H - 62 or r.y1 < 62) and (r.x1 < 70 or r.x0 > W - 70):
            items.append(("corner", r))          # registration marks, all four corners
        elif r.x1 < STRIP_W or r.x0 > W - STRIP_W:
            items.append(("margin", r))          # grey strip behind the margin text
    for img in page.get_image_info():
        r = fitz.Rect(img["bbox"])
        if r.y0 > H - 60 or r.y1 < 60:
            items.append(("barcode", r))
    return items


def fat(r, w=0.25):
    """A hairline has zero area; widen it a little so overlap tests see it."""
    r = fitz.Rect(r)
    if r.width < 2 * w:
        r.x0, r.x1 = r.x0 - w, r.x1 + w
    if r.height < 2 * w:
        r.y0, r.y1 = r.y0 - w, r.y1 + w
    return r


def is_blank(page, items=None):
    items = furniture(page) if items is None else items
    return any(k == "blank" for k, _ in items)


def band(page, items=None, gap=0.5):
    """(top, bottom): the vertical band between header and footer furniture."""
    items = furniture(page) if items is None else items
    H = page.rect.height
    # corner marks sit at the far left and right, outside any text line; they
    # would pull the band 6pt into a bottom tariff, so they are painted out by
    # crop.whiteout instead of shaping the band
    skip = ("margin", "nav", "corner")
    top = max([r.y1 for k, r in items if r.y1 < 70 and k not in skip] + [0.0]) + gap
    bottom = min([r.y0 for k, r in items
                  if (r.y0 > H - 75 or k == "footer") and k not in skip] + [H]) - gap
    return top, bottom


def columns(page, items=None, gap=2.0):
    """(left, right): the horizontal band between the margin columns."""
    items = furniture(page) if items is None else items
    W = page.rect.width
    left = max([r.x1 for k, r in items if k == "margin" and r.x1 < W / 2] + [0.0]) + gap
    right = min([r.x0 for k, r in items if k == "margin" and r.x0 > W / 2] + [W]) - gap
    return left, right
