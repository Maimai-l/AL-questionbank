#!/usr/bin/env python3
"""Remove the PapaCambridge and dynamicpapers watermarks from downloaded papers, in place.

    python3 strip_watermark.py [--check] FILE_OR_DIR ...

Standalone copy of the question bank's pipeline/fetch/strip_watermark.py (needs PyMuPDF).

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

dynamicpapers adds an Acrobat header to every page: the marked-content block
`/Artifact <</Contents (www.dynamicpapers.com)/Subtype /Header ...>> BDC ... EMC`
at the end of the page content, which draws a form XObject holding the address.
That block is removed; the form goes with the unused objects on save.

Some PapaCambridge copies are re-assembled with FPDF (producer "FPDF 1.7"): each
original page is a form XObject `/TPLn`, drawn scaled by about 0.95 to make room
for a PapaCambridge logo image (`/I1`, 999x156) at the bottom right, plus a pink
text block holding a space. Such a page is reduced to `q /TPLn Do Q`, which draws
the original page at its own size, and the logo is removed from the resources.

Pages whose content no longer draws a watermark can still list it in their resources
(`/FormXob.pcm`, or a form XObject holding a site name, left by earlier runs or by the
site itself). Such unused entries are removed too, so the objects go on save.

Links to the sites (the FPDF copies put one over the logo) are deleted, and so are
document properties and XMP metadata naming a site (the 2026 PapaCambridge copies have
"PapaCambridge" in the title, author, subject, keywords, creator and producer).

--check only reports which files still show or contain the watermark.
"""
import argparse
import os
import re

import pymupdf

CLIP = re.compile(rb"\nq\n0(?:\.0)? 0(?:\.0)? 595\.27\d* 841\.88\d* re\nW\nn\n")
PAGE_CLIP = re.compile(rb"q\s+0(?:\.0)?\s+0(?:\.0)?\s+595\.27\d*\s+841\.8\d*\s+re\s+W\s+n\s")
OVERLAY = b"/gRLs0-0 gs"
DP_HEADER = re.compile(rb"/Artifact\s*<<[^>]*?dynamicpapers[^>]*?>>\s*BDC.*?EMC\s?", re.S | re.I)
SITES = ("papacambridge", "dynamicpapers")
FPDF_TPL = re.compile(rb"/(TPL\d+) Do")
FPDF_LOGO = re.compile(rb"/(I\d+) Do")


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


def dp_marked(page):
    return bool(DP_HEADER.search(page.read_contents()))


def fpdf_marked(page):
    c = page.read_contents()
    return len(FPDF_TPL.findall(c)) == 1 and bool(FPDF_LOGO.search(c))


def leftover(page):
    """Watermark XObjects the page lists in its resources but does not draw."""
    used = set(re.findall(rb"/([^\s/\[\]()<>{}%]+)\s*Do", page.read_contents()))
    out = []
    for xref, name, invoker, _ in page.get_xobjects():
        if invoker or name.encode() in used:
            continue
        data = (page.parent.xref_stream(xref) or b"").lower()
        if name == "FormXob.pcm" or any(s.encode() in data for s in SITES):
            out.append(name)
    return out


def site_links(page):
    return [l for l in page.get_links() if any(s in (l.get("uri") or "").lower() for s in SITES)]


def site_meta(doc):
    """Document property keys and XMP metadata that name a site."""
    keys = [k for k, v in (doc.metadata or {}).items()
            if k not in ("format", "encryption") and v and any(s in v.lower() for s in SITES)]
    xmp = any(s in (doc.get_xml_metadata() or "").lower() for s in SITES)
    return keys, xmp


def doc_marked(doc):
    keys, xmp = site_meta(doc)
    return bool(keys or xmp)


def marked(doc):
    return doc_marked(doc) or any(page_marked(p) or dp_marked(p) or fpdf_marked(p)
                                  or leftover(p) or site_links(p) for p in doc)


def banner(p):
    return [pymupdf.Rect(t["bbox"]) for t in p.get_texttrace() if t["type"] != 3
            and any(w in "".join(chr(c[0]) for c in t["chars"]).lower() for w in SITES)]


def visible(doc):
    """Pages that still show or hold a mark: the diagonal marks, the PapaCambridge banner or
    the dynamicpapers address as text, the FPDF logo, an unused watermark object or a link to
    a site; [0] when only the document properties name a site.
    (A stripped page may keep the overlay's graphics-state name in its content.)"""
    pages = [p.number + 1 for p in doc if b"/FormXob.pcm Do" in p.read_contents()
             or fpdf_marked(p) or banner(p) or leftover(p) or site_links(p)]
    return pages or ([0] if doc_marked(doc) else [])


def page_resources_drop(doc, page, key):
    """Remove one entry (e.g. b"XObject/I1") from the page's resources, which may be a
    direct dictionary or a shared object, with the sub-dictionary direct or shared too."""
    group, name = key.decode().split("/")
    kind, val = doc.xref_get_key(page.xref, "Resources")
    if kind == "xref":
        owner, prefix = int(val.split()[0]), ""
    elif kind == "dict":
        owner, prefix = page.xref, "Resources/"
    else:
        return                           # inherited resources: leave them alone
    kind, val = doc.xref_get_key(owner, prefix + group)
    if kind == "xref":
        doc.xref_set_key(int(val.split()[0]), name, "null")
    elif kind == "dict":
        doc.xref_set_key(owner, prefix + group + "/" + name, "null")


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
    for page in doc:                     # the dynamicpapers header block
        if dp_marked(page):
            xrefs = page.get_contents()
            content = DP_HEADER.sub(b"", page.read_contents())
            doc.update_stream(xrefs[0], content)
            for x in xrefs[1:]:
                doc.update_stream(x, b"")
    for page in doc:                     # FPDF copies: the original page alone, at full size
        if fpdf_marked(page):
            content = page.read_contents()
            tpl = FPDF_TPL.search(content).group(1)
            for name in set(FPDF_LOGO.findall(content)):
                page_resources_drop(doc, page, b"XObject/" + name)
            xrefs = page.get_contents()
            doc.update_stream(xrefs[0], b"q\n/" + tpl + b" Do\nQ\n")
            for x in xrefs[1:]:
                doc.update_stream(x, b"")
    for page in doc:                     # links to the sites
        links = site_links(page)
        if any(not l["xref"] for l in links):
            # inline link dictionaries (FPDF) cannot be deleted one by one
            if len(links) < len(page.get_links()) or page.first_annot:
                return f"unexpected annotations on page {page.number + 1}"
            doc.xref_set_key(page.xref, "Annots", "null")
            continue
        for link in links:
            page.delete_link(link)
    keys, xmp = site_meta(doc)           # document properties naming a site
    if keys:
        doc.set_metadata({k: v for k, v in doc.metadata.items()
                          if k not in keys and k not in ("format", "encryption") and v})
    if xmp:
        doc.del_xml_metadata()
    for page in doc:                     # watermark objects still listed but no longer drawn
        for name in leftover(page):
            page_resources_drop(doc, page, b"XObject/" + name.encode())
    for page in doc:                     # re-assembled pages keep the banner line: redact its text
        rects = banner(page)
        for r in rects:
            page.add_redact_annot(r + (-1, -1, 1, 1))
        if rects:
            page.apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_NONE, graphics=pymupdf.PDF_REDACT_LINE_ART_NONE)
    left = visible(doc)
    if left:
        return f"marks left on pages {left}"
    tmp = path + ".tmp"
    doc.save(tmp, garbage=4, deflate=True)
    doc.close()
    os.replace(tmp, path)
    return "stripped"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("where", nargs="+")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    where = a.where
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
                res = "marked" if visible(d) else "clean"
        else:
            res = strip(f)
        counts[res] = counts.get(res, 0) + 1
        if res not in ("clean",):
            print(f"{res:20} {f}")
    print(counts)


if __name__ == "__main__":
    main()
