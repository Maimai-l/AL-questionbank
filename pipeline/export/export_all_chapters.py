#!/usr/bin/env python3
"""Export every textbook chapter and its topic-matched CAIE questions.

Each chapter gets its own ZIP containing chapter.md and its textbook images (JPEGs
re-encoded at quality 75 when that is smaller), a separate questions.md, question
images, and mark schemes. It only reads the question-bank database and assets; it
never changes them. The batch-generation flow's 章节包 node (manager/flow.py) writes
the same archives through write_chapter(), with the questions the flow selected.

    python3 pipeline/export/export_all_chapters.py [--syllabus 9618] [--chapter 8] [--no-images]

--syllabus and --chapter limit the run. --no-images leaves every image out: the
textbook's image lines are dropped from chapter.md, questions.md has no image
links, and the archive name ends in _no_images.
"""
from __future__ import annotations

import argparse
import io
import json
import re
import sqlite3
import zipfile
from collections import defaultdict
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from lib import paths  # noqa: E402
from pipeline.export import question_md  # noqa: E402

DATA = Path(paths.DATA)
DB = Path(paths.DB)
ASSETS = DATA  # images and books/ live in data/
OUT_DIR = Path(paths.EXPORTS) / "chapters"
IMG_REF = re.compile(r"(?:src|href)=[\"'](imgs/[^\"'#?]+)", re.IGNORECASE)
IMG_LINE = re.compile(r"^[ \t]*(?:<div[^>]*>)?\s*<img [^>]*src=[\"']imgs/[^>]*>\s*(?:</div>)?[ \t]*\n?", re.IGNORECASE | re.MULTILINE)
IMG_TAG = re.compile(r"<img [^>]*src=[\"']imgs/[^>]*>", re.IGNORECASE)


def safe_name(value: str) -> str:
    """Make a stable, human-readable filename fragment."""
    return re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("._") or "chapter"


def markdown_question(question: sqlite3.Row, image_rel: str | None, topic: str | None = None) -> str:
    """The question, or only its parts tagged with topic, and their mark scheme."""
    label = f"{question['paper']} {question['session']} Q{question['q']}"
    labels = question_md.labels_on_topic(question, topic) if topic else []
    all_labels = [p["label"] for p in (question_md.parts_of(question) or {}).get("parts", [])]
    if labels and len(labels) < len(all_labels):
        text, scheme = question_md.parts_md(question, labels)
        marks = sum(p["marks"] or 0 for p in question_md.parts_of(question)["parts"]
                    if p["label"] in labels)
        label += f" ({', '.join(labels)})" + (f" · {marks} marks" if marks else "")
    else:
        text, scheme = question_md.question_text(question), question_md.scheme_text(question)
        if question["marks"] is not None:
            label += f" · {question['marks']} marks"
    lines = [f"### {label}", ""]
    if image_rel:
        lines += [f"![{label}]({image_rel})", ""]
    lines += [text, "", "#### Mark scheme", "", scheme, ""]
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


TEXTBOOK_JPEG_QUALITY = 75     # textbook figures are re-encoded at this quality when that makes them smaller


def add_textbook_image(zf: zipfile.ZipFile, source: Path, archive_name: str, added: set[str]) -> bool:
    """A textbook figure, once. A JPEG is re-encoded (same name, so chapter.md's links
    still work) when that makes it smaller; other images go in as they are."""
    if archive_name in added or not source.is_file():
        return False
    if source.suffix.lower() not in {".jpg", ".jpeg"}:
        return add_file(zf, source, archive_name, added)
    from PIL import Image
    data = source.read_bytes()
    buf = io.BytesIO()
    with Image.open(io.BytesIO(data)) as im:
        im.convert("RGB").save(buf, "JPEG", quality=TEXTBOOK_JPEG_QUALITY, optimize=True, progressive=True)
    added.add(archive_name)
    zf.writestr(archive_name, min(data, buf.getvalue(), key=len), compress_type=zipfile.ZIP_STORED)
    return True


def chapter_stem(chapter, images: bool = True) -> str:
    """The archive name without .zip: <book>_<two-digit chapter>_<title without its
    number>, e.g. 9709_p1_09_Integration, 9709_p23_09_Differential_equations,
    9231_01_Roots_of_polynomial_equations."""
    title = re.sub(r"^(chapter\s+)?\d+\s+", "", chapter["title"], flags=re.IGNORECASE)
    stem = f"{safe_name(chapter['book'] or chapter['syllabus'])}_{chapter['chapter_no']:02d}_{safe_name(title)}"
    return stem if images else stem + "_no_images"


def chapter_path(chapter, images: bool = True) -> Path:
    """Where the chapter's archive goes: one folder per subject,
    exports/chapters/<syllabus>/<stem>.zip (the four 9709 books share 9709/)."""
    return OUT_DIR / safe_name(chapter["syllabus"] or "other") / f"{chapter_stem(chapter, images)}.zip"


def legacy_path(chapter, images: bool = True) -> Path:
    """Where earlier versions put the archive: exports/chapters/<book>/<syllabus>_<book>_<NN>_<title>.zip."""
    stem = f"{chapter['syllabus']}_{safe_name(chapter['book'])}_{chapter['chapter_no']:02d}_{safe_name(chapter['title'])}"
    return OUT_DIR / safe_name(chapter["book"] or chapter["syllabus"] or "other") / f"{stem if images else stem + '_no_images'}.zip"


def remove_legacy(chapter, images: bool = True) -> None:
    """Remove the chapter's archive from the old layout, and its book folder once empty."""
    old = legacy_path(chapter, images)
    if old.is_file() and old != chapter_path(chapter, images):
        old.unlink()
    try:
        if old.parent != OUT_DIR and old.parent.is_dir() and not any(old.parent.iterdir()):
            old.parent.rmdir()
    except OSError:
        pass


def chapter_questions(con: sqlite3.Connection, chapter, ids=None) -> list:
    """Whole questions on the chapter's topic, and questions with only some parts on it
    (part_data), in paper order; with ids, only those questions."""
    rows = con.execute("""
        SELECT id, paper, session, q, marks, topic, question_latex, question_text,
               ms_latex, ms_text, image, q_quality, part_data
        FROM questions
        WHERE syllabus = ? AND (topic = ? OR topic_parts LIKE ?)
        ORDER BY year, month, paper, q, id
    """, (chapter["syllabus"], chapter["topic"], f'%"topic": "{chapter["topic"]}"%'))
    keep = set(ids) if ids is not None else None
    return [q for q in rows if (keep is None or q["id"] in keep)
            and (q["topic"] == chapter["topic"] or question_md.labels_on_topic(q, chapter["topic"]))]


def write_chapter(con: sqlite3.Connection, chapter, out: Path, images: bool = True, ids=None, stats=None) -> dict:
    """One portable ZIP for a chapter: chapter.md with its textbook images in imgs/,
    questions.md with the matched questions (only the parts on the topic when just some
    are), their images in images/questions/, a README and a manifest. With ids, only
    those questions. Written to a temporary file and then put in place, so an existing
    archive is replaced whole. Returns the chapter's manifest entry."""
    stats = stats if stats is not None else defaultdict(int)
    stem = out.stem
    package_root = stem
    out.parent.mkdir(parents=True, exist_ok=True)
    chapter_source = DATA / chapter["path"]
    if not chapter_source.is_file():
        raise FileNotFoundError(f"Missing chapter Markdown: {chapter_source}")
    original = chapter_source.read_text(encoding="utf-8")
    if not images:
        original = IMG_TAG.sub("", IMG_LINE.sub("", original))
    questions = chapter_questions(con, chapter, ids)
    stats["part_placements"] += sum(q["topic"] != chapter["topic"] for q in questions)
    tmp = out.with_name(out.name + ".tmp")
    added: set[str] = set()
    with zipfile.ZipFile(tmp, "w", allowZip64=True) as zf:
        chapter_arc = f"{package_root}/chapter.md"
        question_parts = [f"# 配套 CAIE 真题：{chapter['title']}", "",
                          f"匹配规则：题目与本章同属 `{chapter['syllabus']}` / topic `{chapter['topic']}`；"
                          "只有部分小问属于本 topic 的题，只给出这些小问及其评分细则（原题图仍是整题）。"]
        if not questions:
            question_parts += ["", "_当前没有已标注到这个 topic 的题目。_"]
        for question in questions:
            image_link = None
            if question["image"] and images:
                image_source = ASSETS / question["image"]
                image_arc = f"{package_root}/images/questions/{question['image']}"
                if add_file(zf, image_source, image_arc, added):
                    stats["question_images"] += 1
                if image_source.is_file():
                    image_link = str(Path("images/questions") / question["image"])
                else:
                    stats["missing_question_images"] += 1
            question_parts += ["", markdown_question(question, image_link, chapter["topic"]).rstrip()]
            stats["question_placements"] += 1
        zf.writestr(chapter_arc, original.rstrip() + "\n", compress_type=zipfile.ZIP_DEFLATED)
        zf.writestr(f"{package_root}/questions.md", "\n".join(question_parts) + "\n", compress_type=zipfile.ZIP_DEFLATED)
        stats["chapters"] += 1
        # Preserve the existing imgs/... links in chapter.md.
        for image_ref in sorted(set(IMG_REF.findall(original))):
            image_source = chapter_source.parent / image_ref
            if add_textbook_image(zf, image_source, f"{package_root}/{image_ref}", added):
                stats["textbook_images"] += 1
            elif not image_source.is_file():
                stats["missing_textbook_images"] += 1
        chapter_manifest = {
            "chapter_id": chapter["id"], "syllabus": chapter["syllabus"],
            "book": chapter["book"], "chapter_no": chapter["chapter_no"],
            "title": chapter["title"], "topic": chapter["topic"],
            "questions": len(questions), "file": chapter_arc,
        }
        readme = f"""# {chapter['title']}

This archive contains one textbook chapter, all questions whose `syllabus +
topic` tag matches it, and extracted mark schemes, as text only: no images.
""" if not images else f"""# {chapter['title']}

This archive contains one textbook chapter, all questions whose `syllabus +
topic` tag matches it, their original question images, and extracted mark
schemes.

`chapter.md` is the textbook text with its textbook images in `imgs/`.
`questions.md` contains matched questions, their images, and mark schemes. Open
either file from within this extracted folder to keep image links working.
"""
        zf.writestr(f"{package_root}/README.md", readme, compress_type=zipfile.ZIP_DEFLATED)
        zf.writestr(f"{package_root}/manifest.json", json.dumps(chapter_manifest, ensure_ascii=False, indent=2), compress_type=zipfile.ZIP_DEFLATED)
    tmp.replace(out)
    if out == chapter_path(chapter, images):
        remove_legacy(chapter, images)
    return chapter_manifest


def chapters_of(con: sqlite3.Connection, syllabus=None, chapter_no=None) -> list:
    return [c for c in con.execute("""
        SELECT id, syllabus, book, chapter_no, title, path, topic, topic_name
        FROM chapters
        ORDER BY syllabus, book, chapter_no, id
    """) if (not syllabus or c["syllabus"] == syllabus) and (chapter_no is None or c["chapter_no"] == chapter_no)]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--syllabus")
    ap.add_argument("--chapter", type=int)
    ap.add_argument("--no-images", action="store_true")
    args = ap.parse_args()
    images = not args.no_images
    if not DB.is_file():
        raise FileNotFoundError(DB)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    stats = defaultdict(int)
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    chapters = chapters_of(con, args.syllabus, args.chapter)
    for number, chapter in enumerate(chapters, start=1):
        write_chapter(con, chapter, chapter_path(chapter, images), images, stats=stats)
        if number % 10 == 0 or number == len(chapters):
            print(f"Prepared {number}/{len(chapters)} chapters")
    con.close()

    print(f"Created: {OUT_DIR}")
    print(f"Chapters: {stats['chapters']}; question placements: {stats['question_placements']} "
          f"(by part only: {stats['part_placements']})")
    print(f"Question images: {stats['question_images']}; textbook images: {stats['textbook_images']}")
    if stats["missing_question_images"] or stats["missing_textbook_images"]:
        print(f"Missing question images: {stats['missing_question_images']}; missing textbook images: {stats['missing_textbook_images']}")
    print(f"Archives: {len(list(OUT_DIR.rglob('*.zip')))}")


if __name__ == "__main__":
    main()
