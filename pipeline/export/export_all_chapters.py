#!/usr/bin/env python3
"""Export every textbook chapter and its topic-matched CAIE questions.

Each chapter gets its own ZIP containing chapter.md and its textbook images, a
separate questions.md, question images, and mark schemes. It only reads the
question-bank database and assets; it never changes them.
"""
from __future__ import annotations

import json
import re
import shutil
import sqlite3
import tempfile
import zipfile
from collections import defaultdict
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from lib import paths  # noqa: E402

DATA = Path(paths.DATA)
DB = Path(paths.DB)
ASSETS = DATA  # images and books/ live in data/
OUT_DIR = Path(paths.EXPORTS) / "chapters"
IMG_REF = re.compile(r"(?:src|href)=[\"'](imgs/[^\"'#?]+)", re.IGNORECASE)


def safe_name(value: str) -> str:
    """Make a stable, human-readable filename fragment."""
    return re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("._") or "chapter"


def markdown_question(question: sqlite3.Row, image_rel: str | None) -> str:
    label = f"{question['paper']} {question['session']} Q{question['q']}"
    if question["marks"] is not None:
        label += f" · {question['marks']} marks"
    text = question["question_latex"] or question["question_text"] or "_题干未能提取；请查看原题图。_"
    scheme = question["ms_latex"] or question["ms_text"] or "_暂无可用评分细则文本。_"
    lines = [f"### {label}", ""]
    if image_rel:
        lines += [f"![{label}]({image_rel})", ""]
    lines += [text.strip(), "", "#### Mark scheme", "", scheme.strip(), ""]
    return "\n".join(lines)


def add_file(zf: zipfile.ZipFile, source: Path, archive_name: str, added: set[str]) -> bool:
    """Add a file once. Images are stored rather than re-compressed."""
    if archive_name in added:
        return False
    if not source.is_file():
        return False
    added.add(archive_name)
    kind = zipfile.ZIP_STORED if source.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".gif"} else zipfile.ZIP_DEFLATED
    zf.write(source, archive_name, compress_type=kind)
    return True


def main() -> None:
    if not DB.is_file():
        raise FileNotFoundError(DB)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    temp_dir = Path(tempfile.mkdtemp(prefix="caie-export-"))
    stats = defaultdict(int)
    manifest: list[dict[str, object]] = []

    try:
        con = sqlite3.connect(DB)
        con.row_factory = sqlite3.Row
        chapters = list(con.execute("""
            SELECT id, syllabus, book, chapter_no, title, path, topic, topic_name
            FROM chapters
            ORDER BY syllabus, book, chapter_no, id
        """))
        for number, chapter in enumerate(chapters, start=1):
            # One portable ZIP per chapter.  Its Markdown stays next to imgs/,
            # while question images live at images/questions/.
            archive_stem = f"{chapter['syllabus']}_{safe_name(chapter['book'])}_{chapter['chapter_no']:02d}_{safe_name(chapter['title'])}"
            # Keep the exported chapter packages grouped by their source book.
            book_out_dir = OUT_DIR / safe_name(chapter["book"] or chapter["syllabus"] or "other")
            book_out_dir.mkdir(parents=True, exist_ok=True)
            out = book_out_dir / f"{archive_stem}.zip"
            package_root = archive_stem
            added: set[str] = set()
            with zipfile.ZipFile(out, "w", allowZip64=True) as zf:
                chapter_source = DATA / chapter["path"]
                if not chapter_source.is_file():
                    raise FileNotFoundError(f"Missing chapter Markdown: {chapter_source}")
                chapter_file = "chapter.md"
                questions_file = "questions.md"
                chapter_arc = f"{package_root}/{chapter_file}"
                original = chapter_source.read_text(encoding="utf-8")
                questions = list(con.execute("""
                    SELECT id, paper, session, q, marks, question_latex, question_text,
                           ms_latex, ms_text, image
                    FROM questions
                    WHERE syllabus = ? AND topic = ?
                    ORDER BY year, month, paper, q, id
                """, (chapter["syllabus"], chapter["topic"])))

                question_parts = [f"# 配套 CAIE 真题：{chapter['title']}", "",
                         f"匹配规则：题目与本章同属 `{chapter['syllabus']}` / topic `{chapter['topic']}`。"]
                if not questions:
                    question_parts += ["", "_当前没有已标注到这个 topic 的题目。_"]
                for question in questions:
                    image_link = None
                    if question["image"]:
                        image_source = ASSETS / question["image"]
                        image_arc = f"{package_root}/images/questions/{question['image']}"
                        if add_file(zf, image_source, image_arc, added):
                            stats["question_images"] += 1
                        if image_source.is_file():
                            image_link = str(Path("images/questions") / question["image"])
                        else:
                            stats["missing_question_images"] += 1
                    question_parts += ["", markdown_question(question, image_link).rstrip()]
                    stats["question_placements"] += 1

                chapter_temp = temp_dir / f"{archive_stem}_chapter.md"
                chapter_temp.write_text(original.rstrip() + "\n", encoding="utf-8")
                add_file(zf, chapter_temp, chapter_arc, added)
                questions_temp = temp_dir / f"{archive_stem}_questions.md"
                questions_temp.write_text("\n".join(question_parts) + "\n", encoding="utf-8")
                add_file(zf, questions_temp, f"{package_root}/{questions_file}", added)
                stats["chapters"] += 1

                # Preserve the existing imgs/... links in chapter.md.
                for image_ref in sorted(set(IMG_REF.findall(original))):
                    image_source = chapter_source.parent / image_ref
                    image_arc = f"{package_root}/{image_ref}"
                    if add_file(zf, image_source, image_arc, added):
                        stats["textbook_images"] += 1
                    elif not image_source.is_file():
                        stats["missing_textbook_images"] += 1

                chapter_manifest = {
                    "chapter_id": chapter["id"], "syllabus": chapter["syllabus"],
                    "book": chapter["book"], "chapter_no": chapter["chapter_no"],
                    "title": chapter["title"], "topic": chapter["topic"],
                    "questions": len(questions), "file": chapter_arc,
                }
                manifest.append(chapter_manifest)
                readme = f"""# {chapter['title']}

This archive contains one textbook chapter, all questions whose `syllabus +
topic` tag matches it, their original question images, and extracted mark
schemes.

`chapter.md` is the textbook text with its textbook images in `imgs/`.
`questions.md` contains matched questions, their images, and mark schemes. Open
either file from within this extracted folder to keep image links working.
"""
                zf.writestr(f"{package_root}/README.md", readme, compress_type=zipfile.ZIP_DEFLATED)
                zf.writestr(f"{package_root}/manifest.json", json.dumps(chapter_manifest, ensure_ascii=False, indent=2), compress_type=zipfile.ZIP_DEFLATED)
            if number % 10 == 0 or number == len(chapters):
                print(f"Prepared {number}/{len(chapters)} chapters")
        con.close()
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

    print(f"Created: {OUT_DIR}")
    print(f"Chapters: {stats['chapters']}; question placements: {stats['question_placements']}")
    print(f"Question images: {stats['question_images']}; textbook images: {stats['textbook_images']}")
    if stats["missing_question_images"] or stats["missing_textbook_images"]:
        print(f"Missing question images: {stats['missing_question_images']}; missing textbook images: {stats['missing_textbook_images']}")
    print(f"Archives: {len(list(OUT_DIR.rglob('*.zip')))}")


if __name__ == "__main__":
    main()
