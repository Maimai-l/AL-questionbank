#!/usr/bin/env python3
"""Export the bank as CSV, for a conversation with Claude to look things up in.

    python3 -m pipeline.export.export_project [--out DIR]

Writes to exports/ (paths.EXPORTS):

  questions.csv              one row per question: where it comes from, marks,
                             topic, the question and its mark scheme as text
                             (the OCR LaTeX where there is one, else the PDF
                             text layer), the answer and options for the
                             multiple-choice exams, and the crop's path.
  image-only-questions.csv   questions whose text cannot stand in for the crop
                             (q_quality missing, garbled or partial): in a
                             text-only setting these need the image.

UTF-8 with a byte-order mark, so a spreadsheet opens the Chinese and the maths
correctly.
"""
import argparse, csv, os, sqlite3, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))
from lib import paths  # noqa: E402

COLUMNS = [
    ("id", "id"), ("syllabus", "syllabus"), ("component", "component"),
    ("component_name", "component_name"), ("paper", "paper"), ("session", "session"),
    ("year", "year"), ("q", "q"), ("marks", "marks"), ("marks_parts", "marks_parts"),
    ("topic", "topic"), ("topic_name", "topic_name"), ("subtopic", "subtopic"),
    ("subtopic_name", "subtopic_name"), ("topic_source", "topic_source"),
    ("qtype", "qtype"), ("options", "options"), ("answer", "answer"),
    ("question", "COALESCE(question_latex, question_text)"),
    ("mark_scheme", "COALESCE(ms_latex, ms_text)"),
    ("ms_total", "ms_total"), ("totals_agree", "totals_agree"),
    ("q_quality", "q_quality"), ("ms_quality", "ms_quality"),
    ("has_diagram", "has_diagram"), ("image", "image"),
]
IMAGE_ONLY = ("missing", "garbled", "partial")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=paths.EXPORTS)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)

    con = sqlite3.connect(paths.DB)
    sql = ", ".join(f"{expr} AS {name}" for name, expr in COLUMNS)
    rows = con.execute(f"SELECT {sql} FROM questions ORDER BY syllabus, year, "
                       "paper, session, q").fetchall()
    names = [n for n, _ in COLUMNS]

    main_csv = os.path.join(a.out, "questions.csv")
    with open(main_csv, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(names)
        w.writerows(rows)

    qi = names.index("q_quality")
    only = [r for r in rows if r[qi] in IMAGE_ONLY]
    img_csv = os.path.join(a.out, "image-only-questions.csv")
    with open(img_csv, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["id", "syllabus", "session", "q", "q_quality", "image"])
        for r in only:
            d = dict(zip(names, r))
            w.writerow([d["id"], d["syllabus"], d["session"], d["q"], d["q_quality"],
                        d["image"]])

    print(f"{len(rows)} 题 -> {main_csv}")
    print(f"{len(only)} 题只能看原题图 -> {img_csv}")


if __name__ == "__main__":
    main()
