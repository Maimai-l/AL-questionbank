#!/usr/bin/env python3
"""Grade every text field and record the verdict in the database.

Run this after `combine.py` — combining rebuilds the table from the per-subject
databases, so any column added afterwards is lost.

For Computer Science the PDF text layer is already clean prose, and OCR can
actually flatten its tables for the worse, so the two versions are compared and
the weaker one is dropped rather than blindly preferring the OCR.
"""
import sqlite3, sys

sys.path.insert(0, __file__.rsplit("/", 1)[0] if "/" in __file__ else ".")
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))          # 项目根目录
from lib import paths
from pipeline.text.audit_text import classify_q, classify_ms

RANK = {"ok": 0, "degraded": 1, "severe": 2, "garbled": 2, "missing": 3}


def main(dbpath):
    con = sqlite3.connect(dbpath)
    cols = {r[1] for r in con.execute("PRAGMA table_info(questions)")}
    for n in ("q_quality", "ms_quality"):
        if n not in cols:
            con.execute(f"ALTER TABLE questions ADD COLUMN {n} TEXT")

    rows = con.execute("SELECT id, syllabus, question_latex, ms_latex, ms_text "
                       "FROM questions").fetchall()
    upd, dropped = [], 0
    for qid, syl, ql, ml, mt in rows:
        maths = syl in ("9709", "9231")
        gl = classify_ms(ml, maths) if ml else "missing"
        gt = classify_ms(mt, maths) if mt else "missing"
        if ml and RANK[gl] > RANK[gt]:
            # the OCR is worse than the text layer here — do not surface it
            con.execute("UPDATE questions SET ms_latex=NULL WHERE id=?", (qid,))
            ml, gl, dropped = None, "missing", dropped + 1
        best = gl if ml else gt
        upd.append((classify_q(ql), best, qid))
    con.executemany("UPDATE questions SET q_quality=?, ms_quality=? WHERE id=?", upd)
    con.commit()

    print(f"graded {len(upd)} questions; dropped {dropped} OCR mark schemes "
          f"that scored worse than the text layer")
    for label, col in (("题干", "q_quality"), ("Mark scheme", "ms_quality")):
        print(f"  {label}:")
        for r in con.execute(f"SELECT syllabus, {col}, COUNT(*) FROM questions "
                             f"GROUP BY syllabus, {col} ORDER BY syllabus"):
            print(f"    {r[0]} {r[1]:<10} {r[2]}")
    con.close()


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else paths.DB)
