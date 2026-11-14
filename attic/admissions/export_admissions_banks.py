#!/usr/bin/env python3
"""Create standalone TMUA and TARA question-bank ZIPs from the active DB.

The ZIPs contain all referenced images under their own images/ directory; they
never refer to the project's OCR-source folder or any other external local path.
"""
from __future__ import annotations

import csv
import re
import shutil
import sqlite3
import tempfile
import zipfile
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from lib import paths  # noqa: E402

DATA = Path(paths.DATA)
ASSETS = DATA  # images and books/ live in data/
DB = Path(paths.DB)
OUT = Path(paths.EXPORTS)
IMAGE_REF = re.compile(r'((?:src|href)=["\']|\]\()((?:img_adm|img_tara|imgs)/[^"\')\s]+)', re.I)


def source_for(row: sqlite3.Row, ref: str) -> tuple[str, Path]:
    """Return archive-relative name and local source for a referenced image."""
    if ref.startswith("imgs/"):
        # TMUA official worked answers retain their original per-PDF imgs/ links.
        # Bundle these legacy images under a unique, internal destination.
        base = row["id"].rsplit("-q", 1)[0].replace("-P", "-paper-") + "-worked-answers"
        source = Path(paths.BANK_OCR) / "TMUA" / "worked_answers" / base / ref
        return f"worked_answers/{base}/{Path(ref).name}", source
    return ref, ASSETS / ref


def rewrite_and_collect(row: sqlite3.Row, text: str, images: dict[str, Path]) -> str:
    def replace(match: re.Match[str]) -> str:
        ref = match.group(2)
        destination, source = source_for(row, ref)
        images[destination] = source
        return match.group(1) + "images/" + destination
    return IMAGE_REF.sub(replace, text)


def build(name: str, syllabuses: tuple[str, ...]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / f"{name.lower()}_question_bank.zip"
    package = f"{name.lower()}_question_bank"
    tmp = Path(tempfile.mkdtemp(prefix=f"{name.lower()}-export-"))
    try:
        with sqlite3.connect(DB) as con:
            con.row_factory = sqlite3.Row
            placeholders = ",".join("?" for _ in syllabuses)
            rows = list(con.execute(f"""
                SELECT id, syllabus, component, component_name, paper, session, year, month,
                       q, marks, topic, topic_name, subtopic_name, question_latex,
                       question_text, ms_latex, ms_text, answer, qtype, options, image
                FROM questions
                WHERE syllabus IN ({placeholders})
                ORDER BY syllabus, component, year, month, paper, q, id
            """, syllabuses))

        images: dict[str, Path] = {}
        lines = [f"# {name} Question Bank", "",
                 f"{len(rows)} questions. This is a standalone export: all referenced images are included in `images/`.",
                 ""]
        manifest = []
        for row in rows:
            question = row["question_latex"] or row["question_text"] or "_Question text unavailable._"
            markscheme = row["ms_latex"] or row["ms_text"] or "_Mark scheme unavailable._"
            question = rewrite_and_collect(row, question, images)
            markscheme = rewrite_and_collect(row, markscheme, images)
            if row["image"]:
                destination, source = source_for(row, row["image"])
                images[destination] = source
            lines += ["---", "", f"## {row['paper']} · {row['session']} · Q{row['q']}", "",
                      f"- ID: `{row['id']}`", f"- Source: {row['syllabus']} — {row['component_name']}",
                      f"- Topic: {row['topic_name'] or 'Unclassified'}",
                      f"- Marks: {row['marks'] if row['marks'] is not None else '—'}", ""]
            if row["image"]:
                destination, _ = source_for(row, row["image"])
                lines += [f"![Question image](images/{destination})", ""]
            lines += ["### Question", "", question.strip(), "", "### Mark scheme", "", markscheme.strip(), ""]
            manifest.append({
                "id": row["id"], "syllabus": row["syllabus"], "paper": row["paper"],
                "session": row["session"], "question": row["q"], "component": row["component"],
                "topic": row["topic_name"] or "", "subtopic": row["subtopic_name"] or "",
                "marks": row["marks"] or "", "answer": row["answer"] or "", "type": row["qtype"] or "",
            })

        questions_file = tmp / "questions.md"
        questions_file.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
        manifest_file = tmp / "manifest.csv"
        with manifest_file.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(manifest[0]))
            writer.writeheader()
            writer.writerows(manifest)
        readme = tmp / "README.md"
        readme.write_text(
            f"# {name} question bank\n\n"
            f"Contains {len(rows)} questions from {', '.join(syllabuses)}. Extract this ZIP and open `questions.md`; "
            "all image paths are internal to this archive. No external project files are required.\n",
            encoding="utf-8")

        missing = []
        with zipfile.ZipFile(out, "w", allowZip64=True) as zf:
            zf.write(questions_file, f"{package}/questions.md", compress_type=zipfile.ZIP_DEFLATED)
            zf.write(manifest_file, f"{package}/manifest.csv", compress_type=zipfile.ZIP_DEFLATED)
            zf.write(readme, f"{package}/README.md", compress_type=zipfile.ZIP_DEFLATED)
            for destination, source in sorted(images.items()):
                if source.is_file():
                    zf.write(source, f"{package}/images/{destination}", compress_type=zipfile.ZIP_STORED)
                else:
                    missing.append(str(source))
        if missing:
            raise FileNotFoundError(f"{name}: {len(missing)} referenced images missing, e.g. {missing[:3]}")
        print(f"{name}: {len(rows)} questions, {len(images)} images -> {out}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main() -> None:
    build("TMUA", ("TMUA",))
    build("TARA", ("TSA", "BMAT"))


if __name__ == "__main__":
    main()
