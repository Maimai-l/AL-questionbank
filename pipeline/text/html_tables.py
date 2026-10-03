#!/usr/bin/env python3
"""Turn the OCR's HTML tables into pipe tables.

PaddleOCR returns a genuine <table> for every grid it sees — frequency tables,
trace tables, truth tables. That is the right *content*, but as raw markup it
is unreadable to a human and expensive noise to a language model: one 20-row
trace table costs several hundred tokens of style attributes alone.

Converting to a pipe table keeps every cell and reads correctly as plain text.
rowspan / colspan are expanded so columns still line up.

Only the known layout tags are touched. A Computer Science paper legitimately
contains <symbol> and <letter> — those are BNF non-terminals, not markup, and
stripping them would destroy the question.
"""
import html as _html, re, sqlite3, sys
from html.parser import HTMLParser

import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))          # 项目根目录
from lib import paths

LAYOUT = {"table", "tr", "td", "th", "thead", "tbody", "div", "p", "br",
          "span", "b", "i", "u", "strong", "em", "font", "sub", "sup"}
TAG_RE = re.compile(r"</?([a-zA-Z][a-zA-Z0-9]*)\b[^>]*>")
TABLE_RE = re.compile(r"<table\b.*?</table>", re.I | re.S)


class Grid(HTMLParser):
    """Collect a table as a rectangular list of rows, expanding spans."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.rows, self.cur, self.cell = [], None, None
        self.pending = {}          # column -> (rows_left, text) from a rowspan
        self.col = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "tr":
            self.cur, self.col = [], 0
            self._fill()
        elif tag in ("td", "th") and self.cur is not None:
            self._fill()
            self.cell = {"t": [], "cs": int(a.get("colspan", 1) or 1),
                         "rs": int(a.get("rowspan", 1) or 1)}
        elif tag == "br" and self.cell is not None:
            self.cell["t"].append(" / ")

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self.cell is not None:
            txt = " ".join("".join(self.cell["t"]).split())
            for k in range(self.cell["cs"]):
                self.cur.append(txt if k == 0 else "")
                if self.cell["rs"] > 1:
                    # counts the row it is declared in, so it is decremented
                    # once at the end of that row and survives into the next
                    self.pending[self.col] = [self.cell["rs"], txt if k == 0 else ""]
                self.col += 1
            self.cell = None
        elif tag == "tr" and self.cur is not None:
            self.rows.append(self.cur)
            self.cur = None
            for c in list(self.pending):
                self.pending[c][0] -= 1
                if self.pending[c][0] <= 0:
                    del self.pending[c]

    def handle_data(self, d):
        if self.cell is not None:
            self.cell["t"].append(d)

    def _fill(self):
        """Drop in any cell still spanning down from an earlier row."""
        while self.col in self.pending:
            self.cur.append(self.pending[self.col][1])
            self.col += 1


def to_pipe(fragment):
    g = Grid()
    try:
        g.feed(fragment)
        g.close()
    except Exception:
        return None
    rows = [r for r in g.rows if any(c.strip() for c in r)]
    if not rows:
        return None
    w = max(len(r) for r in rows)
    rows = [r + [""] * (w - len(r)) for r in rows]
    out = ["| " + " | ".join(r) + " |" for r in rows]
    # a header rule makes it a real markdown table, which models parse reliably
    out.insert(1, "|" + "|".join(["---"] * w) + "|")
    return "\n".join(out)


BLOCK = {"div", "p", "table", "tr", "thead", "tbody"}


def strip_layout(text):
    def sub(m):
        t = m.group(1).lower()
        if t not in LAYOUT:
            return m.group(0)          # <symbol>, <letter> — BNF, not markup
        return "\n" if t in BLOCK else ""
    return TAG_RE.sub(sub, text)


def convert(text):
    if not text or "<" not in text:
        return text, 0
    before = text

    def rep(m):
        p = to_pipe(m.group(0))
        return "\n\n" + p + "\n\n" if p else " "
    text = TABLE_RE.sub(rep, text)
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.I)
    text = strip_layout(text)
    # entities survive outside tables too (&lt; in a CS paper's BNF)
    if "&" in text:
        text = _html.unescape(text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{3,}", "  ", text)
    return text.strip(), int(text.strip() != before)


def main(dbpath=None):
    con = sqlite3.connect(dbpath)
    con.row_factory = sqlite3.Row
    fields = ("question_latex", "ms_latex", "question_text", "ms_text")
    counts = {f: 0 for f in fields}
    for r in con.execute(f"SELECT id,{','.join(fields)} FROM questions").fetchall():
        upd = {}
        for f in fields:
            new, ch = convert(r[f])
            if ch:
                upd[f] = new; counts[f] += 1
        if upd:
            con.execute("UPDATE questions SET " + ", ".join(f"{k}=?" for k in upd)
                        + " WHERE id=?", list(upd.values()) + [r["id"]])
    con.commit()
    print("HTML 表格 -> 竖线表格:")
    for f, n in counts.items():
        print(f"  {f}: {n}")
    left = con.execute("SELECT COUNT(*) FROM questions WHERE question_latex LIKE '%<td%' "
                       "OR ms_latex LIKE '%<td%'").fetchone()[0]
    print(f"  残留 <td>: {left}")
    con.close()


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else paths.DB)
