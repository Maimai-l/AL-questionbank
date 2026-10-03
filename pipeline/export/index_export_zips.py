#!/usr/bin/env python3
"""Embed one standard, LLM-ready question index into every export ZIP."""
from __future__ import annotations

import argparse
import csv
import io
import json
import sqlite3
import tempfile
import zipfile
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from lib import paths  # noqa: E402
from pipeline.export import question_md  # noqa: E402

DATA = Path(paths.DATA)
PROJECT = ROOT
EXPORTS = Path(paths.EXPORTS)
DB = Path(paths.DB)
SCHEMA = "alevel-question-index/v1"


def rows_for_ids(con: sqlite3.Connection, ids: list[str]) -> list[sqlite3.Row]:
    if not ids:
        return []
    marks = ",".join("?" for _ in ids)
    found = list(con.execute(f"SELECT * FROM questions WHERE id IN ({marks})", ids))
    by_id = {row["id"]: row for row in found}
    missing = [qid for qid in ids if qid not in by_id]
    if missing:
        raise ValueError(f"Database lacks {len(missing)} indexed questions, e.g. {missing[:3]}")
    return [by_id[qid] for qid in ids]


def archive_rows(con: sqlite3.Connection, path: Path, zin: zipfile.ZipFile) -> tuple[list[sqlite3.Row], dict]:
    names = zin.namelist()
    # question banks list their questions in manifest.csv, the curated papers in
    # index.csv (export_curated_hard_papers.py); both carry an "id" column
    csv_name = next((n for n in names if n.endswith(("manifest.csv", "/index.csv"))), None)
    json_name = next((n for n in names if n.endswith("manifest.json")), None)
    image_only = path.name == "9709_p1_images_webp.zip"
    if image_only:
        rows = list(con.execute("SELECT * FROM questions WHERE syllabus='9709' AND component='1' ORDER BY year, month, paper, q, id"))
        return rows, {"kind": "image-bundle", "companion_archive": "9709_p1_questions_text.zip"}
    if csv_name:
        reader = csv.DictReader(io.StringIO(zin.read(csv_name).decode("utf-8")))
        ids = [r["id"] for r in reader if r.get("id")]
        return rows_for_ids(con, ids), {"kind": "question-bank"}
    if json_name:
        chapter = json.loads(zin.read(json_name).decode("utf-8"))
        # as export_all_chapters.py: whole questions on the topic, and those
        # with only some parts on it
        rows = [r for r in con.execute("""
            SELECT * FROM questions WHERE syllabus=? AND (topic=? OR topic_parts LIKE ?)
            ORDER BY year, month, paper, q, id
        """, (chapter["syllabus"], chapter["topic"], f'%"topic": "{chapter["topic"]}"%'))
            if r["topic"] == chapter["topic"] or question_md.labels_on_topic(r, chapter["topic"])]
        if len(rows) != chapter["questions"]:
            raise ValueError(f"{path.name}: chapter says {chapter['questions']} questions, DB has {len(rows)}")
        return rows, {"kind": "chapter-package", "chapter": chapter}
    raise ValueError(f"Cannot identify question manifest in {path}")


def local_image(path: Path, row: sqlite3.Row, kind: str) -> str | None:
    if not row["image"]:
        return None
    if path.name.startswith("9709_p1_"):
        return "images/" + str(Path(row["image"]).with_suffix(".webp"))
    if kind == "chapter-package":
        return "images/questions/" + row["image"]
    return "images/" + row["image"]


def entry(path: Path, row: sqlite3.Row, kind: str, topic: str | None = None) -> dict:
    """One question of the index. text_usable false means question_text cannot
    stand in for the image (q_quality missing, garbled or partial); parts are
    the question's parts with their own marks, topic and task (part_data), and
    parts_included, in a chapter package, the parts it gives when not all."""
    question = row["question_latex"] or row["question_text"] or ""
    scheme = row["ms_latex"] or row["ms_text"] or ""
    image = local_image(path, row, kind)
    parts = [{"label": p["label"], "marks": p["marks"], "topic": p["topic"], "task": p.get("task"),
              "has_mark_scheme": bool(p["ms"])}
             for p in (question_md.parts_of(row) or {}).get("parts", [])]
    included = None
    if kind == "chapter-package" and topic and row["topic"] != topic:
        included = question_md.labels_on_topic(row, topic)
    return {
        "id": row["id"], "syllabus": row["syllabus"], "component": row["component"],
        "component_name": row["component_name"], "paper": row["paper"],
        "session": row["session"], "year": row["year"], "question": row["q"],
        "marks": row["marks"], "topic": row["topic"], "topic_name": row["topic_name"],
        "subtopic_name": row["subtopic_name"], "answer": row["answer"], "question_type": row["qtype"],
        "image": image, "question_text": question, "mark_scheme": scheme,
        "q_quality": row["q_quality"], "ms_quality": row["ms_quality"],
        "text_usable": question_md.text_usable(row) and bool(question),
        "has_diagram": bool(row["has_diagram"]), "parts": parts,
        "options": json.loads(row["option_texts"]) if row["option_texts"] else None,
        "parts_included": included,
        "markdown_file": "questions.md",
    }


def index_markdown(index: dict) -> str:
    meta = index["archive"]
    lines = ["# Question index", "", f"Schema: `{SCHEMA}`", "",
             "This ZIP is self-indexing. An LLM can select question IDs from `index.json` and return:", "",
             "```json", '{"schema":"alevel-question-set/v1","items":[{"archive_id":"' + meta["id"] + '","question_ids":["ID1","ID2"]}]}', "```", "",
             "`text_usable: false` means the question text is unreliable: read the image instead. "
             "`parts` gives each part's marks, topic and task.", "",
             "| id | paper | year | topic | marks | parts | text | image |",
             "|---|---|---:|---|---:|---|---|---|"]
    for q in index["questions"]:
        parts = ", ".join(q["parts_included"] or [p["label"] for p in q["parts"] if p["label"]])
        text = "ok" if q["text_usable"] else "image only"
        lines.append(f"| `{q['id']}` | {q['paper']} | {q['year']} | {q['topic_name'] or ''} | "
                     f"{q['marks'] or ''} | {parts} | {text} | {q['image'] or ''} |")
    return "\n".join(lines) + "\n"


def update_zip(path: Path, con: sqlite3.Connection, write: bool) -> tuple[int, str]:
    with zipfile.ZipFile(path) as zin:
        names = zin.namelist()
        roots = [n.split("/", 1)[0] for n in names if "/" in n]
        if not roots:
            raise ValueError(f"Empty or flat ZIP: {path}")
        archive_id = roots[0]
        rows, extra = archive_rows(con, path, zin)
        index = {"schema": SCHEMA, "archive": {"id": archive_id, "file": path.name, **extra},
                 "questions": [entry(path, row, extra["kind"], extra.get("chapter", {}).get("topic"))
                               for row in rows]}
        if not write:
            return len(rows), extra["kind"]
        data_json = json.dumps(index, ensure_ascii=False, indent=2).encode("utf-8")
        data_md = index_markdown(index).encode("utf-8")
        with tempfile.NamedTemporaryFile(prefix=path.stem + "-", suffix=".zip", dir=path.parent, delete=False) as temp:
            temp_path = Path(temp.name)
        try:
            with zipfile.ZipFile(temp_path, "w", allowZip64=True) as zout:
                for info in zin.infolist():
                    if info.filename.endswith(("/INDEX.md", "/index.json", "/index.js", "/viewer.html")):
                        continue
                    zout.writestr(info, zin.read(info.filename))
                zout.writestr(f"{archive_id}/INDEX.md", data_md, compress_type=zipfile.ZIP_DEFLATED)
                zout.writestr(f"{archive_id}/index.json", data_json, compress_type=zipfile.ZIP_DEFLATED)
            temp_path.replace(path)
        finally:
            temp_path.unlink(missing_ok=True)
        return len(rows), extra["kind"]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="replace ZIPs after a successful consistency check")
    args = parser.parse_args()
    paths = sorted(EXPORTS.rglob("*.zip"))
    with sqlite3.connect(DB) as con:
        con.row_factory = sqlite3.Row
        results = [(path, *update_zip(path, con, args.write)) for path in paths]
    for path, count, kind in results:
        print(f"{kind:16} {count:4}  {path.relative_to(PROJECT)}")
    print(f"Checked {len(results)} ZIPs" + (" and embedded indexes" if args.write else " (dry run)"))


if __name__ == "__main__":
    main()
