#!/usr/bin/env python3
"""The three Edexcel IAL Kinematics practice PDFs (data/sources/WPH/kinematics/) as questions.

    python3 -I pipeline/books/kinematics_questions.py extract
    python3 pipeline/ocr/ocr.py raw/book_questions/kinematics/ocr_input.json data/imgWPH \\
        raw/ocr/q_WPH_kin_fig.jsonl 4 --pack 10 --figures data/imgWPH/fig
    python3 pipeline/books/kinematics_questions.py marks     # -> raw/ocr/q_WPH_kin_fig_marked.jsonl
    python3 pipeline/books/kinematics_questions.py add [--write]
    python3 pipeline/text/split_parts.py --syllabus WPH --write

Three sets, one "paper" each (series = component, paper WPH/<series>):

kpmt  kinematics_pmt_questions.pdf: 63 scanned pages (PhysicsAndMathsTutor), structured
      questions cut from past papers. The text layer holds only "Q1." ... "Q31." and
      the page numbers; the page content is pictures. A question runs from its "Qn."
      to the next one, over pages; a page without pictures (59-63) is skipped.
ktop  kinematics_pmt_qp.pdf: 7 pages, PMT "Kinematics - Questions by Topic" (IAL). No
      text layer at all (printed to PDF as outlines), so the pages are read once with
      PaddleOCR (raw/book_ocr/kinematics/ktop_pages.jsonl, kept) for the boxes of "Qn."
      and "(Total for question = n mark)"; a question runs from the one to the other.
kmcq  kinematics_mcq.pdf: 6 pages of 56 multiple-choice questions in two columns, with
      session headings (May 02, June 10) and the key at the end ("1-D, 2-A, ...").
      A question runs from its number to the next number, heading or the key, in
      reading order (left column, then right, then the next page).

Crops are 150 dpi, 16-level grey (lib/png16.py), as book_questions.py makes them:
data/imgWPH/WPH_<series>_qNN.png. `extract` writes them and
raw/book_questions/kinematics/questions.json (+ ocr_input.json for ocr.py). `add`
puts the rows in (replacing WPH_kpmt_/ktop_/kmcq_ rows): question_latex is the OCR
(apply_reocr.normalise), question_text the text layer (kmcq) or the OCR without its
markup; marks are the [n] of kpmt (which the OCR drops: `marks` finds them, see
marks_step), the Total of ktop, 1 for kmcq. A ktop question
whose OCR text matches a kpmt question (word Jaccard >= DUP) is left out and its tag
goes on the kpmt row. kmcq: qtype mcq, answer from the key, the scheme stored as the
9702 paper 1 rows store theirs ("5  B  |  1", ms_quality ok).
"""
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from lib import db, paths, png16  # noqa: E402

SRC = os.path.join(paths.DATA, "sources", "WPH", "kinematics")
WORK = os.path.join(paths.RAW, "book_questions", "kinematics")
PAGE_OCR = os.path.join(paths.RAW, "book_ocr", "kinematics", "ktop_pages.jsonl")
OCR_CACHE = os.path.join(paths.RAW, "ocr", "q_WPH_kin_fig.jsonl")
IMG = os.path.join(paths.DATA, "imgWPH")
DPI = 150
ZOOM = DPI / 72.0
DUP = 0.5
MAX_PAGES = 100          # docs/pipeline.md: one OCR job, at most 100 pages
SUPPLIED = 2026          # the year the user handed the files over (2026-11-25)

SETS = {
    "kpmt": {"pdf": "kinematics_pmt_questions.pdf", "tag": "PMT Kinematics 真题汇编",
             "name": "PMT Kinematics 真题汇编", "x": (86, 526)},
    "ktop": {"pdf": "kinematics_pmt_qp.pdf", "tag": "PMT IAL Questions by Topic: Kinematics",
             "name": "PMT IAL Questions by Topic: Kinematics", "x": (50, 562)},
    "kmcq": {"pdf": "kinematics_mcq.pdf", "tag": None,            # with the years: see mcq_tag()
             "name": "Kinematics 选择题"},
}
COMMON_TAGS = ["精选", "WPH Kinematics"]
COLS = [(16, 295), (295, 584)]          # kmcq: the two columns
MONTHS = {"jan": 1, "feb": 2, "mar": 3, "may": 5, "jun": 6, "june": 6, "nov": 11, "oct": 10}
SESSION = re.compile(r"^(May|June|Jun|Nov|Jan|Oct|Mar)\.?\s+(\d{2})\.?$")


def mcq_tag(years):
    return f"Kinematics 选择题 {min(years)}–{max(years)}"


# ------------------------------------------------------------------ rendering

def ink_rows(page, x0, x1, y0, y1):
    """(first, last) y with ink in the box (1 px per pt), or None."""
    import pymupdf
    y0, y1 = max(0, y0), min(page.rect.height, y1)
    if y1 - y0 < 2:
        return None
    pix = page.get_pixmap(clip=pymupdf.Rect(x0, y0, x1, y1), colorspace=pymupdf.csGRAY, alpha=False)
    w, h, s = pix.width, pix.height, pix.samples
    rows = [y for y in range(h) if min(s[y * w:(y + 1) * w]) < 160]
    if not rows:
        return None
    k = (y1 - y0) / h
    return y0 + rows[0] * k, y0 + (rows[-1] + 1) * k


def render(doc, pieces, path):
    """Stack the pieces [(page index, x0, y0, x1, y1)] into one PNG, as book_questions.render."""
    import pymupdf
    tiles = [doc[p].get_pixmap(matrix=pymupdf.Matrix(ZOOM, ZOOM), alpha=False, colorspace=pymupdf.csGRAY,
                               clip=pymupdf.Rect(x0, y0, x1, y1)) for p, x0, y0, x1, y1 in pieces]
    w, h = max(t.width for t in tiles), sum(t.height for t in tiles)
    out = pymupdf.Pixmap(pymupdf.csGRAY, pymupdf.IRect(0, 0, w, h), False)
    out.clear_with(255)
    y = 0
    for t in tiles:
        t.set_origin(0, y)
        out.copy(t, t.irect)
        y += t.height
    png16.save_pixmap(out, path)


# ------------------------------------------------------------------ kpmt: labels in a scanned file

def layout_kpmt(doc):
    x0, x1 = SETS["kpmt"]["x"]
    labels, pics = [], {}
    for p, page in enumerate(doc):
        for w in page.get_text("words"):
            m = re.fullmatch(r"Q(\d{1,2})\.", w[4])
            if m:
                labels.append((p, w[1], int(m.group(1))))
        pics[p] = [b["bbox"] for b in page.get_text("dict")["blocks"] if b["type"] == 1]
    labels.sort()
    out = []
    for k, (p0, y0, n) in enumerate(labels):
        nxt = labels[k + 1] if k + 1 < len(labels) else (len(doc), 0, None)
        pieces = []
        for p in range(p0, min(nxt[0], len(doc) - 1) + 1):
            top = y0 - 3 if p == p0 else None
            bottom = nxt[1] - 3 if p == nxt[0] else None
            # the pictures below the label and above the next one (a label sits between two)
            own = [b for b in pics[p] if (top is None or b[1] >= top) and (bottom is None or b[3] <= bottom + 3)]
            if not own:
                continue
            top = min(b[1] for b in own) - 2 if top is None else top
            bottom = max(b[3] for b in own) + 2 if bottom is None else bottom
            pieces.append((p, x0, top, x1, bottom))
        out.append({"n": n, "pieces": pieces, "text": ""})
    return out


# ------------------------------------------------------------------ ktop: boxes from a page OCR

def ocr_job(pdf, out, layout=True):
    """The PaddleOCR result (layout boxes included) of every page of a PDF, kept in out;
    ocr.py keeps only the markdown, which leaves out what the layout model takes for page
    furniture. layout=False reads each page as one piece of text (no layout model: a
    lone "[2]" is otherwise taken for a picture)."""
    if not os.path.exists(out):
        import tempfile
        import time
        import pymupdf
        import requests
        from pipeline.ocr import ocr
        src, texts = pymupdf.open(pdf), []
        for first in range(0, src.page_count, MAX_PAGES):      # a job of more pages times out
            with tempfile.TemporaryDirectory() as tmp:
                part = os.path.join(tmp, "part.pdf")
                doc = pymupdf.open()
                doc.insert_pdf(src, from_page=first, to_page=min(first + MAX_PAGES, src.page_count) - 1)
                doc.save(part)
                with open(part, "rb") as f:
                    r = requests.post(ocr.JOB, headers=ocr.HEADERS, files={"file": f}, timeout=300,
                                      data={"model": ocr.MODEL, "optionalPayload": json.dumps(
                                          dict(ocr.OPT, useLayoutDetection=layout))})
            jid = r.json()["data"]["jobId"]
            while True:
                d = requests.get(f"{ocr.JOB}/{jid}", headers=ocr.HEADERS, timeout=90).json()["data"]
                if d["state"] == "done":
                    texts.append(requests.get(d["resultUrl"]["jsonUrl"], timeout=120).text.strip())
                    break
                if d["state"] == "failed":
                    sys.exit("OCR 失败:" + str(d.get("errorMsg")))
                time.sleep(3)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        open(out, "w", encoding="utf-8").write("\n".join(texts) + "\n")
    pages = []
    for ln in open(out, encoding="utf-8"):
        if ln.strip():
            pages += json.loads(ln)["result"]["layoutParsingResults"]
    return pages


def page_ocr(pdf):
    """The pages of the ktop file, read once (it has no text layer)."""
    return ocr_job(pdf, PAGE_OCR)


def layout_ktop(doc):
    x0, x1 = SETS["ktop"]["x"]
    marks = []                       # (page, y, kind, value)
    for p, res in enumerate(page_ocr(doc.name)):
        pr = res["prunedResult"]
        k = doc[p].rect.width / pr["width"]
        for b in pr["parsing_res_list"]:
            c = b["block_content"].strip()
            y0 = b["block_bbox"][1] * k
            m = re.match(r"Q(\d{1,2})\.", c)
            if m and b["block_bbox"][0] * k < 100:
                marks.append((p, y0, "q", int(m.group(1))))
            t = re.search(r"\(Total for question\s*=\s*(\d+)\s*marks?\)", c)
            if t:
                marks.append((p, y0, "total", int(t.group(1))))
    marks.sort()
    foot = 748                      # "Edexcel (IAL) Physics A-level   n   PhysicsAndMathsTutor.com"
    out = []
    for k, (p0, y0, kind, n) in enumerate(marks):
        if kind != "q":
            continue
        end = next((m for m in marks[k + 1:] if m[2] == "total"), None)
        if end is None or any(m[2] == "q" for m in marks[k + 1:marks.index(end)]):
            sys.exit(f"ktop 第 {n} 题没有 Total 行")
        pieces = []
        for p in range(p0, end[0] + 1):
            top = y0 - 3 if p == p0 else None
            bottom = end[1] + 16 if p == end[0] else None
            ink = ink_rows(doc[p], x0, x1, 25 if top is None else top, foot if bottom is None else bottom)
            if not ink:
                continue
            pieces.append((p, x0, ink[0] - 3 if top is None else top, x1, ink[1] + 3 if bottom is None else bottom))
        out.append({"n": n, "pieces": pieces, "text": "", "total": end[3]})
    return out


# ------------------------------------------------------------------ kmcq: two columns with a text layer

def layout_kmcq(doc):
    marks, expect, header = [], 1, {}
    for p, page in enumerate(doc):
        header[p] = max([w[3] for w in page.get_text("words") if "PhysicsAndMathsTutor" in w[4] and w[1] < 40]
                        + [20])
        for b in page.get_text("dict")["blocks"]:
            for l in b.get("lines", []):
                t = "".join(s["text"] for s in l["spans"]).strip()
                x, y = l["bbox"][0], l["bbox"][1]
                col = 0 if x < COLS[0][1] else 1
                if abs(x - COLS[col][0] - 6) > 6:
                    continue
                s = SESSION.match(t)
                if s:
                    marks.append((p, col, y, "session", (s.group(1), int(s.group(2)))))
                elif t.startswith("Answers"):
                    marks.append((p, col, y, "key", None))
        for w in page.get_text("words"):
            m = re.fullmatch(r"(\d{1,2})\.", w[4])
            col = 0 if w[0] < COLS[0][1] else 1
            if m and abs(w[0] - COLS[col][0] - 6) <= 6:
                marks.append((p, col, w[1], "q", int(m.group(1))))
    marks.sort(key=lambda m: (m[0], m[1], m[2]))
    qs = []
    for m in marks:                  # keep the numbers in sequence (a "2." inside a sentence is not one)
        if m[3] == "q":
            if m[4] != expect:
                continue
            expect += 1
        qs.append(m)
    key = {}
    for page in doc:
        t = page.get_text()
        if "Answers" in t:
            key.update({int(a): b for a, b in re.findall(r"(\d{1,2})\s*-\s*([A-D])", t.split("Answers", 1)[1])})
    out, session = [], None
    for k, m in enumerate(qs):
        if m[3] == "session":
            session = m[4]
            continue
        if m[3] != "q":
            continue
        nxt = qs[k + 1] if k + 1 < len(qs) else (len(doc) - 1, 1, 842, "end", None)
        spots = [(p, c) for p in range(m[0], nxt[0] + 1) for c in (0, 1)
                 if (p, c) >= (m[0], m[1]) and (p, c) <= (nxt[0], nxt[1])]
        pieces = []
        for p, c in spots:
            x0, x1 = COLS[c]
            top = m[2] - 1 if (p, c) == (m[0], m[1]) else None
            bottom = nxt[2] - 2 if (p, c) == (nxt[0], nxt[1]) else None
            ink = ink_rows(doc[p], x0, x1, header[p] + 2 if top is None else top,
                           doc[p].rect.height - 5 if bottom is None else bottom)
            if not ink:
                continue
            pieces.append((p, x0, ink[0] - 2 if top is None else top, x1,
                           min(ink[1] + 3, bottom if bottom else 10 ** 6)))
        text = "\n".join(doc[p].get_text("text", clip=(x0, y0, x1, y1)).strip() for p, x0, y0, x1, y1 in pieces)
        out.append({"n": m[4], "pieces": pieces, "text": re.sub(r"[ \t]+", " ", text).strip(),
                    "session": session, "answer": key.get(m[4])})
    return out, key


# ------------------------------------------------------------------ extract

def extract(out_json):
    import pymupdf
    os.makedirs(IMG, exist_ok=True)
    data, report = [], []
    for series, spec in SETS.items():
        doc = pymupdf.open(os.path.join(SRC, spec["pdf"]))
        if series == "kpmt":
            qs = layout_kpmt(doc)
        elif series == "ktop":
            qs = layout_ktop(doc)
        else:
            qs, key = layout_kmcq(doc)
            report.append(f"kmcq 答案表 {len(key)} 题")
        nums = [q["n"] for q in qs]
        gaps = sorted(set(range(1, max(nums) + 1)) - set(nums))
        dups = sorted({n for n in nums if nums.count(n) > 1})
        report.append(f"{series}: {len(qs)} 题,Q{min(nums)}–Q{max(nums)};缺号 {gaps or '无'};重复 {dups or '无'}")
        for q in qs:
            qid = f"WPH_{series}_q{q['n']:02d}"
            render(doc, q["pieces"], os.path.join(IMG, qid + ".png"))
            data.append(dict(q, id=qid, series=series, image=f"imgWPH/{qid}.png",
                             pages=sorted({p for p, *_ in q["pieces"]})))
            if not q["pieces"]:
                report.append(f"  {qid}: 没有内容")
    os.makedirs(os.path.dirname(out_json), exist_ok=True)
    json.dump({"questions": data}, open(out_json, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump([{"image": d["image"].split("/")[1]} for d in data],
              open(os.path.join(os.path.dirname(out_json), "ocr_input.json"), "w"))
    print("\n".join(report))
    print(f"{len(data)} 张题图 -> {IMG};-> {out_json}")


# ------------------------------------------------------------------ add

WORDS = re.compile(r"[a-z]{3,}|\d+(?:\.\d+)?")
CROPS_OCR = os.path.join(paths.RAW, "book_ocr", "kinematics", "kpmt_crops.jsonl")
SNIPS_OCR = os.path.join(paths.RAW, "book_ocr", "kinematics", "kpmt_marks.jsonl")
MARKED = os.path.join(paths.RAW, "ocr", "q_WPH_kin_fig_marked.jsonl")
MARK_RX = {"kpmt": re.compile(r"\[\s*(\d{1,2})\s*\]"),            # CIE: [2]
           "ktop": re.compile(r"^\(\s*(\d{1,2})\s*\)$")}            # Edexcel: (2), on its own


def plain(latex):
    """The OCR text without its markup, for question_text and the search index."""
    t = re.sub(r"<img[^>]*>", "", latex or "")
    t = re.sub(r"</?(?:div|table|tr|td|th|tbody|thead)[^>]*>", " ", t)
    t = re.sub(r"\\(?:mathrm|text|mathbf|boldsymbol)\s*\{([^{}]*)\}", r"\1", t)
    t = t.replace("$", "")
    t = re.sub(r"[ \t]+", " ", t)
    return re.sub(r"\n{3,}", "\n\n", t).strip()


def words(t):
    return set(WORDS.findall((t or "").lower()))


def jaccard(a, b):
    a, b = words(a), words(b)
    return len(a & b) / max(1, len(a | b))


# ------------------------------------------------------------------ marks back into the OCR

def blocks(res, skip=("number",)):
    """[(y as a fraction of the page height, text)] of one OCR page, in reading order."""
    pr = res["prunedResult"]
    out = []
    for b in pr["parsing_res_list"]:
        if b["block_label"] in skip:
            continue
        t = re.sub(r"<[^>]+>", " ", b["block_content"]).replace("$", " ").strip()
        out.append((b["block_bbox"][1] / pr["height"], re.sub(r"\s+", " ", t)))
    return out


def _runs(col):
    out, y, n = [], 0, len(col)
    while y < n:
        if col[y]:
            s = y
            while y < n and col[y]:
                y += 1
            out.append((s, y - 1))
        y += 1
    return out


def bracket_boxes(path, xmin=0.55):
    """Boxes (x0, y0, x1, y1, crop px) in the right part of a scanned crop that may hold a
    mark "[n]": a square bracket is a vertical stroke 13-34 px high (150 dpi) with serifs
    at both ends on one side and nothing beside it in the middle. A box is taken from
    either bracket; the OCR of the box decides."""
    import numpy as np
    from PIL import Image
    ink = np.array(Image.open(path).convert("L")) < 150
    H, W = ink.shape
    found = {"[": [], "]": []}
    for x in range(int(W * xmin), W - 6):
        for y0, y1 in _runs(ink[:, x - 1:x + 2].any(axis=1)):
            if not 13 <= y1 - y0 + 1 <= 34:
                continue
            mid = slice(y0 + 4, y1 - 3)

            def full(c):
                return 0 <= c < W and ink[y0:y1 + 1, c].mean() >= 0.8

            def serif(c):
                return 0 <= c < W and ink[y0:y0 + 3, c].any() and ink[y1 - 2:y1 + 1, c].any() \
                    and ink[mid, c].mean() < 0.3

            for kind, side in (("[", 1), ("]", -1)):
                ok = False
                if full(x) and not full(x + side) and serif(x + side):
                    c, k = x, 0
                    while full(c - side) and k < 4:
                        c -= side
                        k += 1
                    ok = c - side < 0 or c - side >= W or ink[mid, c - side].mean() < 0.3
                if not ok and ink[y0:y1 + 1, x].mean() >= 0.8:          # serifs 2 px long
                    a, b = (x + 1, x + 3) if side == 1 else (x - 2, x)
                    ok = a >= 0 and b < W and ink[y0:y0 + 3, a:b].any(axis=0).all() \
                        and ink[y1 - 2:y1 + 1, a:b].any(axis=0).all() and ink[mid, a:b].mean() < 0.2
                if ok:
                    found[kind].append((x, y0, y1))
    boxes = []
    for kind, lst in found.items():
        for x, y0, y1 in lst:
            w = int(1.4 * (y1 - y0)) + 4
            b = (x, y0, x + w, y1) if kind == "[" else (x - w, y0, x + 3, y1)
            j = next((i for i, p in enumerate(boxes) if abs(b[1] - p[1]) <= 6 and b[0] < p[2] and p[0] < b[2]), None)
            if j is None:
                boxes.append(b)
            else:
                p = boxes[j]
                boxes[j] = (min(p[0], b[0]), min(p[1], b[1]), max(p[2], b[2]), max(p[3], b[3]))
    return sorted(boxes, key=lambda b: (b[1], b[0])), H


def marks_step(src, cache_path, out):
    """The OCR drops the right-aligned marks ([2] in kpmt, (2) in ktop) as page furniture,
    and these two files have no text layer to take them from.

    kpmt: the square brackets are found in the crops (bracket_boxes), each box is read on
    its own (one PDF page per box, enlarged three times, without the layout model; read
    as "[2]" it is a mark), and
    the crops are read once more keeping the layout boxes, for the height of each part
    label. ktop: the page OCR (layout_ktop) has the "(2)" blocks and the labels. The marks
    go back into the text (book_questions.restore_marks, anchored on the line before
    them); the cache line keeps marks_y and leaf_y, for the marks of the parts."""
    from PIL import Image
    from pipeline.books.book_questions import restore_marks
    from pipeline.text.split_parts import bare_labels, leaves
    data = json.load(open(src, encoding="utf-8"))["questions"]
    kp = [q for q in data if q["series"] == "kpmt"]
    # kpmt: the crops whole (labels) and the bracket boxes (marks)
    pdf = os.path.join(WORK, "kpmt_crops.pdf")
    if not os.path.exists(CROPS_OCR):
        ims = [Image.open(os.path.join(paths.DATA, q["image"])).convert("RGB") for q in kp]
        ims[0].save(pdf, "PDF", save_all=True, append_images=ims[1:], resolution=200)
    crops = ocr_job(pdf, CROPS_OCR)
    boxes = []
    for q in kp:
        bs, h = bracket_boxes(os.path.join(paths.DATA, q["image"]))
        boxes += [(q["id"], b, h) for b in bs]
    pdf = os.path.join(WORK, "kpmt_marks.pdf")
    if not os.path.exists(SNIPS_OCR):
        pages = []
        for qid, (x0, y0, x1, y1), _ in boxes:
            im = Image.open(os.path.join(IMG, qid + ".png")).convert("L")
            sn = im.crop((x0 - 8, y0 - 8, x1 + 10, y1 + 8))
            sn = sn.resize((sn.width * 3, sn.height * 3))
            page = Image.new("L", (sn.width + 160, sn.height + 120), 255)
            page.paste(sn, (80, 60))
            pages.append(page.convert("RGB"))
        pages[0].save(pdf, "PDF", save_all=True, append_images=pages[1:], resolution=72)
    snips = ocr_job(pdf, SNIPS_OCR, layout=False)
    if len(snips) != len(boxes) or len(crops) != len(kp):
        sys.exit(f"OCR 返回的页数不对(方括号 {len(snips)}/{len(boxes)},题图 {len(crops)}/{len(kp)}),删掉缓存重跑")
    marks_at = {}
    for (qid, b, h), res in zip(boxes, snips):
        t = " ".join(re.sub(r"<[^>]+>|\$", " ", x["block_content"]) for x in res["prunedResult"]["parsing_res_list"])
        m = re.search(r"\[\s*(\d)\s*\]", t.replace("\\left", "").replace("\\right", ""))
        if m:
            got = marks_at.setdefault(qid, [])
            y = b[1] / h
            if not any(abs(y - y2) < 0.004 for y2, _ in got):
                got.append((y, int(m.group(1))))
    per = {}
    for q, res in zip(kp, crops):
        full = [(y, MARK_RX["kpmt"].sub("", t).strip()) for y, t in blocks(res)]
        per[q["id"]] = (sorted(marks_at.get(q["id"], [])), [(y, t) for y, t in full if t and not re.match(r"Q\d+\.?$", t)])
    # ktop: everything from the page OCR, y counted in pages
    pages = page_ocr(os.path.join(SRC, SETS["ktop"]["pdf"]))
    seq = [(p + y, t) for p, res in enumerate(pages) for y, t in blocks(res, skip=("number", "footer"))]
    for q in (q for q in data if q["series"] == "ktop"):
        start = next(y for y, t in seq if re.match(rf"Q{q['n']}\.", t))
        end = next(y for y, t in seq if y > start and "Total for question" in t)
        span = [(y, t) for y, t in seq if start < y < end]
        per[q["id"]] = ([(y, int(MARK_RX["ktop"].match(t).group(1))) for y, t in span if MARK_RX["ktop"].match(t)],
                        [(y, t) for y, t in span if not MARK_RX["ktop"].match(t)])
    cache = ocr_results(cache_path)
    lines, report = dict(cache), []
    for qid, (found, full) in per.items():
        joined, at = "", []
        for y, t in full:
            at.append((len(joined), y))
            joined += bare_labels(t) + "\n\n"
        leaf_y = [(lab, max(y for o, y in at if o <= start)) for lab, start, _ in leaves(joined)]
        d = dict(cache.get(qid) or {"id": qid, "latex": ""})
        text = "\n".join(t for _, t in sorted(full + [(y + 1e-6, f"[{v}]") for y, v in found]))
        latex, misses = restore_marks(text, d["latex"]) if d["latex"] else ("", 0)
        if qid.startswith("WPH_ktop_"):
            total = next(q["total"] for q in data if q["id"] == qid)
            latex = re.sub(r"(?m)^\[(\d{1,2})\]$", r"(\1)", latex) + f"\n\n(Total for question = {total} marks)"
        d.update(latex=latex, marks_y=found, leaf_y=leaf_y)
        lines[qid] = d
        report.append(f"{qid}: 分值 {[v for _, v in found]},小问 {[l for l, _ in leaf_y]}"
                      + (f",{misses} 个没放回" if misses else ""))
    with open(out, "w", encoding="utf-8") as f:
        for d in lines.values():
            f.write(json.dumps(d, ensure_ascii=False) + "\n")
    print("\n".join(report))
    print(f"方括号候选 {len(boxes)} 个，读成分值 {sum(len(v) for v in marks_at.values())} 个;{len(lines)} 题 -> {out}")


def parts_of(o, n, latex):
    """parts (["3(a)(i)"...]) and the marks printed for each: a mark belongs to the last
    part label above it (several parts with one mark: None for all but the last). When
    the labels of the text and of the boxes differ, no parts (the whole question one part)."""
    from pipeline.text.split_parts import bare_labels, leaves
    L = leaves(bare_labels(latex))
    ly = (o or {}).get("leaf_y") or []
    my = (o or {}).get("marks_y") or []
    if not L or [l[0] for l in L] != [l for l, _ in ly]:
        return [], None
    mp = [None] * len(L)
    for y, v in my:
        i = max([j for j, (_, y2) in enumerate(ly) if y2 <= y + 0.002] or [0])
        mp[i] = (mp[i] or 0) + v
    labels = [f"{n}({lab.split('(')[0]})" + (f"({lab.split('(')[1]}" if "(" in lab else "") for lab, _, _ in L]
    return labels, mp


def ocr_results(path):
    got = {}
    if os.path.exists(path):
        for ln in open(path, encoding="utf-8"):
            d = json.loads(ln)
            if d.get("latex"):
                got[d["id"]] = d
    return got


def tidy(latex):
    """The file's own label ("Q9.", "## Q9") off the top, "*(b)" (a quality-of-written-
    communication star) as "(b) *" so the label is found, and the answer lines the OCR
    reads as arrays of dots ("44 mi = 14 units \\cdots \\cdots 72") dropped."""
    t = re.sub(r"^\s*(?:#+\s*)?Q\d+\.?\s*\n+", "", latex or "")
    t = re.sub(r"(?m)^(\s*)\*\s*\(([a-h])\)", r"\1(\2) *", t)
    t = re.sub(r"\n*\s*\$+\s*\\begin\{array\}(?:(?!\\end\{array\}).)*?(?:\\cdots.*?){2,}\\end\{array\}\s*\$+\s*",
               "\n\n", t, flags=re.S)
    t = t.replace("(Total for question = 1 marks)", "(Total for question = 1 mark)")
    t = t.replace("\\textsc{", "\\text{")                 # KaTeX has no \textsc (option letters)
    return re.sub(r"\n{3,}", "\n\n", t).strip()


def rows_for(data, cache):
    from pipeline.ocr.apply_reocr import normalise
    from pipeline.text.audit_text import classify_q
    years = [2000 + q["session"][1] for q in data if q["series"] == "kmcq"]
    tag_mcq = mcq_tag(years)
    rows, notes = [], []
    for q in data:
        s, n = q["series"], q["n"]
        spec = SETS[s]
        o = cache.get(q["id"])
        latex = tidy(normalise(o["latex"])) if o else None
        grade = classify_q(latex) if latex else "missing"
        if not o:
            notes.append(f"{q['id']}: 没有 OCR 结果")
        elif grade != "ok":
            notes.append(f"{q['id']}: OCR 评为 {grade}")
        r = {"id": q["id"], "syllabus": "WPH", "component": s, "component_name": spec["name"],
             "paper": f"WPH/{s}", "variant": "", "year": SUPPLIED, "month": 0, "series": s, "q": n,
             "topic": None, "topic_name": None, "question_latex": latex,
             "q_quality": "ok" if grade == "ok" else ("partial" if latex else "missing"),
             "image": q["image"], "qp_pdf": spec["pdf"], "qp_pages": json.dumps(q["pages"]),
             "has_diagram": int(bool(o and o.get("figures"))),
             "ms_text": None, "ms_latex": None, "ms_quality": "missing", "mark_codes": None,
             "ms_total": None, "totals_agree": None, "ms_pdf": None,
             "qtype": None, "options": None, "option_texts": None, "answer": None}
        if s == "kmcq":
            mon, yy = q["session"]
            r.update(year=2000 + yy, month=MONTHS[mon.lower()], session=f"Kinematics 选择题 · {mon} {2000 + yy}",
                     question_text=q["text"], marks=1, parts="[]", marks_parts="[1]", qtype="mcq",
                     options=json.dumps(list("ABCD")), answer=q["answer"],
                     ms_text=f"{n}  {q['answer']}  |  1" if q["answer"] else None,
                     mark_codes="[]" if q["answer"] else None, ms_total=1 if q["answer"] else None,
                     totals_agree=1 if q["answer"] else None, ms_quality="ok" if q["answer"] else "missing",
                     ms_pdf=spec["pdf"] if q["answer"] else None,
                     topic_note=f"出处:kinematics_mcq.pdf 第 {n} 题,考季 {mon} {yy:02d};答案取文末答案表",
                     tags=json.dumps(COMMON_TAGS + [tag_mcq], ensure_ascii=False))
            if not q["answer"]:
                notes.append(f"{q['id']}: 答案表里没有")
        else:
            text = plain(latex)
            parts, mp = parts_of(o, n, latex or "")
            printed = sum(v for _, v in (o or {}).get("marks_y") or [])
            marks = q["total"] if s == "ktop" else (printed or None)
            if s == "ktop" and printed != marks and not (marks == 1 and not printed):
                notes.append(f"{q['id']}: 读出的分值之和 {printed} ≠ Total {marks}")
            if parts and sum(x or 0 for x in mp) != (marks or 0):
                notes.append(f"{q['id']}: 小问分值之和 {sum(x or 0 for x in mp)} ≠ 总分 {marks}")
            elif not parts and re.search(r"\(a\)", latex or ""):
                notes.append(f"{q['id']}: 小问标号与版面对不上，不拆小问")
            mcq = s == "ktop" and marks == 1 and not parts
            r.update(session=spec["name"], question_text=text, marks=marks,
                     parts=json.dumps(parts), marks_parts=json.dumps(mp if parts else ([marks] if marks else [])),
                     qtype="mcq" if mcq else None, options=json.dumps(list("ABCD")) if mcq else None,
                     topic_note=f"出处:{spec['pdf']} Q{n}(PMT 汇编,未附评分细则)" + (
                         ";题面是 CIE 9702 卷 2 式结构题(题前印原卷题号),原卷未认出" if s == "kpmt" else
                         ";Edexcel IAL 题，原卷未认出") + f";year 取提供年份 {SUPPLIED}",
                     tags=json.dumps(COMMON_TAGS + [spec["tag"]], ensure_ascii=False))
        rows.append(r)
    return rows, notes


def dedupe(rows):
    """ktop questions that are also in kpmt: kept once (the kpmt row), with both tags."""
    kp = [r for r in rows if r["series"] == "kpmt"]
    drop, report = set(), []
    for r in rows:
        if r["series"] != "ktop":
            continue
        best = max(kp, key=lambda x: jaccard(r["question_text"], x["question_text"]))
        sim = jaccard(r["question_text"], best["question_text"])
        report.append(f"{r['id']} 最像 {best['id']}:{sim:.2f}")
        if sim >= DUP:
            drop.add(r["id"])
            tags = json.loads(best["tags"])
            tags.append(SETS["ktop"]["tag"])
            best["tags"] = json.dumps(tags, ensure_ascii=False)
            best["topic_note"] += f";又见 kinematics_pmt_qp.pdf Q{r['q']}"
    return [r for r in rows if r["id"] not in drop], report


def add(src, cache_path, write):
    data = json.load(open(src, encoding="utf-8"))["questions"]
    rows, notes = rows_for(data, ocr_results(cache_path))
    rows, dup = dedupe(rows)
    for x in dup + notes:
        print("  " + x)
    by = {}
    for r in rows:
        by[r["series"]] = by.get(r["series"], 0) + 1
    print(f"{len(rows)} 题 {by};带插图 {sum(r['has_diagram'] for r in rows)};"
          f"q_quality ok {sum(r['q_quality'] == 'ok' for r in rows)}")
    if not write:
        print("未写入;加 --write 写入")
        return
    con = db.connect()
    db.ensure_tags(con)
    for s in SETS:
        con.execute("DELETE FROM questions WHERE id LIKE ? ESCAPE '\\'", (f"WPH\\_{s}\\_%",))
        con.execute("DELETE FROM q_fts WHERE id LIKE ?", (f"WPH_{s}_%",))
    cols = list(rows[0])
    con.executemany(f"INSERT INTO questions ({','.join(cols)}) VALUES ({','.join('?' * len(cols))})",
                    [[r[c] for c in cols] for r in rows])
    con.executemany("INSERT INTO q_fts (id, question_text, ms_text, topic_name) VALUES (?, ?, ?, ?)",
                    [(r["id"], r["question_latex"] or r["question_text"], r["ms_text"], None) for r in rows])
    con.commit()
    print(f"写入 {len(rows)} 题")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("extract")
    e.add_argument("--out", default=os.path.join(WORK, "questions.json"))
    m = sub.add_parser("marks", help="把 OCR 丢掉的分值放回(kpmt、ktop)")
    m.add_argument("--src", default=os.path.join(WORK, "questions.json"))
    m.add_argument("--ocr", default=OCR_CACHE)
    m.add_argument("--out", default=MARKED)
    a = sub.add_parser("add")
    a.add_argument("--src", default=os.path.join(WORK, "questions.json"))
    a.add_argument("--ocr", default=MARKED)
    a.add_argument("--write", action="store_true")
    args = ap.parse_args()
    if args.cmd == "extract":
        extract(args.out)
    elif args.cmd == "marks":
        marks_step(args.src, args.ocr, args.out)
    else:
        add(args.src, args.ocr, args.write)


if __name__ == "__main__":
    main()
