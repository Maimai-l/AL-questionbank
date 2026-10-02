#!/usr/bin/env python3
"""Add the OCR'd mark schemes to the bank as `ms_latex`.

Mirrors the question_latex / question_text split: the pdftotext version stays
(it is what the mark-code and total extraction was validated against, and it
tokenises well for full-text search), while `ms_latex` carries the readable
version with the mathematics intact.

Each scheme goes through the step-8 chain (glyphs -> line breaks -> tables)
here, and the rows written are graded as flag_quality.py grades them (an OCR
scheme that reads worse than the text layer is not kept). Running the step-8
scripts over the whole table afterwards would also convert rows that never
went through OCR: html_tables.py takes "<p<1" in a pdftotext ms_text
(9709_s21_53_q07) for a tag.
"""
import json, os, re, sqlite3, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))
from pipeline.text.audit_text import classify_ms  # noqa: E402
from pipeline.text.clean_encoding import clean  # noqa: E402
from pipeline.text.fix_newlines import unescape  # noqa: E402
from pipeline.text.flag_quality import RANK  # noqa: E402
from pipeline.text.html_tables import convert  # noqa: E402


def normalise(t):
    return convert(unescape(clean(t)[0])[0])[0]


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
        rows.append((normalise(r["ms_ocr"]), qid))
    con.executemany("UPDATE questions SET ms_latex=? WHERE id=?", rows)

    dropped = 0
    for t, qid in rows:
        syl, mt = con.execute("SELECT syllabus, ms_text FROM questions WHERE id=?",
                              (qid,)).fetchone()
        maths = syl in ("9709", "9231")
        gl = classify_ms(t, maths) if t else "missing"
        gt = classify_ms(mt, maths) if mt else "missing"
        if RANK[gl] > RANK[gt]:
            con.execute("UPDATE questions SET ms_latex=NULL, ms_quality=? WHERE id=?",
                        (gt, qid))
            dropped += 1
        else:
            con.execute("UPDATE questions SET ms_quality=? WHERE id=?", (gl, qid))
    print(f"{dropped} 题的 OCR 评分细则不如文本层,未保留")

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
