#!/usr/bin/env python3
"""Re-render the crops of the CAIE questions already in the database, after a
change to split_qp.py's span rules or to crop.py.

    python3 pipeline/split/recrop.py [--out DIR] [--jobs 4] [PAPER ...]

Each question paper in raw/pdf/ is split again and every question whose id is
in data/caie.db is rendered to img<syllabus>/<id>.png under data/ (or under
--out, to compare first). Only the images change: text, marks and parts in
the database stay as they are. PAPER limits the run to those files
(9709_s23_qp_12.pdf). Prints how many images changed height.
"""
import argparse, glob, os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))
import pymupdf as fitz  # noqa: E402

from lib import db, paths  # noqa: E402
from pipeline.split import crop, split_qp  # noqa: E402

IDS, OUT = set(), paths.DATA


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
        d = os.path.join(OUT, "img" + qid.split("_")[0])
        os.makedirs(d, exist_ok=True)
        before = height(os.path.join(paths.DATA, "img" + qid.split("_")[0], qid + ".png"))
        try:
            name = crop.render(q, os.path.dirname(path), d)
        except Exception as e:
            out.append(("error", qid, str(e), None, None))
            continue
        out.append(("ok", qid, name, before, height(os.path.join(d, name)) if name else None))
    return out


def init(ids, out):
    global IDS, OUT
    IDS, OUT = ids, out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("papers", nargs="*")
    ap.add_argument("--out", default=paths.DATA)
    ap.add_argument("--jobs", type=int, default=4)
    a = ap.parse_args()
    ids = {r[0] for r in db.connect().execute(
        "SELECT id FROM questions WHERE syllabus IN ('9709', '9231', '9618')")}
    pdfdir = os.path.join(paths.RAW, "pdf")
    files = [os.path.join(pdfdir, p) for p in a.papers] or \
        sorted(glob.glob(os.path.join(pdfdir, "*_qp_*.pdf")))
    from multiprocessing import Pool
    with Pool(a.jobs, initializer=init, initargs=(ids, a.out)) as pool:
        rows = [r for rs in pool.imap_unordered(one, files) for r in rs]
    ok = [r for r in rows if r[0] == "ok" and r[2]]
    errors = [r for r in rows if r[0] == "error" or not r[2]]
    taller = [r for r in ok if r[3] and r[4] and r[4] > r[3]]
    shorter = [r for r in ok if r[3] and r[4] and r[4] < r[3]]
    print(f"{len(ok)} 张 -> {a.out};变高 {len(taller)},变矮 {len(shorter)},"
          f"失败 {len(errors)}")
    for r in errors[:20]:
        print("  失败", r[1], r[2])
    for r in shorter[:20]:
        print("  变矮", r[1], r[3], "->", r[4])
    if not a.papers:
        missed = sorted(ids - {r[1] for r in ok})
        print(f"库中有、未重新生成 {len(missed)}", missed[:20])


if __name__ == "__main__":
    main()
