#!/usr/bin/env python3
"""Merge the per-subject databases into one bank.

  combine.py caie.db 9709.db 9231.db 9618.db

One file is far more useful than three: a single MCP tool call can then ask
for "8-mark questions on recursion" without the caller having to know which
syllabus owns the topic.
"""
import os, sqlite3, sys


def main(out, sources):
    if os.path.exists(out):
        os.remove(out)
    con = sqlite3.connect(out)
    first = True
    for src in sources:
        s = sqlite3.connect(src)
        if first:
            for row in s.execute(
                    "SELECT sql FROM sqlite_master WHERE sql IS NOT NULL "
                    "AND name NOT LIKE 'sqlite_%' AND name NOT LIKE 'q_fts_%'"):
                con.execute(row[0])
            first = False
        s.close()
        con.execute("ATTACH DATABASE ? AS src", (src,))
        cols = [r[1] for r in con.execute("PRAGMA table_info(questions)")]
        srccols = [r[1] for r in con.execute("PRAGMA src.table_info(questions)")]
        shared = [c for c in cols if c in srccols]
        con.execute(f"INSERT INTO questions ({','.join(shared)}) "
                    f"SELECT {','.join(shared)} FROM src.questions")
        con.execute("INSERT INTO q_fts (id, question_text, ms_text, topic_name) "
                    "SELECT id, question_text, ms_text, topic_name FROM src.q_fts")
        con.commit()          # DETACH fails while a write txn is still open
        con.execute("DETACH DATABASE src")

    n = con.execute("SELECT COUNT(*) FROM questions").fetchone()[0]
    print(f"{n} questions in {out}")
    for r in con.execute(
            "SELECT syllabus, COUNT(*), SUM(ms_text IS NOT NULL), "
            "       SUM(question_latex IS NOT NULL), SUM(image IS NOT NULL) "
            "FROM questions GROUP BY syllabus ORDER BY syllabus"):
        print(f"  {r[0]}: {r[1]:>4} questions | {r[2]:>4} mark schemes | "
              f"{r[3]:>4} LaTeX | {r[4]:>4} images")
    con.close()


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2:])
