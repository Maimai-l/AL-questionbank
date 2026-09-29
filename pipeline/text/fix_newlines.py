#!/usr/bin/env python3
r"""Turn literal backslash-n escapes back into real line breaks.

The mark-scheme OCR returned HTML tables whose <br> became the two characters
'\' + 'n' rather than a newline, so a whole mark scheme arrives as one long
line reading "...(Max 5)\nOne mark per...". Unreadable on a page, and a
retrieval system splitting on newlines sees one giant blob.

The catch is that '\n' is also the start of real LaTeX — \neq, \nu, \nabla. The
discriminator is whether the escape sits inside a $...$ span: inside is maths,
outside is a line break. Anything inside is left alone.
"""
import re, sqlite3, sys

import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))          # 项目根目录
from lib import paths

# LaTeX commands beginning with n, longest first so \neq wins over \ne.
# Bare \ne is excluded when a '.' follows: that is a line break in front of
# "e.g.", which outnumbers real \ne by four to one in this corpus.
NCMD = re.compile(r"\\n(?:eq(?![a-zA-Z])|e(?![a-zA-Z.])|u(?![a-zA-Z])|"
                  r"(?:abla|ot|onumber|ewline|mid|gtr|leq|geq|sim|parallel|"
                  r"cong|subseteq|in)(?![a-zA-Z]))")


def unescape(text):
    if not text or "\\n" not in text:
        return text, 0
    out, i, n, in_math = [], 0, len(text), False
    while i < n:
        ch = text[i]
        if ch == "$":
            in_math = not in_math
            out.append(ch); i += 1; continue
        if ch == "\\" and i + 1 < n and text[i + 1] == "n":
            if in_math or NCMD.match(text, i):
                out.append(text[i:i + 2]); i += 2; continue
            out.append("\n"); i += 2
            # the escape often carried its own leading space from the table cell
            while i < n and text[i] == " ":
                i += 1
            continue
        out.append(ch); i += 1
    new = "".join(out)
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
    print("还原成真换行的字段:")
    for f, n in counts.items():
        print(f"  {f}: {n}")
    con.close()


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else paths.DB)
