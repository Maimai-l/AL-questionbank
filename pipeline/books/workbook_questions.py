#!/usr/bin/env python3
"""Add the questions of the CIE Mechanics workbook (练习册) to the bank.

    python3 pipeline/books/workbook_questions.py [--write]

The workbook (raw/textbooks/cie_mech_wb.pdf, labels in pipeline/tags/labels_mech.json)
prints each question as a picture of the original paper between a number line
("1.") and a source line ("(9709_s17_qp_41)" or a textbook exercise); both lines
are in the text layer, so the question is cropped from the top of its number to
the bottom of its source, across a page break when it runs on. The text is the
OCR of the workbook pages (raw/book_ocr/cie_mech_wb/pages, ocr_book_pages.py) cut
the same way as pipeline/tags/chapter_labels.py cuts it, with the figures the OCR
kept copied to data/img9709/fig/.

Rows: id 9709_mwb_ch05_q03 (chapter 5, question 3 of the workbook), syllabus 9709,
component 4, series "mwb", year from the source paper, topic from the chapter
(CHAPTER_TOPIC), tags 精选 + the workbook + the chapter label. No mark scheme: the
workbook has none (source papers are noted in topic_note so the scheme can be
fetched later).
"""
import argparse
import glob
import json
import os
import re
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import pymupdf  # noqa: E402

from lib import db, paths, png16  # noqa: E402

BOOK = "cie_mech_wb"
TABLE = os.path.join(paths.ROOT, "pipeline", "tags", "labels_mech.json")
PDF = os.path.join(paths.TEXTBOOKS, f"{BOOK}.pdf")
PAGES = os.path.join(paths.RAW, "book_ocr", BOOK, "pages")
IMG = os.path.join(paths.DATA, "img9709")
TAGS = ["精选", "CIE Mechanics 练习册"]
# the workbook's chapters in the 9709 syllabus (most frequent pairing in the bank's paper 4)
CHAPTER_TOPIC = {"1": "4.2", "2": "4.4", "3": "4.1", "4": "4.4", "5": "4.4",
                 "6": "4.2", "7": "4.3", "8": "4.5", "9": "4.5"}
NUM = re.compile(r"^\s*(\d{1,3})\s*[.．]\s*$")
SRC = re.compile(r"^\s*\((.*(?:\d{4}_[msw]\d\d_qp_\d\d|第\s*\d+\s*题).*)\)\s*$")
REF = re.compile(r"(\d{4})_([msw])(\d\d)_qp_(\d)(\d)")
QNUM = re.compile(r"(?m)^#{0,4}\s*(\d{1,3})\s*[.．]\s*$")
SOURCE = re.compile(r"\(([^()\n]*(?:\d{4}_[msw]\d\d_qp_\d\d|第\s*\d+\s*题)[^()\n]*)\)")
X0, X1, ZOOM = 80, 515, 2.0


def layout(doc):
    """[(n, [(page, y0, y1)...], source)] from the text layer, in order."""
    marks = []
    for pno, page in enumerate(doc, 1):
        for b in page.get_text("dict")["blocks"]:
            if b["type"] != 0:
                continue
            t = " ".join(s["text"] for l in b["lines"] for s in l["spans"]).strip()
            if NUM.match(t):
                marks.append(("n", pno, b["bbox"][1], int(NUM.match(t).group(1))))
            elif SRC.match(t):
                marks.append(("s", pno, b["bbox"][3], SRC.match(t).group(1).strip()))
    marks.sort(key=lambda m: (m[1], m[2]))
    out = []
    for k, m in enumerate(marks):
        if m[0] != "n":
            continue
        end = next((e for e in marks[k + 1:] if e[0] == "s"), None)
        nxt = next((e for e in marks[k + 1:] if e[0] == "n"), None)
        if not end or (nxt and (nxt[1], nxt[2]) < (end[1], end[2])):
            sys.exit(f"第 {m[1]} 页第 {m[3]} 题没有出处行")
        pieces = []
        for p in range(m[1], end[1] + 1):
            top = m[2] - 4 if p == m[1] else 40
            if p == end[1]:
                bottom = end[2] + 4
            else:
                imgs = [b["bbox"][3] for b in doc[p - 1].get_text("dict")["blocks"] if b["type"] == 1]
                bottom = max(imgs + [top + 1]) + 4
            pieces.append((p, top, bottom))
        out.append((m[3], pieces, end[3]))
    return out


def ocr_questions():
    """Question markdown from the OCR pages, figures kept, cut as chapter_labels cuts them."""
    pages = sorted(glob.glob(os.path.join(PAGES, "page_*.md")))
    text = "".join(open(p, encoding="utf-8").read() + "\n" for p in pages)
    qs = [m for m in QNUM.finditer(text)]
    out = []
    for k, m in enumerate(qs):
        end = qs[k + 1].start() if k + 1 < len(qs) else len(text)
        body = SOURCE.sub("", text[m.end():end])
        body = re.sub(r"(?mi)^#{0,4}\s*Chapter\s+\d+.*$", "", body)
        out.append(re.sub(r"\n{3,}", "\n\n", body).strip())
    return out


def render(doc, pieces, path):
    tiles = [doc[p - 1].get_pixmap(matrix=pymupdf.Matrix(ZOOM, ZOOM), alpha=False, colorspace=pymupdf.csGRAY,
                                   clip=pymupdf.Rect(X0, y0, X1, y1)) for p, y0, y1 in pieces]
    w, h = max(t.width for t in tiles), sum(t.height for t in tiles)
    out = pymupdf.Pixmap(pymupdf.csGRAY, pymupdf.IRect(0, 0, w, h), False)
    out.clear_with(255)
    y = 0
    for t in tiles:
        t.set_origin(0, y)
        out.copy(t, t.irect)
        y += t.height
    png16.save_pixmap(out, path)


def figures(md, qid):
    """Copy the figures the OCR kept to data/img9709/fig/<qid>_<n>.jpg; rewrite their src."""
    os.makedirs(os.path.join(IMG, "fig"), exist_ok=True)
    n = 0

    def one(m):
        nonlocal n
        src = os.path.join(PAGES, m.group(2))
        if not os.path.exists(src):
            return m.group(0)
        n += 1
        name = f"{qid}_{n:02d}{os.path.splitext(src)[1]}"
        shutil.copyfile(src, os.path.join(IMG, "fig", name))
        return f'{m.group(1)}img9709/fig/{name}{m.group(3)}'
    return re.sub(r'(<img\s[^>]*?src=")([^"]+)(")', one, md), n


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    spec = json.load(open(TABLE, encoding="utf-8"))
    names = {c: lab["name"] for c, lab in spec["labels"].items()}
    order = sorted(spec["labels"], key=lambda c: spec["labels"][c]["pdf_from"])
    doc = pymupdf.open(PDF)
    lay, texts = layout(doc), ocr_questions()
    if len(lay) != len(texts):
        sys.exit(f"文字层 {len(lay)} 题，OCR {len(texts)} 题，对不上")
    rows, chap, last = [], None, 0
    for (n, pieces, source), md in zip(lay, texts):
        if chap is None or (n == 1 and last != 0):
            chap = order[0] if chap is None else order[order.index(chap) + 1]
        last = n
        qid = f"9709_mwb_ch{int(chap):02d}_q{n:02d}"
        ref = REF.search(source)
        image = os.path.join(IMG, f"{qid}.png")
        if a.write:
            render(doc, pieces, image)
            md, nfig = figures(md, qid)
        else:
            nfig = md.count("<img")
        marks = sum(int(x) for x in re.findall(r"\[\s*(\d{1,2})\s*\]", md)) or None
        rows.append({
            "id": qid, "syllabus": "9709", "component": "4", "component_name": "Mechanics",
            "paper": "9709/4", "variant": ref.group(5) if ref else "", "year": 2000 + int(ref.group(3)) if ref else 2018,   # textbook exercises: the 2018 coursebook
            "month": 0, "session": "CIE Mechanics 练习册", "series": "mwb", "q": n, "parts": None,
            "marks": marks, "marks_parts": None,
            "topic": CHAPTER_TOPIC[chap], "topic_name": None, "topic_source": "workbook",
            "topic_note": f"练习册第 {chap} 章第 {n} 题，出处 {source}",
            "question_text": re.sub(r"<[^>]+>", " ", md), "question_latex": md,
            "ms_text": None, "ms_latex": None, "ms_quality": "missing", "q_quality": "ok" if md else "missing",
            "image": os.path.relpath(image, paths.DATA), "qp_pdf": None,
            "qp_pages": json.dumps([p - 1 for p, _, _ in pieces]), "has_diagram": int(nfig > 0),
            "tags": json.dumps(TAGS + [f"{spec['prefix']} {chap} {names[chap]}"], ensure_ascii=False),
        })
    by = {}
    for r in rows:
        by[r["id"][11:13]] = by.get(r["id"][11:13], 0) + 1
    print(f"{len(rows)} 题;各章 {by};带图 {sum(r['has_diagram'] for r in rows)};"
          f"无分值 {sum(1 for r in rows if not r['marks'])}")
    if not a.write:
        print("未写入;加 --write 写入")
        return
    con = db.connect()
    db.ensure_tags(con)
    names_row = {r[0]: r[1] for r in con.execute(
        "SELECT topic, topic_name FROM questions WHERE syllabus = '9709' AND topic_name IS NOT NULL")}
    for r in rows:
        r["topic_name"] = names_row.get(r["topic"])
    con.execute("DELETE FROM questions WHERE id LIKE '9709\\_mwb\\_%' ESCAPE '\\'")
    con.execute("DELETE FROM q_fts WHERE id LIKE '9709_mwb_%'")
    cols = list(rows[0])
    con.executemany(f"INSERT INTO questions ({','.join(cols)}) VALUES ({','.join('?' * len(cols))})",
                    [[r[c] for c in cols] for r in rows])
    con.executemany("INSERT INTO q_fts (id, question_text, ms_text, topic_name) VALUES (?, ?, ?, ?)",
                    [(r["id"], r["question_text"], None, r["topic_name"]) for r in rows])
    con.commit()
    print(f"写入 {len(rows)} 题")


if __name__ == "__main__":
    main()
