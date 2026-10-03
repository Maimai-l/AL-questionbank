#!/usr/bin/env python3
"""Mechanical clean-ups of the reviewed text, written as a fix_batches result file so
that `fix_batches.py apply` checks and records them like any other correction.

    python3 pipeline/text/normalize_text.py      # writes raw/text_fix/normalize/out/batch_01.json

dollar   A literal dollar sign outside a formula is written \\$ by the review rules,
         but KaTeX auto-render does not skip an escaped delimiter: it opens a formula
         at that $ and the rest of the line renders wrongly. Outside a formula \\$
         becomes $\\$$, a formula holding only the sign; inside a formula it stays.
codes    Part of 9231 paper 2 was written before the block rules, with the marks in
         square brackets on the line after the answer: "[M1 A1] guidance". The codes
         move to the end of the answer line and the rest becomes a Guidance line, as
         everywhere else. Codes in round brackets are left alone: the original pages
         print them so for alternative methods.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from lib import db  # noqa: E402
from pipeline.text.fix_batches import WORK, mcol, qcol  # noqa: E402

TOKEN = re.compile(r"\\\$|\$\$|\$")
CODE = r"\*?(?:DM|SC\s?B|M|A|B)\d\*?(?:\s?FT)?"
BRACKET = re.compile(rf"^\[((?:{CODE})(?:\s+{CODE})*)\]\s*(.*)$")


def fix_dollars(text):
    """\\$ outside a formula becomes $\\$$; formulas are tracked by unescaped $ and $$."""
    out, pos, open_, join = [], 0, None, False
    for m in TOKEN.finditer(text):
        out.append(text[pos:m.start()])
        t = m.group()
        if join:                                  # the formula opened by "$\$" already holds this one
            join, pos = False, m.end()
            open_ = "$"
            continue
        if t == "\\$":
            # "\$$x$" would become "$\$$$x$", which auto-render reads as $$ display
            # math; the sign and the formula after it become one formula, "$\$x$"
            join = not open_ and text[m.end():m.end() + 1] == "$" and text[m.end():m.end() + 2] != "$$"
            out.append(t if open_ else "$\\$" if join else "$\\$$")
        else:
            if open_ is None:
                open_ = t
            elif open_ == t:
                open_ = None
            out.append(t)
        pos = m.end()
    out.append(text[pos:])
    return "".join(out)


def fix_codes(text):
    """Move "[M1 A1] guidance" lines onto the answer line above."""
    lines = text.split("\n")
    out = []
    for line in lines:
        m = BRACKET.match(line.strip())
        if not m or not out:
            out.append(line)
            continue
        codes, rest = m.group(1), m.group(2).strip()
        total = ""
        t = re.fullmatch(r"\|\s*(\d+)", rest)
        if t:                                     # "[B1]  |  4": the part ends here
            total, rest = t.group(1), ""
        if rest == "AG":
            codes, rest = codes + " AG", ""
        out[-1] = out[-1].rstrip() + "  " + codes
        if rest:
            out.append("Guidance: " + rest)
        if total:
            out.append("  |  " + total)
    return "\n".join(out)


def main():
    con = db.connect()
    items = []
    for r in con.execute("SELECT * FROM questions WHERE syllabus IN ('9618', '9709', '9231') ORDER BY id"):
        q, s = r[qcol(r)] or "", r[mcol(r)] or ""
        nq = fix_dollars(q)
        ns = fix_codes(fix_dollars(s)) if r["syllabus"] == "9231" else fix_dollars(s)
        why = []
        if nq != q or fix_dollars(s) != s:
            why.append("文本中的美元符号改写成 $\\$$,避免 KaTeX 把 \\$ 当作公式起点")
        if ns != fix_dollars(s):
            why.append("方括号评分码移到答案行末,说明另起 Guidance 行")
        if why:
            items.append({"id": r["id"], "question": nq if nq != q else None,
                          "scheme": ns if ns != s else None, "why": ";".join(why)})
    out = os.path.join(WORK, "normalize", "out")
    os.makedirs(out, exist_ok=True)
    path = os.path.join(out, "batch_01.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=1)
    print(f"{len(items)} 题 -> {os.path.relpath(path)}")


if __name__ == "__main__":
    main()
