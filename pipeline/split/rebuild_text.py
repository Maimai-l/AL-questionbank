#!/usr/bin/env python3
"""Bring the CAIE rows of the bank in line with the current split.

    python3 pipeline/split/rebuild_text.py [raw/pdf] [--write]

The crops are re-rendered by crop.py; this does the same for what the database
says about each question, without rebuilding the table (combine.py would drop
the OCR, the tags and the quality flags). Per question:

  question_text   the splitter's text, through clean_encoding.clean() as in
                  step 8 of the pipeline. The old text kept "BLANK PAGE" and
                  lost lines the barcode filter mistook for glyph soup.
  marks, marks_parts, totals_agree
                  from the tariffs the splitter reads (9618_s24_13_q07: 19 -> 22,
                  which is what the mark scheme totals).
  answer space    dotted and ruled answer lines are dropped from both texts
                  (pipeline/text/answer_lines.py).
  question_latex  cut at the first piece of end matter. The OCR was run on the
                  old crops, which ran on through "Additional page", "BLANK
                  PAGE" and the copyright block; everything after that point is
                  never part of the question.

Dry run by default: prints what would change. q_fts is rebuilt on --write.
"""
import argparse, json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))
from lib import db, paths  # noqa: E402
from pipeline.split import crop, split_qp  # noqa: E402
from pipeline.text.clean_encoding import clean  # noqa: E402
from pipeline.text.answer_lines import strip as strip_answer_lines  # noqa: E402

END_MATTER = re.compile(
    r"(?:^|\n)[#|\s]*(?:BLANK PAGE|Additional page|If you use the following|"
    r"Permission to reproduce|To avoid the issue of disclosure|"
    r"Cambridge Assessment International Education is part of)", re.I)
# what the OCR read off the page foot just above the end matter: a page
# number ("17") or a barcode crumb ("1J", "1V")
CRUMB = re.compile(r"\n+\s*(?:\d{1,2}|\d[A-Z])\s*$")


def cut_end_matter(t):
    if not t:
        return t
    m = END_MATTER.search(t)
    if not m:
        return t
    t = t[:m.start()].rstrip()
    while CRUMB.search(t):
        t = CRUMB.sub("", t).rstrip()
    return t


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdfdir", nargs="?", default=os.path.join(paths.RAW, "pdf"))
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()

    split = {}
    for f in sorted(os.listdir(a.pdfdir)):
        if "_qp_" in f:
            for q in split_qp.split_paper(os.path.join(a.pdfdir, f)):
                split[crop.qid(q)] = q

    con = db.connect()
    rows = con.execute(
        "SELECT id, question_text, question_latex, marks, marks_parts, ms_total, "
        "totals_agree FROM questions WHERE syllabus IN ('9709','9231','9618')").fetchall()
    missing = [r["id"] for r in rows if r["id"] not in split]
    if missing:
        sys.exit(f"{len(missing)} 题在 {a.pdfdir} 中找不到试卷,例如 {missing[:3]}")

    upd, n_text, n_latex, marks_changed = [], 0, 0, []
    for r in rows:
        q = split[r["id"]]
        text = strip_answer_lines(clean(q["text"])[0])
        latex = strip_answer_lines(cut_end_matter(r["question_latex"]))
        marks, mp = q["marks"], json.dumps(q["marks_parts"])
        agree = (int(marks == r["ms_total"]) if marks is not None and r["ms_total"] is not None
                 else r["totals_agree"])
        n_text += text != r["question_text"]
        n_latex += latex != r["question_latex"]
        if marks != r["marks"] or mp != r["marks_parts"]:
            marks_changed.append(f"{r['id']}: {r['marks']} {r['marks_parts']} -> "
                                 f"{marks} {mp}(评分细则 {r['ms_total']})")
        if (text, latex, marks, mp, agree) != (r["question_text"], r["question_latex"],
                                               r["marks"], r["marks_parts"], r["totals_agree"]):
            upd.append((text, latex, marks, mp, agree, r["id"]))

    print(f"{len(rows)} 题;将改动 {len(upd)} 题:question_text {n_text},"
          f"question_latex {n_latex},分值 {len(marks_changed)}")
    for m in marks_changed:
        print("  " + m)
    left = con.execute("SELECT COUNT(*) FROM questions WHERE syllabus IN "
                       "('9709','9231','9618') AND question_text LIKE '%BLANK PAGE%'").fetchone()[0]
    print(f"改动前 question_text 含 BLANK PAGE 的题:{left}")
    if not a.write:
        print("(dry run;加 --write 写入)")
        return
    con.executemany("UPDATE questions SET question_text=?, question_latex=?, marks=?, "
                    "marks_parts=?, totals_agree=? WHERE id=?", upd)
    con.execute("DELETE FROM q_fts")
    con.execute("INSERT INTO q_fts(id,question_text,ms_text,topic_name) SELECT id, "
                "COALESCE(question_latex,question_text), COALESCE(ms_latex,ms_text), "
                "topic_name FROM questions")
    con.commit()
    for col in ("question_text", "question_latex"):
        n = con.execute(f"SELECT COUNT(*) FROM questions WHERE {col} LIKE '%BLANK PAGE%'").fetchone()[0]
        print(f"写入后 {col} 含 BLANK PAGE:{n}")


if __name__ == "__main__":
    main()
