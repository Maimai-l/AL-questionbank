#!/usr/bin/env python3
"""Remove the PapaCambridge watermark from downloaded papers, in place.

    python3 pipeline/fetch/strip_watermark.py [--check] [FILE_OR_DIR ...]

Default places: raw/pdf, raw/ms and data/papers.

PapaCambridge wraps each original page in a form XObject `/R` and draws three
layers in the page content: diagonal "PapaCambridge" marks (`/FormXob.pcm`),
the original (`/R` plus the page's header, footer and margin XObjects R0..),
then a second overlay (a faint large mark, a banner and a QR code below the
footer). The original layer starts at the clip `q 0 0 595.27559 841.88976 re W n`
that precedes `/R Do`; the second overlay starts at the next full-page clip.
Pages PapaCambridge re-assembled (the mark schemes, and six compact question papers
whose content separates operators with spaces) have no `/R`: there the diagonal marks,
if any, are dropped and the content is cut where the second overlay begins (the
full-page clip followed by `/gRLs0-0 gs`).
The page content is replaced by the original layer only, and unused objects are
dropped on save. A page with neither `/FormXob.pcm` nor that overlay is left alone.

--check only reports which files carry the watermark.
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import pymupdf  # noqa: E402

from lib import paths  # noqa: E402

CLIP = re.compile(rb"\nq\n0(?:\.0)? 0(?:\.0)? 595\.27\d* 841\.88\d* re\nW\nn\n")
PAGE_CLIP = re.compile(rb"q\s+0(?:\.0)?\s+0(?:\.0)?\s+595\.27\d*\s+841\.8\d*\s+re\s+W\s+n\s")
OVERLAY = b"/gRLs0-0 gs"


def balanced(seg):
    depth = 0
    for line in seg.split(b"\n"):
        t = line.strip()
        if t == b"q":
            depth += 1
        elif t == b"Q":
            depth -= 1
            if depth < 0:
                return False
    return depth == 0


def original_layer(content):
    """The page's own content, or None if the layout is not the one described above."""
    r = content.find(b"/R Do")
    if r < 0:
        return None
    starts = [m.start() for m in CLIP.finditer(content) if m.start() < r]
    ends = [m.start() for m in CLIP.finditer(content) if m.start() > r]
    if not starts:
        return None
    a = starts[-1] + 1
    b = ends[0] if ends else len(content)
    seg = content[a:b]
    # the overlay is preceded by the closing of the outer group: trim trailing unmatched Q
    while not balanced(seg) and seg.rstrip().endswith(b"Q"):
        seg = seg.rstrip()[:-1]
    return seg if balanced(seg) else None


def inline_layer(content):
    """Pages PapaCambridge re-assembled itself (the mark schemes): no `/R` wrapper, the
    original drawn inline between the two overlays. Drop the diagonal marks (the
    `/FormXob.pcm` draws) and cut the content where the second overlay begins."""
    seg = re.sub(rb"q\n[-\d. ]+cm\n/FormXob\.pcm Do\nQ\n", b"", content)
    tail = [m.start() for m in PAGE_CLIP.finditer(seg) if OVERLAY in seg[m.start():m.start() + 300]]
    if tail:
        seg = seg[:tail[-1]]
    depth = 0
    for t in re.findall(rb"[^\s/\[\]()<>{}%]+", re.sub(rb"\((?:\\.|[^\\)])*\)", b"", seg)):
        depth += (t == b"q") - (t == b"Q")
    if depth < 0:
        return None
    return seg + b"\nQ" * depth


def page_marked(page):
    c = page.read_contents()
    return b"/FormXob.pcm Do" in c or OVERLAY in c


def marked(doc):
    return any(page_marked(p) for p in doc)


def strip(path):
    doc = pymupdf.open(path)
    if not marked(doc):
        return "clean"
    for page in doc:
        if not page_marked(page):
            continue
        xrefs = page.get_contents()
        content = page.read_contents()
        seg = original_layer(content) if b"/R Do" in content else inline_layer(content)
        if seg is None:
            return f"unexpected layout on page {page.number + 1}"
        doc.update_stream(xrefs[0], b"q\n" + seg + b"\nQ\n")
        for x in xrefs[1:]:
            doc.update_stream(x, b"")
    def banner(p):
        return [pymupdf.Rect(t["bbox"]) for t in p.get_texttrace() if t["type"] != 3
                and "papacambridge" in "".join(chr(c[0]) for c in t["chars"]).lower()]
    for page in doc:                     # re-assembled pages keep the banner line: redact its text
        rects = banner(page)
        for r in rects:
            page.add_redact_annot(r + (-1, -1, 1, 1))
        if rects:
            page.apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_NONE, graphics=pymupdf.PDF_REDACT_LINE_ART_NONE)
    left = [p.number + 1 for p in doc if banner(p)]
    if left:
        return f"marks left on pages {left}"
    tmp = path + ".tmp"
    doc.save(tmp, garbage=4, deflate=True)
    doc.close()
    os.replace(tmp, path)
    return "stripped"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("where", nargs="*")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    where = a.where or [os.path.join(paths.RAW, "pdf"), os.path.join(paths.RAW, "ms"), paths.PAPERS]
    files = []
    for w in where:
        if os.path.isdir(w):
            for root, _, names in os.walk(w):
                files += [os.path.join(root, n) for n in names if n.lower().endswith(".pdf")]
        elif os.path.exists(w):
            files.append(w)
    counts = {}
    for f in sorted(files):
        if a.check:
            with pymupdf.open(f) as d:
                res = "marked" if marked(d) else "clean"
        else:
            res = strip(f)
        counts[res] = counts.get(res, 0) + 1
        if res not in ("clean",):
            print(f"{res:20} {os.path.relpath(f, paths.ROOT)}")
    print(counts)


if __name__ == "__main__":
    main()
