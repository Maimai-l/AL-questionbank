#!/usr/bin/env python3
"""Check every admissions crop against the page furniture, without looking at
a single image. The admissions counterpart of pipeline/split/audit_crops.py.

    python3 pipeline/admissions_rebuild/audit_adm_imgs.py [TSA|BMAT|TMUA]

For each question: the clips render_adm_imgs.py would render, and for each
clip every piece of furniture inside it must come out white once rendered.
Also reported: questions whose number could not be located (rendered from
the page band instead of from their own position), and question-page content
that no question's clip contains.
"""
import collections, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))
import pymupdf as fitz  # noqa: E402

import render_adm_imgs as R  # noqa: E402
from pipeline.split import furniture  # noqa: E402

TOL = 2.0


def ink_left(page, clip, r):
    pix = page.get_pixmap(matrix=fitz.Matrix(R.ZOOM, R.ZOOM), colorspace=fitz.csGRAY, clip=clip)
    R.whiteout(pix, clip, R.page_furniture(page))
    rr = fitz.Rect(r) & clip
    x0, y0 = int((rr.x0 - clip.x0) * R.ZOOM), int((rr.y0 - clip.y0) * R.ZOOM)
    x1, y1 = int((rr.x1 - clip.x0) * R.ZOOM), int((rr.y1 - clip.y0) * R.ZOOM)
    for y in range(max(y0, 0), min(y1, pix.height)):
        for x in range(max(x0, 0), min(x1, pix.width)):
            if pix.pixel(x, y)[0] < 245:       # 浅灰残痕也算:trim 以 245 为界判断空白
                return True
    return False


def material(page):
    furn = [r for _k, r in R.page_furniture(page)]
    out = []
    for txt, r, _h in furniture.lines(page):
        if any((r & f).get_area() > 0.5 * max(r.get_area(), 1e-6) for f in furn):
            continue
        out.append((R.readable(txt)[:40], r))
    return out


def audit(only=None):
    qs = json.load(open(R.QUESTIONS))
    if only:
        qs = [q for q in qs if q["exam"] == only]
    hits = collections.defaultdict(list)
    by_doc = collections.defaultdict(list)
    for q in qs:
        by_doc[R.pdf_path(q)].append(q)
    for path, group in by_doc.items():
        doc = fitz.open(path)
        mats = R.material_pages(doc)
        # 题号序列:每题都要定位到,且按阅读顺序递增。缺一个,上一题就会把它整个裹进去
        H = R.doc_headers(doc)
        want = {q["q"] for q in group}
        order = [H[k] for k in sorted(H)]
        for n in sorted(want - set(H)):
            hits["header-missing"].append(f"{os.path.basename(path)} q{n}")
        if any(order[i] >= order[i + 1] for i in range(len(order) - 1)):
            hits["header-order"].append(os.path.basename(path))
        page_clips = collections.defaultdict(list)
        for q in group:
            qid = R.qid(q)
            lay = R.layout(doc, q)
            if all(t is None and b is None for _i, t, b in lay):
                hits["whole-page"].append(qid)
            kinds = set()
            own_pages = {i for i, _t, _b in lay}
            for i, clip in R.clips(doc, R.parts_of(q, doc, mats, lay)):
                page_clips[i].append(clip)
                # 本题的裁图里不得出现别题的题号(材料页除外:材料页上本就印着一组题号)
                if i in own_pages:
                    for m, (pg, y) in H.items():
                        if m != q["q"] and pg == i and clip.y0 + 2 < y < clip.y1 - 2:
                            kinds.add("left:other-question")
                for k, r in R.page_furniture(doc[i]):
                    if (fitz.Rect(r) & clip).get_area() > 0.5 or (fitz.Rect(r) & clip).width > 0 and r.height < 1:
                        kinds.add(("left:" if ink_left(doc[i], clip, r) else "whited:") + k)
            for k in kinds:
                hits[k].append(qid)
            if not [k for k in kinds if k.startswith("left:")]:
                hits["clean"].append(qid)
        for i, cl in page_clips.items():
            for label, r in material(doc[i]):
                core = fitz.Rect(r.x0 + TOL, r.y0 + TOL, r.x1 - TOL, r.y1 - TOL) \
                    if r.width > 2 * TOL and r.height > 2 * TOL else r
                if not any(core in c for c in cl):
                    hits["uncovered"].append(f"{os.path.basename(path)} p{i} {[round(v) for v in r]} {label!r}")
        doc.close()
    return len(qs), hits


if __name__ == "__main__":
    n, hits = audit(sys.argv[1] if len(sys.argv) > 1 else None)
    print(f"questions: {n}")
    for k in sorted(hits, key=lambda k: -len(hits[k])):
        c = collections.Counter(h.split("-")[0] for h in hits[k])
        print(f"  {k:16} {len(hits[k]):5}   " + "  ".join(f"{s}={v}" for s, v in sorted(c.items())))
    for k in hits:
        if k.startswith("left:") or k in ("uncovered", "header-missing", "header-order"):
            print(f"\n{k}:", *hits[k][:12], sep="\n  ")
