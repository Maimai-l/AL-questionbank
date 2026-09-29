#!/usr/bin/env python3
"""Build data/textbooks.js from the chapter index and Markdown files."""
import json
import sqlite3
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from lib import paths  # noqa: E402

DATA = Path(paths.DATA)
DB = Path(paths.DB)
OUT = DATA / "textbooks.js"


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
        d["content"] = path.read_text(encoding="utf-8")
        rows.append(d)
    OUT.write_text("window.TEXTBOOKS=" + json.dumps(rows, ensure_ascii=False,
                   separators=(",", ":")) + ";\nwindow.TEXTBOOK_QUESTIONS=[];\n",
                   encoding="utf-8")
    print(f"{len(rows)} chapters -> {OUT}")


if __name__ == "__main__":
    main()
