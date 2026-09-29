#!/usr/bin/env python3
"""Import the OCR'd TMUA/TARA bank into caie.db and export readable Markdown.

The upstream material is page-level OCR, not reliably pre-segmented questions.
It is therefore stored faithfully as documents and pages rather than forcing
possibly wrong question boundaries into the CAIE-specific ``questions`` table.
"""
from __future__ import annotations

import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parent
SOURCE = PROJECT / "admissions_ocr_source"
DB = ROOT / "caie.db"
EXPORTS = PROJECT / "exports"

IMG_HTML = re.compile(r'((?:src|href)=["\'])imgs/', re.IGNORECASE)
IMG_MD = re.compile(r'(\]\()imgs/', re.IGNORECASE)


def document_title(parts: tuple[str, ...]) -> str:
    """Turn a document path into a concise display title."""
    return " / ".join(piece.replace("-", " ") for piece in parts)


def page_number(path: Path) -> int:
    match = re.fullmatch(r"page_(\d+)\.md", path.name)
    return int(match.group(1)) if match else 0


def read_document(document_dir: Path) -> tuple[str, list[tuple[int, str]]]:
    pages = []
    relative = document_dir.relative_to(PROJECT).as_posix()
    image_prefix = "../" + relative + "/imgs/"
    for page in sorted(document_dir.glob("page_*.md"), key=page_number):
        text = page.read_text(encoding="utf-8").strip()
        text = IMG_HTML.sub(r"\1" + image_prefix, text)
        text = IMG_MD.sub(r"\1" + image_prefix, text)
        pages.append((page_number(page), text))
    joined = "\n\n".join(
        f"<!-- {relative}/{page_no:04d} -->\n\n{text}" for page_no, text in pages
    )
    return joined + ("\n" if joined else ""), pages


def setup(con: sqlite3.Connection) -> None:
    con.executescript("""
        CREATE TABLE IF NOT EXISTS exam_bank_documents (
            id TEXT PRIMARY KEY,
            exam TEXT NOT NULL,
            collection TEXT NOT NULL,
            document_key TEXT NOT NULL,
            title TEXT NOT NULL,
            source_path TEXT NOT NULL UNIQUE,
            page_count INTEGER NOT NULL,
            content_md TEXT NOT NULL,
            imported_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_exam_bank_documents_exam
            ON exam_bank_documents(exam, collection, document_key);

        CREATE TABLE IF NOT EXISTS exam_bank_pages (
            document_id TEXT NOT NULL REFERENCES exam_bank_documents(id) ON DELETE CASCADE,
            page_no INTEGER NOT NULL,
            content_md TEXT NOT NULL,
            PRIMARY KEY (document_id, page_no)
        );
        CREATE INDEX IF NOT EXISTS idx_exam_bank_pages_document
            ON exam_bank_pages(document_id, page_no);
    """)


def import_bank(con: sqlite3.Connection) -> dict[str, int]:
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    counts = {"TMUA": 0, "TARA": 0, "pages": 0}
    for exam in ("TMUA", "TARA"):
        root = SOURCE / exam
        for document_dir in sorted({page.parent for page in root.rglob("page_*.md")}):
            relative = document_dir.relative_to(SOURCE / exam)
            parts = relative.parts
            collection = "/".join(parts[:-1]) or "general"
            document_key = parts[-1]
            document_id = f"admissions_ocr:{exam.lower()}:{relative.as_posix()}"
            content, pages = read_document(document_dir)
            con.execute("""
                INSERT INTO exam_bank_documents
                    (id, exam, collection, document_key, title, source_path,
                     page_count, content_md, imported_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    collection=excluded.collection, document_key=excluded.document_key,
                    title=excluded.title, source_path=excluded.source_path,
                    page_count=excluded.page_count, content_md=excluded.content_md,
                    imported_at=excluded.imported_at
            """, (document_id, exam, collection, document_key,
                  document_title(parts), document_dir.relative_to(PROJECT).as_posix(),
                  len(pages), content, now))
            con.execute("DELETE FROM exam_bank_pages WHERE document_id = ?", (document_id,))
            con.executemany("""
                INSERT INTO exam_bank_pages (document_id, page_no, content_md)
                VALUES (?, ?, ?)
            """, [(document_id, number, text) for number, text in pages])
            counts[exam] += 1
            counts["pages"] += len(pages)
    return counts


def export_exam(con: sqlite3.Connection, exam: str) -> Path:
    EXPORTS.mkdir(parents=True, exist_ok=True)
    out = EXPORTS / f"{exam.lower()}_question_bank.md"
    rows = list(con.execute("""
        SELECT collection, document_key, title, source_path, page_count, content_md
        FROM exam_bank_documents
        WHERE exam = ?
        ORDER BY collection, document_key
    """, (exam,)))
    lines = [f"# {exam} 题库", "",
             "由本地官方 OCR 材料从 SQLite 导出。图片仍引用项目中的 `slim/` 文件。",
             ""]
    current_collection = None
    for row in rows:
        if row["collection"] != current_collection:
            current_collection = row["collection"]
            lines += [f"## {current_collection.replace('/', ' / ')}", ""]
        lines += [f"### {row['title']}", "",
                  f"_来源：`{row['source_path']}` · {row['page_count']} 页_", "",
                  row["content_md"].rstrip(), "", "---", ""]
    out.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return out


def main() -> None:
    if not SOURCE.is_dir():
        raise FileNotFoundError(f"Missing source folder: {SOURCE}")
    with sqlite3.connect(DB) as con:
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA foreign_keys = ON")
        setup(con)
        counts = import_bank(con)
        tmua = export_exam(con, "TMUA")
        tara = export_exam(con, "TARA")
    print(f"Imported TMUA: {counts['TMUA']} documents")
    print(f"Imported TARA: {counts['TARA']} documents")
    print(f"Imported pages: {counts['pages']}")
    print(f"Exported: {tmua}")
    print(f"Exported: {tara}")


if __name__ == "__main__":
    main()
