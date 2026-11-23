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
workbook has none.

--schemes fills the mark schemes from the source papers: the 31 question papers and
schemes named in the sources, downloaded to raw/mwb_papers with skills/shared/get_paper.py;
the workbook question is matched to the paper's question by shared words (split_qp.py
splits the paper), and the 2016-2020 scheme table (old_scheme) gives that question's
block. ms_pdf points at raw/mwb_papers (the PDFs are not in data/).
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


# ------------------------------------------------------------------ mark schemes from the source papers

OLD_HDR = re.compile(r"^\s*Question\s+Answer\s+Marks?\b")
OLD_LABEL = re.compile(r"^\s{0,12}(\d{1,2})(\([a-z]\))?(\((?:i{1,3}|iv|vi{0,3}|ix|x)\))?(?=\s\s|\s*$)")
OLD_FURN = re.compile(r"©\s*UCLES|PUBLISHED|^\s*9709/\d\d\s|Cambridge International|Page \d+ of \d+|^\s*Question\s+Answer")
TOTAL = re.compile(r"^\s*Total\s*:?\s*(\d{1,2})\s*$")
WORD = re.compile(r"[a-z]+|\d+(?:\.\d+)?")
PAPERS = os.path.join(paths.RAW, "mwb_papers")


def old_scheme(path):
    """{question: (text, total)} from a 2016-2020 scheme: the table "Question | Answer | Mark |
    Guidance" (Mark singular) with a "Total: n" line closing each part. The text follows the
    bank's 9709 ms_text: a part label opens each block, columns are two spaces apart, a
    part's total stands on a line of its own."""
    import subprocess
    lines = subprocess.run(["pdftotext", "-layout", path, "-"], capture_output=True, text=True).stdout.split("\n")
    start = next((i for i, l in enumerate(lines) if OLD_HDR.match(l)), None)
    if start is None:
        return {}
    out, q = {}, None
    for line in lines[start:]:
        if OLD_FURN.search(line) or not line.strip():
            continue
        t = TOTAL.match(line.replace("Total:", " Total:").strip()) or TOTAL.match(line)
        m = OLD_LABEL.match(line)
        if m:
            q = int(m.group(1))
            out.setdefault(q, [[], 0])
        if q is None:
            continue
        if t:
            out[q][0].append(f"  {t.group(1)}")
            out[q][1] += int(t.group(1))
            continue
        text = re.sub(r" {2,}", "  ", line.strip())
        out[q][0].append(text if m else "  " + text)
    return {k: ("\n".join(v[0]), v[1]) for k, v in out.items()}


START = re.compile(r"^\s{0,8}(\d{1,2})(?=\s*\(|\s{2,}|\s*$)")
PART = re.compile(r"^\s{0,12}(?:\d{1,2})?\s*\((?:[a-z]|i{1,3}|iv|vi{0,3})\)")
ALT = re.compile(r"Alternative|\bAlt\b", re.I)
CODE = re.compile(r"(?<![A-Za-z(])\*?D?[MAB](\d)(?![A-Za-z\d)])")


def any_scheme(path):
    """{question: (text, award total)} from a scheme of any year 2016-2020: past the
    abbreviations, questions start at a left-hand number taken in order 1, 2, 3 (so a
    stray number does not start one); the total adds the award codes (M1 A1 B2), leaving
    out an "Alternative method" until the next part label."""
    import subprocess
    lines = subprocess.run(["pdftotext", "-layout", path, "-"], capture_output=True, text=True).stdout.split("\n")
    out, q, expect, alt = {}, None, 1, False
    for line in lines:
        if OLD_FURN.search(line) or re.search(r"Page \d+|Mark Scheme|Syllabus\s+Paper", line) or not line.strip():
            continue
        m = START.match(line)
        if m and int(m.group(1)) == expect and (expect > 1 or CODE.search(line) or "(" in line[:12]):
            q, expect, alt = expect, expect + 1, False
            out[q] = [[], 0]
        if q is None:
            continue
        if ALT.search(line):
            alt = True
        elif PART.match(line) or (m and int(m.group(1)) == q):
            alt = False
        out[q][0].append(line)
        if not alt:
            out[q][1] += sum(int(d) for d in CODE.findall(line))
    return {k: (compact("\n".join(v[0])), v[1]) for k, v in out.items()}


def compact(text):
    """Layout text as the bank keeps ms_text: the label flush left, columns two spaces apart."""
    out = []
    for line in text.split("\n"):
        if not line.strip() or OLD_FURN.search(line):
            continue
        t = re.sub(r" {2,}", "  ", line.strip())
        out.append(t if OLD_LABEL.match(line) else "  " + t)
    return "\n".join(out)


def words(t):
    return set(WORD.findall((t or "").lower()))


def best_question(text, questions):
    """The paper question whose text shares most words with the workbook's (Jaccard)."""
    w = words(text)
    scored = sorted(((len(w & words(q["text"])) / max(1, len(w | words(q["text"]))), q["q"]) for q in questions),
                    reverse=True)
    return scored[0] if scored else (0, None)


def schemes(a):
    from pipeline.split import split_ms, split_qp
    from pipeline.text.audit_text import classify_ms
    con = db.connect()
    rows = con.execute("SELECT id, topic_note, question_text, marks FROM questions WHERE id LIKE '9709_mwb_%'").fetchall()
    papers, upd, report = {}, [], []
    for r in rows:
        ref = REF.search(r["topic_note"] or "")
        if not ref:
            report.append(f"{r['id']}: 出处不是真题，跳过")
            continue
        code = ref.group(0)
        if code not in papers:
            qp = os.path.join(PAPERS, f"{code}.pdf")
            ms = os.path.join(PAPERS, code.replace("_qp_", "_ms_") + ".pdf")
            if not (os.path.exists(qp) and os.path.exists(ms)):
                papers[code] = None
            else:
                cur = {m["q"]: (compact(m["ms_text"]), m["ms_total"]) for m in split_ms.parse(ms)}
                papers[code] = (split_qp.split_paper(qp), [cur, old_scheme(ms), any_scheme(ms)])
        if not papers[code]:
            report.append(f"{r['id']}: 没有 {code} 的原卷或评分细则")
            continue
        qs, ms = papers[code]
        score, q = best_question(r["question_text"], qs)
        if q is None or score < 0.3:
            report.append(f"{r['id']}: 在 {code} 里找不到对应的题(最高相似度 {score:.2f})")
            continue
        paper_q = next(x for x in qs if x["q"] == q)
        marks, mparts = paper_q.get("marks"), paper_q.get("marks_parts")
        # parts and their marks stay empty: split_parts.py splits the workbook text by its own
        # labels (136 of 145); handed the paper's labels it splits only 58
        labels, mparts = None, None
        # three readings of the scheme (the current table, the 2017-18 table with "Total:",
        # any year): the first whose total is the paper's marks, else the last that has it
        found = [p[q] for p in ms if q in p and p[q][0].strip()]
        if not found:
            report.append(f"{r['id']}: {code} 第 {q} 题，评分细则里没有这一题")
            continue
        text, total = next((f for f in found if f[1] == marks), found[-1])
        codes = re.findall(r"(?<![A-Za-z])(\*?D?[MAB]\d|FT|CAO|CWO|AEF|OE|SOI|ISW|AWRT|WWW|AG)(?![A-Za-z])", text)
        agree = int(bool(marks) and total == marks)
        if not agree:
            report.append(f"{r['id']}: {code} 第 {q} 题，评分细则合计 {total},原卷 {marks},练习册 {r['marks']}")
        note = re.sub(r";原卷第 \d+ 题.*$", "", r["topic_note"]) + f";原卷第 {q} 题(相似度 {score:.2f})"
        upd.append((text, json.dumps(codes), total, agree, classify_ms(text, True),
                    os.path.relpath(os.path.join(PAPERS, code.replace("_qp_", "_ms_") + ".pdf"), paths.ROOT),
                    note, marks, json.dumps(mparts) if mparts else None,
                    json.dumps(labels) if labels else None, r["id"]))
    for x in report:
        print(x)
    print(f"{len(upd)} 题找到评分细则，{sum(u[3] for u in upd)} 题合计与题面一致")
    if a.write:
        con.executemany("UPDATE questions SET ms_text=?, mark_codes=?, ms_total=?, totals_agree=?, ms_quality=?, "
                        "ms_pdf=?, topic_note=?, marks=?, marks_parts=?, parts=? WHERE id=?", upd)
        con.executemany("UPDATE q_fts SET ms_text=? WHERE id=?", [(u[0], u[-1]) for u in upd])
        con.commit()
        print("已写入")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--schemes", action="store_true",
                    help="不重新入库，只从原卷(raw/mwb_papers,get_paper.py 下载)补评分细则")
    a = ap.parse_args()
    if a.schemes:
        return schemes(a)
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
