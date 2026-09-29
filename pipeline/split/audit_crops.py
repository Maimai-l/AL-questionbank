#!/usr/bin/env python3
"""Check every question crop against the page furniture, without looking at
a single image.

Checks: furniture inside a clip, slack below the last line, question material
that no clip covers or that a clip boundary cuts, and clips of two questions
overlapping on one page.

    python3 pipeline/split/audit_crops.py raw/pdf [--crop old|new] [--list KIND]

For each question paper in the folder the splitter produces the spans, the
cropper turns each span into a clip rectangle, and the clip is intersected with
the furniture that furniture.py finds on that page. A clean crop intersects
nothing. The report counts offending questions per furniture kind, so a change
to the cropper can be judged by the numbers before any image is rendered.

--crop old   the clip rule of the original crop.py (full width, span as given)
--crop new   the clip rule of the rewritten crop.py
"""
import argparse, collections, os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))
import pymupdf as fitz  # noqa: E402

from pipeline.split import crop, furniture, split_qp  # noqa: E402

MIN_OVERLAP = 0.5   # pt²; a shared edge is not an overlap
SLACK = 30          # pt of blank space allowed below the last line of a crop


def old_clips(q, doc):
    for sp in q["spans"]:
        page = doc[sp["page"]]
        clip = fitz.Rect(crop.PAD_X_OLD, sp["y0"], page.rect.width - crop.PAD_X_OLD, sp["y1"])
        if clip.height >= 8:
            yield sp["page"], clip


def new_clips(q, doc):
    for p, clip in crop.clips(q, doc):
        yield p, clip


def still_white(page, clip, r):
    """Render the clip as crop.render does and confirm no ink is left inside r."""
    pix = crop.whiteout(page.get_pixmap(matrix=fitz.Matrix(crop.ZOOM, crop.ZOOM),
                                        clip=clip, alpha=False), page, clip)
    rr = fitz.Rect(r) & clip
    x0, y0 = int((rr.x0 - clip.x0) * crop.ZOOM), int((rr.y0 - clip.y0) * crop.ZOOM)
    x1, y1 = int((rr.x1 - clip.x0) * crop.ZOOM), int((rr.y1 - clip.y0) * crop.ZOOM)
    for y in range(max(y0, 0), min(y1, pix.height)):
        for x in range(max(x0, 0), min(x1, pix.width)):
            if pix.pixel(x, y)[0] < 128:
                return False
    return True


def audit(pdfdir, which, only=None):
    clips_of = old_clips if which == "old" else new_clips
    hits = collections.defaultdict(list)       # kind -> [question id]
    n = 0
    for f in sorted(os.listdir(pdfdir)):
        if "_qp_" not in f or (only and not f.startswith(only)):
            continue
        path = os.path.join(pdfdir, f)
        doc = fitz.open(path)
        cache = {}
        page_clips = collections.defaultdict(list)   # page -> [(qid, clip)]
        for q in split_qp.split_paper(path):
            n += 1
            qid = crop.qid(q)
            kinds = set()
            for p, clip in clips_of(q, doc):
                page_clips[p].append((qid, clip))
                if p not in cache:
                    cache[p] = furniture.furniture(doc[p])
                for kind, r in cache[p]:
                    inter = fitz.Rect(clip) & r
                    if not inter.is_empty and inter.get_area() > MIN_OVERLAP:
                        # the new cropper paints furniture inside the clip white;
                        # record it separately, and check the pixels really are white
                        if which == "old":
                            kinds.add(kind)
                        else:
                            kinds.add("whited:" + kind if still_white(doc[p], clip, r)
                                      else "whiteout-failed:" + kind)
            # slack: blank space below the last piece of material in the last
            # clip. A crop that runs on to the footer because something invisible
            # anchored it shows up here and nowhere else.
            cl = list(clips_of(q, doc))
            if cl:
                p, c = cl[-1]
                if p not in cache:
                    cache[p] = furniture.furniture(doc[p])
                boxes = [r for _, r in crop.material(doc[p], cache[p])]
                boxes += [r for t, r, _ in furniture.lines(doc[p])          # answer lines count here
                          if set(t.replace(" ", "")) <= crop.DOTS]
                ys = [r.y1 for r in boxes if (r & c).get_area() > 0 or r in c]
                if ys and c.y1 - max(ys) > SLACK:
                    kinds.add("slack")
            for k in kinds:
                hits[k].append(qid)
            if not [k for k in kinds if not k.startswith("whited:")]:
                hits["clean"].append(qid)
        # overlap: two questions' clips on one page must not share any area.
        # A question whose first line is set higher than its number (a built-up
        # fraction) used to leave that line in the previous question's crop;
        # 90 pairs, invisible to every other check here.
        # The 6pt pad above a question's first line may meet the previous
        # clip; only shared area that holds question material counts.
        for p, lst in page_clips.items():
            mat = None
            for i, (qa, ca) in enumerate(lst):
                for qb, cb in lst[i + 1:]:
                    both = fitz.Rect(ca) & cb
                    if qa == qb or both.get_area() <= MIN_OVERLAP:
                        continue
                    if mat is None:
                        items = cache.get(p) or furniture.furniture(doc[p])
                        mat = [r for _, r in crop.material(doc[p], items)]
                    if any((both & r).get_area() > MIN_OVERLAP for r in mat):
                        hits["overlap"].append(f"{qa}  {qb}  p{p}")
        # content check: every piece of question material on a question page
        # must sit wholly inside one clip
        pages = sorted(page_clips)
        first = min(page_clips.get(pages[0], [(None, fitz.Rect())]), key=lambda t: t[1].y0)[1] if pages else None
        for p in range(pages[0], pages[-1] + 1) if pages else []:
            page = doc[p]
            items = cache.get(p) or furniture.furniture(page)
            if furniture.is_blank(page, items):
                continue
            for label, r in crop.material(page, items):
                if p == pages[0] and r.y1 <= first.y0:
                    continue            # instructions above question 1
                core = fitz.Rect(r)
                if core.width > 2 * crop.TOL:
                    core.x0, core.x1 = core.x0 + crop.TOL, core.x1 - crop.TOL
                if core.height > 2 * crop.TOL:
                    core.y0, core.y1 = core.y0 + crop.TOL, core.y1 - crop.TOL
                inside = [q for q, c in page_clips[p] if core in c + (-0.3, -0.3, 0.3, 0.3)]
                if inside:
                    continue
                touch = [q for q, c in page_clips[p] if (fitz.Rect(r) & c).get_area() > MIN_OVERLAP]
                if touch:
                    hits["cut"].append(f"{touch[0]}  p{p} {[round(v) for v in r]} {label!r}")
                else:
                    stem = f[:-4]
                    hits["uncovered"].append(f"{stem}  p{p} {[round(v) for v in r]} {label!r}")
        doc.close()
    return n, hits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdfdir")
    ap.add_argument("--crop", choices=["old", "new"], default="new")
    ap.add_argument("--only", help="filename prefix, e.g. 9709_s25")
    ap.add_argument("--list", help="print the question ids for this kind")
    a = ap.parse_args()
    n, hits = audit(a.pdfdir, a.crop, a.only)
    print(f"crop rule: {a.crop}   questions: {n}   "
          "(cut/uncovered: number of content items; per-subject: questions or papers)")
    for k in sorted(hits, key=lambda k: -len(hits[k])):
        by_subj = collections.Counter(q.split("_")[0] for q in hits[k])
        if k in ("cut", "uncovered", "overlap"):
            by_subj = collections.Counter(q.split("_")[0] for q in set(h.split("  ")[0] for h in hits[k]))
        print(f"  {k:10} {len(hits[k]):5}   " +
              "  ".join(f"{s}={c}" for s, c in sorted(by_subj.items())))
    if a.list:
        print("\n".join(hits.get(a.list, [])))


if __name__ == "__main__":
    main()
