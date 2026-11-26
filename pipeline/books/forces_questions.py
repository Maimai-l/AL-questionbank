#!/usr/bin/env python3
"""The Edexcel "Force Questions" practice PDF (data/sources/WPH/forces/) as questions.

    python3 -I pipeline/books/forces_questions.py extract
    python3 pipeline/ocr/ocr.py raw/book_questions/forces/ocr_input.json data/imgWPH \\
        raw/ocr/q_WPH_frc_fig.jsonl 4 --pack 10 --figures data/imgWPH/fig
    python3 pipeline/books/forces_questions.py add [--write]
    python3 pipeline/text/split_parts.py --syllabus WPH --write

forces_1_3_2.pdf (user's file "1.3.2 Forces", 2026-11-26): 19 pages of structured
questions numbered 8-23 from the old Edexcel A level (Unit 1), with a text layer and
the diagrams drawn as vectors; no mark scheme. A question runs from its number in
the left margin ("8.") to its "(Total n marks)", across pages; it is cropped as
kinematics_questions.py crops (150 dpi, 16-level grey) to data/imgWPH/WPH_frc_qNN.png,
read with PaddleOCR keeping the figures, and stored as series "frc" (one "paper"),
tags 精选 + WPH Forces + the file. Marks are the printed Total.
"""
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import pymupdf  # noqa: E402

from lib import db, paths  # noqa: E402
from pipeline.books.kinematics_questions import ZOOM, ocr_results, plain, render, tidy  # noqa: E402

SRC = os.path.join(paths.DATA, "sources", "WPH", "forces")
PDF = "forces_1_3_2.pdf"
WORK = os.path.join(paths.RAW, "book_questions", "forces")
CACHE = os.path.join(paths.RAW, "ocr", "q_WPH_frc_fig.jsonl")
IMG = os.path.join(paths.DATA, "imgWPH")
SERIES, NAME = "frc", "Edexcel Force Questions(1.3.2 Forces)"
TAGS = ["精选", "WPH Forces", "Edexcel Force Questions 1.3.2"]
SUPPLIED = 2026
NUM = re.compile(r"^(\d{1,2})\.$")
TOTAL = re.compile(r"^\(Total (\d+) marks?\)$")


def lines(page):
    for b in page.get_text("dict")["blocks"]:
        if b["type"] == 0:
            for l in b["lines"]:
                yield "".join(s["text"] for s in l["spans"]).strip(), l["bbox"]


def bottom(page):
    """The lowest ink on a page above its footer: text lines and vector drawings."""
    ys = [bb[3] for t, bb in lines(page) if t and bb[3] < page.rect.height - 40]
    ys += [d["rect"].y1 for d in page.get_drawings() if d["rect"].y1 < page.rect.height - 40]
    return max(ys + [60])


def layout(doc):
    marks = []
    for pno, page in enumerate(doc, 1):
        for t, bb in lines(page):
            if NUM.match(t) and bb[0] < 70:
                marks.append(("n", pno, bb[1], int(NUM.match(t).group(1))))
            elif TOTAL.match(t):
                marks.append(("t", pno, bb[3], int(TOTAL.match(t).group(1))))
    marks.sort(key=lambda m: (m[1], m[2]))
    out = []
    for k, m in enumerate(marks):
        if m[0] != "n":
            continue
        end = next(e for e in marks[k + 1:] if e[0] == "t")
        pieces = [(p, m[2] - 6 if p == m[1] else 30, end[2] + 4 if p == end[1] else bottom(doc[p - 1]) + 4)
                  for p in range(m[1], end[1] + 1)]
        out.append({"n": m[3], "pieces": pieces, "total": end[3]})
    return out


LABEL = re.compile(r"^\(([a-h]|i{1,3}|iv|vi{0,3})\)$")
PMARK = re.compile(r"^\((\d{1,2})\)$")
ANSWER_LINE = re.compile(r"\n*\s*\$\$[^$]*?\\cdots[^$]*\$\$\s*")      # "Force = ......" read as a formula


def tokens(doc, pieces):
    """The question's part labels and printed marks, in reading order, from the text layer:
    [("label", "a"), ("label", "i"), ("marks", 2), ...]."""
    out = []
    for p, y0, y1 in pieces:
        found = []
        for t, bb in lines(doc[p - 1]):
            if not (y0 <= bb[1] <= y1):
                continue
            if LABEL.match(t) and bb[0] < 120:
                found.append((bb[1], bb[0], ("label", LABEL.match(t).group(1))))
            elif PMARK.match(t) and bb[0] > 400:
                found.append((bb[1], bb[0], ("marks", int(PMARK.match(t).group(1)))))
        out += [x[2] for x in sorted(found)]
    return out


def put_marks(latex, toks):
    """Write each printed mark "[n]" at the end of its part in the OCR text (the OCR drops
    the right-hand "(n)"): a mark belongs to the last label before it; it goes just before
    the next label's occurrence in the text, labels being matched in order."""
    labels = [v for k, v in toks if k == "label"]
    owner, last = {}, None
    for k, v in toks:
        if k == "label":
            last = len([1 for kk, _ in toks[:toks.index((k, v))] if kk == "label"])
        else:
            owner.setdefault(last, []).append(v)
    pos, at = [], 0                       # where each label stands in the text
    for lab in labels:
        m = re.compile(r"(?m)(^|\s)\(" + re.escape(lab) + r"\)").search(latex, at)
        if not m:
            return latex, False
        pos.append(m.start() + len(m.group(1)))
        at = m.end()
    cuts = pos[1:] + [len(latex)]
    for i in sorted(owner, key=lambda k: -1 if k is None else k, reverse=True):
        end = cuts[i] if i is not None else (pos[0] if pos else len(latex))
        stamp = " ".join(f"[{v}]" for v in owner[i])
        latex = latex[:end].rstrip() + f" {stamp}\n\n" + latex[end:].lstrip()
    return latex, True


def parts_of(n, toks):
    """(["21(a)", "21(b)(i)", ...], [3, 2, ...]) from the text layer's labels and marks;
    (None, None) for a question with no labels."""
    labels, marks, letter, roman, since = [], [], None, None, 0
    for k, v in toks:
        if k == "label":
            if v in ("i", "ii", "iii", "iv", "v", "vi", "vii") and (letter or labels or v != "i"):
                roman = v
                since += 1
            else:
                letter, roman, since = v, None, 0
        else:
            if letter is None and roman is None:
                continue
            if since > 1:            # one mark for several sub-parts (20(b)(i)-(ii)): the letter's
                roman = None
            since = 0
            lab = f"{n}" + (f"({letter})" if letter else "") + (f"({roman})" if roman else "")
            if labels and labels[-1] == lab:
                marks[-1] += v
            else:
                labels.append(lab)
                marks.append(v)
    return (labels, marks) if labels else (None, None)


def extract():
    doc = pymupdf.open(os.path.join(SRC, PDF))
    qs = layout(doc)
    os.makedirs(WORK, exist_ok=True)
    for q in qs:
        q["id"] = f"WPH_{SERIES}_q{q['n']:02d}"
        q["image"] = f"{q['id']}.png"
        render(doc, [(p - 1, 40, y0, 565, y1) for p, y0, y1 in q["pieces"]], os.path.join(IMG, q["image"]))
        q["pages"] = [p - 1 for p, _, _ in q["pieces"]]
        q["tokens"] = tokens(doc, q["pieces"])
    json.dump(qs, open(os.path.join(WORK, "questions.json"), "w"), indent=1)
    json.dump([{"image": q["image"]} for q in qs], open(os.path.join(WORK, "ocr_input.json"), "w"))
    print(f"{len(qs)} 题:{' '.join(str(q['n']) for q in qs)};"
          f"跨页 {sum(1 for q in qs if len(q['pieces']) > 1)} 题")


def add(write):
    from pipeline.ocr.apply_reocr import normalise
    from pipeline.text.audit_text import classify_q
    qs = json.load(open(os.path.join(WORK, "questions.json")))
    cache = ocr_results(CACHE)
    rows = []
    for q in qs:
        o = cache.get(q["id"])
        latex = tidy(normalise(o["latex"])) if o else None
        if latex:
            latex = re.sub(r"^\s*\d{1,2}\.\s*", "", latex)          # the file's own number
            latex = ANSWER_LINE.sub("\n\n", latex)
            latex, ok = put_marks(latex, [tuple(t) for t in q["tokens"]])
            printed = sum(v for k, v in q["tokens"] if k == "marks")
            if not ok:
                print(f"  {q['id']}: 小问标号在 OCR 文字里对不上，分值没放回")
            elif printed != q["total"]:
                print(f"  {q['id']}: 各小问分值之和 {printed} ≠ Total {q['total']}")
        grade = classify_q(latex) if latex else "missing"
        parts, mparts = parts_of(q["n"], [tuple(t) for t in q["tokens"]])
        if parts and sum(mparts) != q["total"]:
            parts, mparts = None, None
        if grade != "ok":
            print(f"  {q['id']}: OCR 评为 {grade}")
        rows.append({
            "id": q["id"], "syllabus": "WPH", "component": SERIES, "component_name": NAME,
            "paper": f"WPH/{SERIES}", "variant": "", "year": SUPPLIED, "month": 0, "session": NAME,
            "series": SERIES, "q": q["n"], "parts": json.dumps(parts) if parts else None,
            "marks": q["total"], "marks_parts": json.dumps(mparts) if mparts else None,
            "topic": None, "topic_name": None,
            "topic_note": f"出处:{PDF} 第 {q['n']} 题(旧版 Edexcel A level 结构题，未附评分细则);year 取提供年份 {SUPPLIED}",
            "question_text": plain(latex) if latex else None, "question_latex": latex,
            "q_quality": "ok" if grade == "ok" else ("partial" if latex else "missing"),
            "image": f"imgWPH/{q['image']}", "qp_pdf": PDF, "qp_pages": json.dumps(q["pages"]),
            "has_diagram": int(bool(o and o.get("figures"))),
            "ms_text": None, "ms_latex": None, "ms_quality": "missing", "qtype": None,
            "tags": json.dumps(TAGS, ensure_ascii=False)})
    print(f"{len(rows)} 题;带插图 {sum(r['has_diagram'] for r in rows)};总分 {sum(r['marks'] for r in rows)}")
    if not write:
        print("未写入;加 --write 写入")
        return
    con = db.connect()
    db.ensure_tags(con)
    con.execute("DELETE FROM questions WHERE id LIKE ? ESCAPE '\\'", (f"WPH\\_{SERIES}\\_%",))
    con.execute("DELETE FROM q_fts WHERE id LIKE ?", (f"WPH_{SERIES}_%",))
    cols = list(rows[0])
    con.executemany(f"INSERT INTO questions ({','.join(cols)}) VALUES ({','.join('?' * len(cols))})",
                    [[r[c] for c in cols] for r in rows])
    con.executemany("INSERT INTO q_fts (id, question_text, ms_text, topic_name) VALUES (?, ?, ?, ?)",
                    [(r["id"], r["question_latex"] or r["question_text"], None, None) for r in rows])
    con.commit()
    print(f"写入 {len(rows)} 题")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["extract", "add"])
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    extract() if a.cmd == "extract" else add(a.write)


if __name__ == "__main__":
    main()
