#!/usr/bin/env python3
"""Build data/textbooks.js from the chapter index and Markdown files.

The book shown in the page's drop-down is its name, not the folder the
chapters sit in: 9709_p1 -> "Paper 1 · Pure Mathematics 1", 9709_p23 ->
"Paper 2/3 · Pure Mathematics 2 & 3". The folder stays in book_id.
"""
import json
import re
import sqlite3
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from lib import paths  # noqa: E402

DATA = Path(paths.DATA)
DB = Path(paths.DB)
OUT = DATA / "textbooks.js"

PAPER_9709 = {"1": "Pure Mathematics 1", "2": "Pure Mathematics 2",
              "3": "Pure Mathematics 3", "4": "Mechanics",
              "5": "Probability & Statistics 1", "6": "Probability & Statistics 2"}
SUBJECT = {"9231": "Further Mathematics", "9618": "Computer Science",
           "9709": "Mathematics"}


def book_name(syllabus, book):
    """9709_p23 -> 'Paper 2/3 · Pure Mathematics 2 & 3'; 9231 -> 'Further Mathematics'."""
    m = re.fullmatch(r"\d{4}_p(\d+)", book)
    if not m or syllabus != "9709":
        return SUBJECT.get(book, book)
    papers = list(m.group(1))
    names = [PAPER_9709.get(p, f"Paper {p}") for p in papers]
    if len(papers) > 1 and all(n.startswith("Pure Mathematics ") for n in names):
        name = "Pure Mathematics " + " & ".join(papers)
    else:
        name = " / ".join(names)
    return f"Paper {'/'.join(papers)} · {name}"


def main():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    rows = []
    for row in con.execute("""
        SELECT id, syllabus, book, chapter_no, title, path, topic, topic_name
        FROM chapters ORDER BY syllabus, book, chapter_no
    """):
        d = dict(row)
        path = Path(paths.under_data(d["path"]))
        if not path.is_file():
            raise FileNotFoundError(path)
        d["s"] = d.pop("syllabus")
        d["book_id"] = d["book"]
        d["book"] = book_name(d["s"], d["book"])
        d["content"] = path.read_text(encoding="utf-8")
        rows.append(d)
    OUT.write_text("window.TEXTBOOKS=" + json.dumps(rows, ensure_ascii=False,
                   separators=(",", ":")) + ";\nwindow.TEXTBOOK_QUESTIONS=[];\n",
                   encoding="utf-8")
    print(f"{len(rows)} chapters -> {OUT}")


if __name__ == "__main__":
    main()
