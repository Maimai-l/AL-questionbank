#!/usr/bin/env python3
"""Turn PaddleOCR-VL mark scheme output into per-question text.

The model returns each mark scheme page as an HTML table with the original
Question | Answer | Marks | Guidance columns and LaTeX for the mathematics.
The question label sits in the first cell of a row group, carried across the
group by `rowspan`, so the parser has to track that to attribute rows.
"""
import html, json, os, re, sys, collections
from html.parser import HTMLParser

LABEL_RE = re.compile(r"^\s*(\d{1,2})\s*(\([a-z]\))?\s*(\((?:i{1,3}|iv|v)\))?\s*$")
FURNITURE = re.compile(r"UCLES|PUBLISHED|dynamicpaper|Cambridge International|"
                       r"Mark Scheme|Page \d+ of \d+|^\s*9\d{3}/\d\d\s*$", re.I)


class TableGrab(HTMLParser):
    """Collect tables as lists of rows; each row is a list of (text, rowspan)."""

    def __init__(self):
        super().__init__()
        self.tables, self._rows, self._row, self._cell = [], None, None, None
        self._span = 1

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "table":
            self._rows = []
        elif tag == "tr" and self._rows is not None:
            self._row = []
        elif tag in ("td", "th") and self._row is not None:
            self._cell = []
            try:
                self._span = int(a.get("rowspan", 1))
            except ValueError:
                self._span = 1

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self._cell is not None:
            self._row.append((" ".join("".join(self._cell).split()), self._span))
            self._cell, self._span = None, 1
        elif tag == "tr" and self._row is not None:
            if self._row:
                self._rows.append(self._row)
            self._row = None
        elif tag == "table" and self._rows is not None:
            self.tables.append(self._rows)
            self._rows = None

    def handle_data(self, d):
        if self._cell is not None:
            self._cell.append(d)


def strip_tables(md):
    """Non-table prose on a page, with running header/footer removed."""
    txt = re.sub(r"<table.*?</table>", " ", md, flags=re.S)
    txt = re.sub(r"<[^>]+>", " ", txt)
    keep = [l.strip() for l in txt.split("\n")
            if l.strip() and not FURNITURE.search(l)]
    return "\n".join(keep)


def rows_to_questions(pages):
    """Walk every table row in document order, attributing rows to questions."""
    out = collections.OrderedDict()
    current = None
    for md in pages:
        p = TableGrab()
        try:
            p.feed(md)
        except Exception:
            continue
        for table in p.tables:
            header = [c[0].lower() for c in table[0]] if table else []
            if "question" not in " ".join(header):
                continue                      # cover page / grade table, not a mark scheme
            for row in table[1:]:
                cells = [html.unescape(c[0]) for c in row]
                if not any(cells):
                    continue
                first = cells[0]
                m = LABEL_RE.match(first)
                if m:
                    current = int(m.group(1))
                    label = first.strip()
                    body = cells[1:]
                else:
                    label = ""
                    body = cells
                if current is None:
                    continue
                out.setdefault(current, []).append((label, body))
    return out


def render(rowgroups):
    """One readable block per question, columns kept but flattened."""
    lines = []
    for label, body in rowgroups:
        cells = [c for c in body if c]
        if not cells:
            continue
        prefix = f"{label}  " if label else "    "
        lines.append(prefix + "  |  ".join(cells))
    return "\n".join(lines)


def main(cache, out_json):
    per_file = {}
    for ln in open(cache):
        try:
            d = json.loads(ln)
        except Exception:
            continue
        if not d.get("pages"):
            continue
        per_file[d["file"]] = d["pages"]
    print(f"{len(per_file)} mark schemes decoded")

    records, empty = [], 0
    for fname, pages in sorted(per_file.items()):
        subject, series, _, comp = fname.replace(".pdf", "").split("_")
        qs = rows_to_questions(pages)
        if not qs:
            empty += 1
            continue
        for q, groups in qs.items():
            text = render(groups)
            if len(text) < 20:
                continue
            records.append({
                "subject": subject, "series": series,
                "component": comp[0], "variant": comp[1], "q": q,
                "ms_ocr": text, "source": fname,
            })
    json.dump(records, open(out_json, "w"), ensure_ascii=False, indent=1)
    print(f"{len(records)} question-level mark schemes; {empty} files yielded none")
    byq = collections.Counter(r["subject"] for r in records)
    for k, v in sorted(byq.items()):
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
