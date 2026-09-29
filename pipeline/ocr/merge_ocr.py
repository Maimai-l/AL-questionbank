#!/usr/bin/env python3
"""Fold the PaddleOCR-VL results into the question bank.

Adds `question_latex` (proper LaTeX) alongside the original lossy
`question_text`, plus a `has_diagram` flag. The lossy text is kept because the
FTS index tokenises it better than LaTeX does — searching for "volume of
revolution" should not have to step around \\frac{}{}.
"""
import json, re, sqlite3, sys

MIN_LEN = 12          # shorter than this and the OCR clearly failed


def load_cache(path):
    out = {}
    for ln in open(path):
        try:
            d = json.loads(ln)
        except Exception:
            continue
        if d.get("latex") and len(d["latex"]) >= MIN_LEN:
            out[d["id"]] = d
    return out


def main(cache, dbpath):
    got = load_cache(cache)
    con = sqlite3.connect(dbpath)
    cols = {r[1] for r in con.execute("PRAGMA table_info(questions)")}
    if "question_latex" not in cols:
        con.execute("ALTER TABLE questions ADD COLUMN question_latex TEXT")
    if "has_diagram" not in cols:
        con.execute("ALTER TABLE questions ADD COLUMN has_diagram INTEGER")

    ids = {r[0] for r in con.execute("SELECT id FROM questions")}
    rows = [(d["latex"], int(bool(d.get("has_diagram"))), qid)
            for qid, d in got.items() if qid in ids]
    con.executemany(
        "UPDATE questions SET question_latex=?, has_diagram=? WHERE id=?", rows)

    # keep the plain text in FTS (better tokenisation) but let LaTeX be searched too
    con.executemany(
        "UPDATE q_fts SET question_text = question_text || ' ' || ? WHERE id = ?",
        [(re.sub(r"[\\${}]", " ", d["latex"]), qid)
         for qid, d in got.items() if qid in ids])
    con.commit()

    n = con.execute("SELECT COUNT(*) FROM questions WHERE question_latex IS NOT NULL").fetchone()[0]
    tot = con.execute("SELECT COUNT(*) FROM questions").fetchone()[0]
    dia = con.execute("SELECT COUNT(*) FROM questions WHERE has_diagram=1").fetchone()[0]
    print(f"question_latex on {n}/{tot} questions;  {dia} carry a diagram")
    for r in con.execute(
            "SELECT component_name, COUNT(*), SUM(has_diagram) FROM questions "
            "WHERE question_latex IS NOT NULL GROUP BY component ORDER BY component"):
        print(f"  {r[0]:<28} {r[1]:>4} with LaTeX, {r[2]:>3} with diagram")
    con.close()


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
