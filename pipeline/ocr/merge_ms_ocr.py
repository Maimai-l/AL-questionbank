#!/usr/bin/env python3
"""Add the OCR'd mark schemes to the bank as `ms_latex`.

Mirrors the question_latex / question_text split: the pdftotext version stays
(it is what the mark-code and total extraction was validated against, and it
tokenises well for full-text search), while `ms_latex` carries the readable
version with the mathematics intact.
"""
import json, re, sqlite3, sys


def main(parsed, dbpath):
    R = json.load(open(parsed))
    con = sqlite3.connect(dbpath)
    cols = {r[1] for r in con.execute("PRAGMA table_info(questions)")}
    if "ms_latex" not in cols:
        con.execute("ALTER TABLE questions ADD COLUMN ms_latex TEXT")

    ids = {r[0] for r in con.execute("SELECT id FROM questions")}
    rows, missing = [], 0
    for r in R:
        qid = (f"{r['subject']}_{r['series']}_{r['component']}{r['variant']}"
               f"_q{r['q']:02d}")
        if qid not in ids:
            missing += 1
            continue
        rows.append((r["ms_ocr"], qid))
    con.executemany("UPDATE questions SET ms_latex=? WHERE id=?", rows)

    # let the readable version be searchable too, stripped of LaTeX punctuation
    con.executemany(
        "UPDATE q_fts SET ms_text = ms_text || ' ' || ? WHERE id = ?",
        [(re.sub(r"[\\${}|]", " ", t), q) for t, q in rows])
    con.commit()

    n = con.execute("SELECT COUNT(*) FROM questions WHERE ms_latex IS NOT NULL").fetchone()[0]
    print(f"ms_latex on {n} questions ({len(rows)} written, {missing} unmatched)")
    for r in con.execute(
            "SELECT syllabus, SUM(ms_latex IS NOT NULL), SUM(ms_text IS NOT NULL), "
            "COUNT(*) FROM questions GROUP BY syllabus ORDER BY syllabus"):
        print(f"  {r[0]}: ms_latex {r[1]:>4} | ms_text {r[2]:>4} | total {r[3]:>4}")
    con.close()


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
