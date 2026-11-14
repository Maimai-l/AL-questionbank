#!/usr/bin/env python3
"""The text of each option of an admissions MCQ, from its question text.

    python3 pipeline/admissions_rebuild/option_texts.py [--write]

Writes the column option_texts, JSON {"A": "3 and 4 only", ..., "E": null}:
the last run of lines opening with A, B, C ... in order (a line-start letter
followed by a space, "." or ")"; lines that do not open with the next letter
may sit between them and continue the option above). An option drawn as a
figure ("(图形选项)", "(图中的点 A)", or a letter with nothing after it) is
null, so is every offered letter the text does not print. Options set as one
aligned display (\mathbf{A}\quad ... \\ \mathbf{B} ...) are read from it. merge_admissions.py
calls derive() for each row it inserts; run this alone to refill the column.
Dry run by default.
"""
import argparse, json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))
from lib import db  # noqa: E402

OPT = re.compile(r"^(?:\*\*)?([A-H])(?:\*\*)?(?:[\s.):]+(.*))?$")
MATHOPT = re.compile(r"\\(?:mathbf|textbf|bf)\s*\{\s*([A-H])\s*\}\s*(?:\\q?quad|\\,|~)?\s*"
                     r"(.*?)(?=\\\\|\\end\{|&\s*\\(?:mathbf|textbf|bf)|\$\$)", re.S)
FIGURE = re.compile(r"^\(?(?:图形选项|图中|见图|见上方图)")


def derive(text, letters):
    """{letter: text or None} for the offered letters."""
    lines = (text or "").split("\n")
    runs, cur, want = [], {}, "A"
    for ln in lines:
        s = ln.strip()
        m = OPT.match(s)
        if m and m.group(1) == want:
            cur[want] = (m.group(2) or "").strip()
            last = want
            want = chr(ord(want) + 1)
        elif m and m.group(1) == "A":
            if len(cur) >= 2:
                runs.append(cur)
            cur, want, last = {"A": (m.group(2) or "").strip()}, "B", "A"
        elif cur and s and not s.startswith(("![", "|", "<")) and len(cur) < len(letters or "ABCDE"):
            cur[last] = (cur[last] + " " + s).strip()   # a wrapped option
    if len(cur) >= 2:
        runs.append(cur)
    run = dict(runs[-1]) if runs else {}
    # TMUA prints some option lists as one aligned display: &\mathbf{A}\quad a\leq 1\\...
    for L, t in MATHOPT.findall(text or ""):
        t = t.strip().rstrip("&").strip()
        if t and not run.get(L):
            run[L] = f"$ {t} $"
    out = {}
    for L in letters or sorted(run):
        t = run.get(L)
        out[L] = None if not t or FIGURE.match(t) else t
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    con = db.connect()
    db.add_column(con, "questions", "option_texts")
    rows = con.execute("SELECT id, syllabus, question_text, options FROM questions "
                       "WHERE qtype='mcq'").fetchall()
    upd, full, some, none = [], 0, 0, 0
    for r in rows:
        d = derive(r["question_text"], json.loads(r["options"] or "[]"))
        n = sum(v is not None for v in d.values())
        full += n == len(d); some += 0 < n < len(d); none += n == 0
        upd.append((json.dumps(d, ensure_ascii=False), r["id"]))
    print(f"{len(rows)} 道选择题:选项文字齐全 {full},部分(其余为图形选项){some},"
          f"全部是图形或未找到 {none}")
    if a.write:
        con.executemany("UPDATE questions SET option_texts=? WHERE id=?", upd)
        con.commit()
        print("已写入 option_texts")
    else:
        print("(dry run;加 --write 写入)")


if __name__ == "__main__":
    main()
