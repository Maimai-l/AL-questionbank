#!/usr/bin/env python3
"""Re-render the crops of the CAIE questions already in the database, after a
change to split_qp.py's span rules or to crop.py.

    python3 pipeline/split/recrop.py [--rows] [--out DIR] [--jobs 4] [PAPER ...]

Each question paper in raw/pdf/ is split again and every question whose id is
in data/caie.db is rendered under data/ (or under --out, to compare first).
Only the images change: text, marks and parts in the database stay as they are.
PAPER limits the run to those files (9709_s23_qp_12.pdf).

Without --rows: the question crops, img<syllabus>/<id>.png.
With --rows: the answer-space crops for the writing board,
img<syllabus>_ans/<id>.png (lib/paths.answer_space). One that comes out the
same as the question crop in data/ is not kept, so the folder holds only the
questions whose question crop leaves answer rows out; run without --rows first.
"""
import argparse, glob, os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))
import pymupdf as fitz  # noqa: E402

from lib import db, paths  # noqa: E402
from pipeline.split import crop, split_qp  # noqa: E402

IDS, OUT, ROWS = set(), paths.DATA, False


def height(path):
    try:
        return fitz.Pixmap(path).height
    except Exception:
        return None


def one(path):
    try:
        qs = split_qp.split_paper(path)
    except Exception as e:
        return [("error", os.path.basename(path), str(e), None, None)]
    out = []
    for q in qs:
        qid = crop.qid(q)
        if qid not in IDS:
            continue
        rel = f"img{qid.split('_')[0]}/{qid}.png"
        target = paths.answer_space_rel(rel) if ROWS else rel
        d = os.path.dirname(os.path.join(OUT, target))
        os.makedirs(d, exist_ok=True)
        old = os.path.join(paths.DATA, rel)
        try:
            if ROWS:
                name = crop.render_rows(q, os.path.dirname(path), d, old)
                out.append(("ok", qid, name or "-", None, None, name is None))
                continue
            name = crop.render(q, os.path.dirname(path), d)
        except Exception as e:
            out.append(("error", qid, str(e), None, None))
            continue
        new = os.path.join(d, name) if name else None
        out.append(("ok", qid, name, height(old), height(new) if new else None,
                    bool(new) and crop.same_image(old, new)))
    return out


def init(ids, out, rows):
    global IDS, OUT, ROWS
    IDS, OUT, ROWS = ids, out, rows


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("papers", nargs="*")
    ap.add_argument("--rows", action="store_true", help="answer-space crops (img*_ans/)")
    ap.add_argument("--out", default=paths.DATA)
    ap.add_argument("--jobs", type=int, default=4)
    a = ap.parse_args()
    ids = {r[0] for r in db.connect().execute(
        "SELECT id FROM questions WHERE syllabus IN ('9709', '9231', '9618')")}
    pdfdir = os.path.join(paths.RAW, "pdf")
    files = [os.path.join(pdfdir, p) for p in a.papers] or \
        sorted(glob.glob(os.path.join(pdfdir, "*_qp_*.pdf")))
    from multiprocessing import Pool
    with Pool(a.jobs, initializer=init, initargs=(ids, a.out, a.rows)) as pool:
        rows = [r for rs in pool.imap_unordered(one, files) for r in rs]
    ok = [r for r in rows if r[0] == "ok" and r[2]]
    errors = [r for r in rows if r[0] == "error" or not r[2]]
    if a.rows:
        kept = [r for r in ok if not r[5]]
        print(f"{len(ok)} 题 -> {a.out};保存带答题区的图 {len(kept)},"
              f"与题图相同未保存 {len(ok) - len(kept)},失败 {len(errors)}")
    else:
        changed = [r for r in ok if not r[5]]
        print(f"{len(ok)} 张 -> {a.out};与原图不同 {len(changed)},失败 {len(errors)}")
        for r in changed[:20]:
            print("  不同", r[1], r[3], "->", r[4])
    for r in errors[:20]:
        print("  失败", r[1], r[2])
    if not a.papers:
        missed = sorted(ids - {r[1] for r in ok})
        print(f"库中有、未重新生成 {len(missed)}", missed[:20])


if __name__ == "__main__":
    main()
