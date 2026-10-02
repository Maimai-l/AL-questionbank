#!/usr/bin/env python3
r"""Turn literal backslash-n escapes back into real line breaks.

The mark-scheme OCR returned HTML tables whose <br> became the two characters
'\' + 'n' rather than a newline, so a whole mark scheme arrives as one long
line reading "...(Max 5)\nOne mark per...". Unreadable on a page, and a
retrieval system splitting on newlines sees one giant blob.

The catch is that '\n' is also the start of real LaTeX — \neq, \nu, \nabla. The
discriminator is whether the escape sits inside a $...$ span: inside is maths,
outside is a line break. Anything inside is left alone. Parity of $ is counted per
table cell, so one unclosed $ does not flip the rest of the text.

A break inside a table cell cannot be a real newline (the row would split), so
there it becomes <br>, as in a Markdown table; the pages and exports render it.
"""
import re, sqlite3, sys

import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))          # 项目根目录
from lib import paths, scheme

# LaTeX commands beginning with n, longest first so \neq wins over \ne.
# Bare \ne is excluded when a '.' follows: that is a line break in front of
# "e.g.", which outnumbers real \ne by four to one in this corpus.
NCMD = re.compile(r"\\n(?:eq(?![a-zA-Z])|e(?![a-zA-Z.])|u(?![a-zA-Z])|"
                  r"(?:abla|ot|onumber|ewline|mid|gtr|leq|geq|sim|parallel|"
                  r"cong|subseteq|in)(?![a-zA-Z]))")


def _cell(text, br):
    """One table cell, or one line outside a table: escapes outside $...$ become
    `br`. An escape inside double quotes, or next to a quote, is a string literal
    in code (9618) and stays."""
    out, i, n, in_math, in_str = [], 0, len(text), False, False
    while i < n:
        ch = text[i]
        if ch == "$":
            in_math = not in_math
        elif ch == '"':
            in_str = not in_str
        elif ch == "\\" and text.startswith("\\n", i) and not in_math and not in_str \
                and not NCMD.match(text, i) and not (i and text[i - 1] == "'") \
                and text[i + 2:i + 3] not in ('"', "'"):
            while out and out[-1] == " ":
                out.pop()
            out.append(br)
            i += 2
            while i < n and text[i] == " ":   # the escape often carried a space from the cell
                i += 1
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def unescape(text):
    """Line breaks inside a table cell (a Markdown pipe table row, or a mark-scheme row
    `answer  |  marks  |  guidance`, lib/scheme.py) become <br>, so the row stays one
    line; elsewhere they become real newlines. Escapes inside maths are left for a person to check."""
    if not text or "\\n" not in text:
        return text, 0
    lines = []
    for line in text.split("\n"):
        if "\\n" not in line:
            lines.append(line)
        elif re.match(r"\s*\|.*\|\s*$", line):             # a Markdown pipe table row
            lines.append("|".join(_cell(c, "<br>") for c in line.split("|")))
        elif scheme.is_row(line):                            # a mark-scheme row
            parts = re.split(f"({scheme.SEP.pattern})", line)
            lines.append("".join(p if k % 2 else _cell(p, "<br>") for k, p in enumerate(parts)))
        else:
            lines.append(_cell(line, "\n"))
    new = "\n".join(lines)
    return new, int(new != text)


def main(dbpath=None):
    con = sqlite3.connect(dbpath)
    con.row_factory = sqlite3.Row
    fields = ("question_latex", "question_text", "ms_latex", "ms_text")
    counts = {f: 0 for f in fields}
    for r in con.execute(f"SELECT id,{','.join(fields)} FROM questions").fetchall():
        upd = {}
        for f in fields:
            new, ch = unescape(r[f])
            if ch:
                upd[f] = new; counts[f] += 1
        if upd:
            con.execute("UPDATE questions SET " + ", ".join(f"{k}=?" for k in upd)
                        + " WHERE id=?", list(upd.values()) + [r["id"]])
    con.commit()
    print("改成换行或 <br> 的字段:")
    for f, n in counts.items():
        print(f"  {f}: {n}")
    con.close()


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else paths.DB)
