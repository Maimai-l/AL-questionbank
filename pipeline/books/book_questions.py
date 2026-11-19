#!/usr/bin/env python3
"""Practice questions printed in a textbook, as question rows with crops ("精选题").

    python3 -I pipeline/books/book_questions.py extract raw/textbooks/hodder_edx_al1.pdf --book hodder_edx_al1
    python3 pipeline/books/book_questions.py add [--write]

`extract` reads the PDF's text layer (the book has one; it is an e-book laid out on
US Letter pages) and finds, in every chapter of the bookmarks, the end-of-chapter
"Exam practice questions" and "Stretch and challenge" sections. A question starts at
a bold number at the left margin (1, 2, 3 ... in order; the Stretch and challenge
questions carry on the chapter's numbering) and ends at its last "[Total n Marks]".
What lies between that line and the next question is shared material: "Use Figure
9.16 to answer Questions 1, 2 and 3", the figure itself, "This information is for
use in Questions 1 and 5". Each such block goes with the questions its sentence
names (SHARED overrides where it names none), in page order, on the crop and in
the text. Each question is rendered from the page at the 9702 crops' resolution
(150 dpi, 16-level grey, lib/png16.py), the pieces of a question that runs over
pages stacked, to data/imgWPH/<id>.png. Writes raw/book_questions/<book>/questions.json.

`add` puts them in the questions table (and the full-text index), replacing the
rows of the same book: syllabus WPH, component = chapter number, tags = the book's
TAGS. Without --write it only reports.

Fields that describe a CAIE sitting are filled so that the code reading them keeps
working: paper "WPH/<chapter>" (syllabus/component plus an empty variant, as
9702/12 is component 1 variant 2), variant "", series "hb1", session the book's
title, year its publication year, month 0, q the number printed in the book.
"""
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))
from lib import db, paths, png16  # noqa: E402

DPI = 150                       # pipeline/split/crop.py
ZOOM = DPI / 72.0
X0, X1 = 66, 546                # the text column is 72-540 on every page
PAD = 4                         # pt above the first line and below the last
GAP = 12                        # pt of white between pieces from different places

BOOKS = {
    "hodder_edx_al1": {
        "syllabus": "WPH", "series": "hb1", "year": 2015,
        "title": "Hodder Edexcel A Level Physics 1",
        "tags": ["精选", "Hodder Edexcel A Level Physics 1"],
        "topic_note": "按教材章节分组;WPH 考纲加入后再定主题",
        # A figure or table after a question's last [Total] goes with that question,
        # unless named here: (chapter, the question it follows) -> the questions it
        # is for (the figure that "Use Figure 9.16 to answer Questions 1, 2 and 3"
        # points to comes after question 3)
        "shared": {(9, 3): [1, 2, 3],      # Figure 9.16
                   (9, 5): [4, 5],         # Figure 9.17
                   (10, 4): [1, 2, 3]},    # Figure 10.17
        # figures in the chapter's text that a question uses: (chapter, question) ->
        # [(page, y0, y1)], added below the question
        "extra": {(10, 4): [(332, 410, 541)],    # Figure 10.6
                  (10, 5): [(320, 395, 722)],    # Figure 10.1b
                  (11, 9): [(375, 70, 350)],     # Figure 11.10
                  (11, 16): [(418, 70, 400)]},   # Figure 11.43
        # one-mark questions whose options A-D are drawn in the figure, not printed
        "mcq_in_figure": {(9, 1), (9, 2), (9, 3), (9, 4), (9, 5), (10, 1), (10, 2), (10, 3)},
    },
}

HEAD_EP = "Exam practice questions"
HEAD_SC = "Stretch and challenge"
TOTAL = re.compile(r"\[\s*Total\s*:?\s*(\d+)\s*Marks?\s*\]", re.I)
MARK = re.compile(r"\[\s*(\d+)\s*\]")
NUM = re.compile(r"^(\d{1,2})(?=\s|[a-z]\)|$)")
LETTER = re.compile(r"^\(?([a-i])\)")
ROMAN = re.compile(r"^\(?(i{1,3}|iv|v|vi{1,3}|ix|x)\)")
OPTION = re.compile(r"^([A-D])$")
NAMES = re.compile(r"Questions?\s+((?:\d+\s*(?:,\s*and|,|and|&|–|-|to)?\s*)+)")


def img_dir(syllabus):
    return os.path.join(paths.DATA, "img" + syllabus)


# ------------------------------------------------------------------ the page

def is_bold(span):
    return bool(span["flags"] & 16) or "Bold" in span["font"]


def page_items(page):
    """Lines (with spans) and graphics on one page, top to bottom."""
    lines, graphics = [], []
    for b in page.get_text("dict")["blocks"]:
        if b["type"] == 1:
            graphics.append({"kind": "image", "bbox": tuple(b["bbox"])})
            continue
        for l in b.get("lines", []):
            spans = [s for s in l["spans"] if s["text"].strip()]
            if spans:
                lines.append({"bbox": tuple(l["bbox"]), "spans": spans,
                              "text": "".join(s["text"] for s in l["spans"]).strip()})
    H = page.rect.height
    for d in page.get_drawings():
        r = d["rect"]
        if r.y1 < 0 or r.y0 > H or r.x1 < 0 or r.x0 > page.rect.width:
            continue                         # the e-book's off-page rules
        rule = r.height < 3 and r.width > 400
        graphics.append({"kind": "rule" if rule else "drawing", "bbox": tuple(r)})
    lines.sort(key=lambda l: (round(l["bbox"][1]), l["bbox"][0]))
    return lines, graphics


def line_number(line):
    """The question number a line starts with (bold, at the left margin), or None."""
    spans = line["spans"]
    s = spans[0]
    t = s["text"].strip()
    if t == "•" and len(spans) > 1:
        s, t = spans[1], spans[1]["text"].strip()
    t = t.lstrip("•").strip()
    if not is_bold(s) or line["bbox"][0] > 90:
        return None
    m = NUM.match(t)
    return int(m.group(1)) if m else None


def span_text(spans):
    """A line's text; superscripts as ^, so 10^7 and m s^−1 stay readable, and a
    space after a bold label or option letter set tight against its text (An → A n)."""
    out, prev = "", None
    for s in spans:
        t = s["text"]
        if prev is not None and is_bold(prev) and not is_bold(s) and t[:1].strip() \
                and re.fullmatch(r"\s*(?:[A-D]|[a-h]\)|[ivx]+\)|\d{1,2})", prev["text"]):
            out += " "
        if s["flags"] & 1 and t.strip() and out and not out.endswith(" "):
            out += "^" + t.strip()
        else:
            out += t
        prev = s
    return re.sub(r"\s+", " ", out).strip().lstrip("•").strip()


# ------------------------------------------------------------------ sections

def chapters(doc):
    toc = [(t[1], t[2]) for t in doc.get_toc() if t[0] == 2]
    out = []
    for i, (title, start) in enumerate(toc):
        m = re.match(r"(\d+)\s+(.*)", title)
        end = toc[i + 1][1] - 1 if i + 1 < len(toc) else None
        out.append({"no": int(m.group(1)), "title": m.group(2).strip(), "from": start, "to": end})
    # the last chapter runs to the next level-1 entry (the index)
    last = [t[2] for t in doc.get_toc() if t[0] == 1 and t[2] > out[-1]["from"]]
    out[-1]["to"] = (last[0] - 1) if last else doc.page_count
    return out


def section_stream(doc, ch):
    """Everything after the chapter's "Exam practice questions" heading, in reading
    order: [(page, kind, item, section)] with section "ep" or "sc"."""
    stream, section = [], None
    for pno in range(ch["from"], ch["to"] + 1):
        lines, graphics = page_items(doc[pno - 1])
        items = [(l["bbox"][1], "line", l) for l in lines] + [(g["bbox"][1], g["kind"], g) for g in graphics]
        items.sort(key=lambda x: (round(x[0]), x[1] != "line"))
        for _, kind, it in items:
            if kind == "line" and it["text"].startswith(HEAD_EP) and max(s["size"] for s in it["spans"]) > 16:
                section = "ep"
                stream = []                  # a mention earlier in the chapter is not the section
                continue
            if kind == "line" and it["text"].startswith(HEAD_SC) and max(s["size"] for s in it["spans"]) > 16:
                section = "sc"
                stream.append((pno, "head", it, section))
                continue
            if section:
                stream.append((pno, kind, it, section))
    return stream


def segment(doc, ch, book):
    """Questions of one chapter: own items, shared blocks and anomalies."""
    stream = section_stream(doc, ch)
    if not stream:
        return [], [], []
    starts, expect, problems = [], 1, []
    for i, (pno, kind, it, sec) in enumerate(stream):
        if kind != "line":
            continue
        n = line_number(it)
        if n is None:
            continue
        if n == expect:
            starts.append(i)
            expect += 1
        elif it["bbox"][0] < 90 and not MARK.fullmatch(it["text"]):
            problems.append(f"p{pno}: 题号 {n} 不在顺序上(应为 {expect}):{it['text'][:50]}")
    qs = []
    blocks = [(0, stream[:starts[0]] if starts else stream)]     # (the question before it, items)
    for k, si in enumerate(starts):
        ei = starts[k + 1] if k + 1 < len(starts) else len(stream)
        body = stream[si:ei]
        # the question ends at its last [Total ...]; what follows, up to the next
        # question, is a figure or table the e-book placed after it, or material
        # for the questions a sentence names
        last_total = max((j for j, (_, kind, it, _) in enumerate(body)
                          if kind == "line" and TOTAL.search(it["text"])), default=None)
        own = body if last_total is None else body[:last_total + 1]
        rest = [] if last_total is None else body[last_total + 1:]
        qs.append({"n": k + 1, "section": body[0][3], "own": own})
        if rest:
            blocks.append((k + 1, rest))
    shared = []
    for after, b in blocks:
        for sub, named, past_head in split_block(b):
            text = " ".join(x[2]["text"] for x in sub if x[1] == "line")
            if not text and not any(x[1] in ("image", "drawing") for x in sub):
                continue
            whom = set(named)
            override = book["shared"].get((ch["no"], after))
            if not whom:
                whom = set(override) if override and not past_head else \
                    {after + 1} if past_head or after == 0 else {after}
            shared.append({"items": sub, "text": text, "for": sorted(whom), "after": after,
                           "pos": (sub[0][0], sub[0][2]["bbox"][1])})
            if not named and after == 0 and not override:
                problems.append(f"p{sub[0][0]}: 第 1 题之前的材料没有写明题号,归给第 1 题:{text[:60]!r}")
    return qs, shared, problems


def named_questions(text):
    """The question numbers a sentence names: "Questions 1, 2 and 3", "Questions 1–3"."""
    whom = set()
    for m in NAMES.finditer(text):
        nums = [int(x) for x in re.findall(r"\d+", m.group(1))]
        if re.search(r"\d\s*(–|-|to)\s*\d", m.group(1)) and len(nums) == 2:
            nums = list(range(nums[0], nums[1] + 1))
        whom |= set(nums)
    return whom


def split_block(items):
    """A block between two questions, cut before every sentence that names questions
    and at the Stretch and challenge heading: [(items, named numbers, after heading)]."""
    out, cur, named, past = [], [], set(), False
    for x in items:
        if x[1] == "head":
            if cur:
                out.append((cur, named, past))
            cur, named, past = [], set(), True
            continue
        if x[1] == "rule":
            continue
        n = named_questions(x[2]["text"]) if x[1] == "line" else set()
        if n:
            # the sentence may start on the lines above
            head = []
            while cur and cur[-1][1] == "line" and not re.search(r"[.?!:\]]$", cur[-1][2]["text"]):
                head.insert(0, cur.pop())
            if cur:
                out.append((cur, named, past))
            cur, named = head, n
        cur.append(x)
    if cur:
        out.append((cur, named, past))
    return out


# ------------------------------------------------------------------ one question

def pieces(items):
    """Per page, the vertical extent of the items: [(page, y0, y1)]."""
    by = {}
    for pno, kind, it, _ in items:
        if kind in ("rule", "head"):
            continue
        y0, y1 = it["bbox"][1], it["bbox"][3]
        a = by.setdefault(pno, [y0, y1])
        a[0], a[1] = min(a[0], y0), max(a[1], y1)
    return [(p, a[0], a[1]) for p, a in sorted(by.items())]


def render(doc, groups, path):
    """Stack the pieces of every group (own items, shared blocks) into one PNG."""
    import pymupdf as fitz
    tiles = []
    for gi, items in enumerate(groups):
        for pno, y0, y1 in pieces(items):
            clip = fitz.Rect(X0, max(0, y0 - PAD), X1, min(doc[pno - 1].rect.height, y1 + PAD))
            pix = doc[pno - 1].get_pixmap(matrix=fitz.Matrix(ZOOM, ZOOM), clip=clip, alpha=False,
                                         colorspace=fitz.csGRAY)
            tiles.append((gi, pix))
    w = max(t.width for _, t in tiles)
    gap = int(GAP * ZOOM)
    h = sum(t.height for _, t in tiles) + gap * (len({g for g, _ in tiles}) - 1)
    out = fitz.Pixmap(fitz.csGRAY, fitz.IRect(0, 0, w, h), False)
    out.clear_with(255)
    y, last = 0, None
    for gi, t in tiles:
        if last is not None and gi != last:
            y += gap
        t.set_origin(0, y)
        out.copy(t, t.irect)
        y += t.height
        last = gi
    png16.save_pixmap(out, path)
    return out.width, out.height


def read_text(items):
    """Lines as text, a line per line; part labels and options kept."""
    out = []
    for _, kind, it, _ in items:
        if kind == "line":
            out.append(span_text(it["spans"]))
    return out


def structure(qno, lines):
    """marks, parts (["3(a)(i)", ...]) and marks_parts, and the options, from the lines.

    The parts are the lowest-level labels, as split_parts.py finds them: a), b), and
    i), ii) under a letter. A part's mark is the [n] printed after it, or the
    [Total n Marks] that closes it when it has no [n] of its own (less what the
    parts before it since the last Total got); None when the book prints one mark
    for several parts (after the last of them)."""
    order, marks_by = [], {}
    letter = roman = None
    leaf = str(qno)
    totals, options, cur_opt, since = [], {}, None, 0
    for raw in lines:
        t = raw.strip()
        m = NUM.match(t)
        if m and int(m.group(1)) == qno and not order and not totals:
            t = t[m.end():].strip()
        for _ in range(2):           # "1 a) i) ..." on one line
            lm, rm = LETTER.match(t), ROMAN.match(t)
            if rm and letter and not (rm.group(1) == "i" and letter == "h" and roman is None):
                roman = rm.group(1)
                t = t[rm.end():].strip()
            elif lm:
                letter, roman = lm.group(1), None
                t = t[lm.end():].strip()
            else:
                break
            leaf = f"{qno}({letter})" + (f"({roman})" if roman else "")
            if leaf not in order:
                order.append(leaf)
        om = re.match(r"^([A-D])(?:\s+(.*)|$)", t)
        if om and len(raw) < 120 and not re.match(r"^[A-D]\s+(is|was|and|or)\b", t):
            cur_opt = om.group(1)
            if cur_opt in options:           # a letter printed twice (A B C C): the missing one
                gone = [x for x in "ABCD" if x not in options]
                cur_opt = gone[0] if len(gone) == 1 else cur_opt
            options[cur_opt] = (om.group(2) or "").strip()
        elif cur_opt and not MARK.search(t) and not TOTAL.search(t) and options.get(cur_opt) == "":
            options[cur_opt] = t
        tm = TOTAL.search(t)
        for mm in MARK.finditer(TOTAL.sub("", t)):
            marks_by[leaf] = marks_by.get(leaf, 0) + int(mm.group(1))
            since += int(mm.group(1))
        if not tm and re.fullmatch(r"\d{1,2}\]", t):      # "[" left on the line above
            marks_by[leaf] = marks_by.get(leaf, 0) + int(t[:-1])
            since += int(t[:-1])
        if tm:
            n = int(tm.group(1))
            totals.append(n)
            if leaf not in marks_by and n > since:
                marks_by[leaf] = n - since
            since = 0
    parts = [l for l in order if not any(o.startswith(l + "(") for o in order)]
    total = sum(totals) if totals else sum(marks_by.values()) or None
    if parts:
        mp = [marks_by.get(p) for p in parts]
        stray = sum(v for k, v in marks_by.items() if k not in parts)
        ok = stray == 0 and sum(x or 0 for x in mp) == (total or 0)
    else:
        mp, ok = ([total] if total else []), True
    if len(options) < 3 or set(options) - set("ABCD"):
        options = {}
    return {"marks": total, "parts": parts, "marks_parts": mp, "options": options, "parts_sum_ok": ok}


# ------------------------------------------------------------------ extract

def extract(pdf, book_id, out_json):
    import pymupdf as fitz
    book = BOOKS[book_id]
    doc = fitz.open(pdf)
    outdir = img_dir(book["syllabus"])
    os.makedirs(outdir, exist_ok=True)
    records, report = [], []
    for ch in chapters(doc):
        qs, shared, problems = segment(doc, ch, book)
        if not qs:
            continue
        n_ep = sum(q["section"] == "ep" for q in qs)
        n_sc = len(qs) - n_ep
        report.append((ch, n_ep, n_sc, problems))
        body = range(ch["from"], qs[0]["own"][0][0] + 1)     # the chapter before its questions
        for q in qs:
            qid = f"{book['syllabus']}_{book['series']}_ch{ch['no']:02d}_q{q['n']:02d}"
            mine = [s for s in shared if q["n"] in s["for"]]
            first = (q["own"][0][0], q["own"][0][2]["bbox"][1])
            before = [s["items"] for s in mine if s["pos"] < first]
            after = [s["items"] for s in mine if s["pos"] > first]
            extra = [[(p, "image", {"bbox": (X0, y0, X1, y1)}, "extra")]
                     for p, y0, y1 in book.get("extra", {}).get((ch["no"], q["n"]), [])]
            groups = before + [q["own"]] + after + extra
            name = qid + ".png"
            render(doc, groups, os.path.join(outdir, name))
            own_lines = read_text(q["own"])
            text = "\n\n".join("\n".join(read_text(g)) for g in groups)
            st = structure(q["n"], own_lines)
            all_items = [x for g in groups for x in g]
            pages = sorted({p for p, *_ in all_items})
            # what the question points to that its crop does not hold: a figure in the
            # chapter's text, another question
            own_text = " ".join(own_lines)
            refs = [] if extra else [f"Figure {f}" for f in sorted(set(re.findall(r"Figures? (\d+\.\d+[a-z]?)", own_text)))
                    if any(doc[p - 1].search_for(f"Figure {f}") for p in body
                           if p < q["own"][0][0] or f"Figure {f}" not in " ".join(read_text(q["own"])))]
            refs += [f"Question {n}" for n in re.findall(r"(?:[Ii]n|from|of|to) Question (\d+)", own_text)
                     if int(n) != q["n"]]
            records.append({
                "id": qid, "chapter": ch["no"], "chapter_title": ch["title"], "q": q["n"],
                "section": q["section"], "image": f"img{book['syllabus']}/{name}",
                "pages": pages, "text": text, **st,
                # formulas are small pictures too: a figure is at least 50 pt high and 120 pt wide
                "has_diagram": any(k == "image" and it["bbox"][3] - it["bbox"][1] >= 50
                                   and it["bbox"][2] - it["bbox"][0] >= 120 for _, k, it, _ in all_items),
                "has_drawing": any(k == "drawing" for _, k, *_ in all_items),
                "shared": [s["text"][:80] for s in mine], "refs": refs,
                "extra": book.get("extra", {}).get((ch["no"], q["n"]), []),
            })
    os.makedirs(os.path.dirname(out_json), exist_ok=True)
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump({"book": book_id, "pdf": os.path.basename(pdf), "questions": records}, f,
                  ensure_ascii=False, indent=1)
    tot = 0
    for ch, ep, sc, problems in report:
        tot += ep + sc
        print(f"第 {ch['no']:>2} 章 {ch['title'][:44]:<44} Exam practice {ep:>2}  Stretch {sc}")
        for p in problems:
            print("    " + p)
    for r in records:
        if r["refs"]:
            print(f"    {r['id']} 引用了题图以外的内容:{', '.join(r['refs'])}")
    bad = [r["id"] for r in records if not r["parts_sum_ok"]]
    print(f"共 {tot} 题,题图 -> {outdir};小问分值之和与总分不符:{bad or '无'}")
    print(f"-> {out_json}")


# ------------------------------------------------------------------ add

def rows_for(data):
    book = BOOKS[data["book"]]
    out = []
    for r in data["questions"]:
        single = r["marks"] == 1 and not r["parts"]
        drawn = (r["chapter"], r["q"]) in book.get("mcq_in_figure", ())
        mcq = single and (bool(r["options"]) or drawn)
        out.append({
            "id": r["id"], "syllabus": book["syllabus"], "component": str(r["chapter"]),
            "component_name": r["chapter_title"], "paper": f"{book['syllabus']}/{r['chapter']}",
            "variant": "", "year": book["year"], "month": 0, "session": book["title"],
            "series": book["series"], "q": r["q"], "parts": json.dumps(r["parts"]),
            "marks": r["marks"], "marks_parts": json.dumps(r["marks_parts"]),
            "topic": None, "topic_name": None, "topic_note": book["topic_note"],
            "question_text": r["text"], "ms_text": None, "ms_latex": None, "ms_quality": "missing",
            "q_quality": "partial", "image": r["image"], "qp_pdf": data["pdf"],
            "qp_pages": json.dumps([p - 1 for p in r["pages"]]),
            "has_diagram": int(r["has_diagram"]), "qtype": "mcq" if mcq else None,
            "options": json.dumps(sorted(r["options"]) if r["options"] else list("ABCD")) if mcq else None,
            "option_texts": json.dumps(r["options"], ensure_ascii=False) if mcq and r["options"] else None,
            "answer": None, "tags": json.dumps(book["tags"], ensure_ascii=False),
        })
    return out


def add(src, write):
    data = json.load(open(src, encoding="utf-8"))
    book = BOOKS[data["book"]]
    rows = rows_for(data)
    con = db.connect()
    if write:
        db.ensure_tags(con)
    pattern = f"{book['syllabus']}\\_{book['series']}\\_%"
    old = con.execute("SELECT COUNT(*) FROM questions WHERE id LIKE ? ESCAPE '\\'", (pattern,)).fetchone()[0]
    print(f"{len(rows)} 题(库里已有本书 {old} 题,将替换)")
    if not write:
        print("未写入;加 --write 写入")
        return
    ids = [r["id"] for r in rows]
    con.execute("DELETE FROM questions WHERE id LIKE ? ESCAPE '\\'", (pattern,))
    con.execute("DELETE FROM q_fts WHERE id LIKE ?", (f"{book['syllabus']}_{book['series']}_%",))
    cols = list(rows[0])
    con.executemany(f"INSERT INTO questions ({','.join(cols)}) VALUES ({','.join('?' * len(cols))})",
                    [[r[c] for c in cols] for r in rows])
    con.executemany("INSERT INTO q_fts (id, question_text, ms_text, topic_name) VALUES (?, ?, ?, ?)",
                    [(r["id"], r["question_text"], None, None) for r in rows])
    con.commit()
    print(f"写入 {len(ids)} 题")


# ------------------------------------------------------------------ marks back into the OCR

MARK_LINE = re.compile(r"^(?:\[\s*Total\s*:?\s*\d+\s*Marks?\s*\]|\[?\s*\d{1,2}\s*\])$", re.I)


def _norm(t, keep_map=False):
    """Letters and digits only, lower case, LaTeX commands dropped (\\mathbf{D}7.2\\times10^{23}
    and "D 7.2 × 10^23" both give d721023); with keep_map, each kept character's position."""
    out, pos = [], []
    for m in re.finditer(r"\\(sin|cos|tan|log|ln|exp)\b|\\[A-Za-z]+|([A-Za-z0-9])", t):
        if m.group(1):                   # \cos is "cos" in the text layer
            out += list(m.group(1))
            pos += [m.start()] * len(m.group(1))
        elif m.group(2):
            out.append(m.group(2).lower())
            pos.append(m.start())
    return ("".join(out), pos) if keep_map else "".join(out)


def restore_marks(text, latex):
    """The OCR leaves out the right-aligned [n] and [Total n Marks] lines (it takes them
    for page furniture). Put each back where the text layer has it: after the paragraph
    of the OCR text that holds the end of the line before it. Returns (latex, misses)."""
    latex = re.sub(r"(?m)^(\s*)•\s*", r"\1", latex)      # the coloured bullet before a number
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    plan, anchor = [], ""
    for l in lines:
        if MARK_LINE.match(l):
            tok = l if l.startswith("[") else "[" + l
            if plan and plan[-1][0] == anchor:
                plan[-1][1].append(tok)
            else:
                plan.append((anchor, [tok]))
            continue
        inline = MARK.search(TOTAL.sub("", l)) or TOTAL.search(l)
        body = l[:inline.start()].strip() if inline and l.rstrip().endswith("]") else l
        anchor = (anchor + " " + body)[-200:] if len(_norm(body)) < 12 else body
        if body != l:
            plan.append((anchor, [l[inline.start():].strip()]))
    # as many of each token as the text layer has, less what the OCR kept
    from collections import Counter
    need = Counter(t for _, toks in plan for t in toks)
    need.subtract(Counter(re.findall(r"\[\s*(?:Total\s*:?\s*)?\d+\s*(?:Marks?\s*)?\]", latex)))
    norm, pos = _norm(latex, keep_map=True)
    out, at, cut, misses = latex, 0, [], 0
    for anchor, toks in plan:
        key = _norm(anchor)
        hit = -1
        # the end of the line before; failing that, its start (the OCR may have
        # dropped an exponent near the end): the mark goes after that paragraph
        for k in (key[-30:], key[-18:], key[-10:], key[-60:][:15]):
            if len(k) >= 6:
                hit = norm.find(k, at)
                if hit >= 0:
                    hit += len(k) - 1
                    break
        if hit < 0:
            if anchor is plan[-1][0] or all(TOTAL.search(t) for t in toks):
                cut.append((len(latex), toks))          # the closing Total: at the end
            else:
                misses += 1
            continue
        at = hit + 1
        end = latex.find("\n", pos[hit])
        cut.append((len(latex) if end < 0 else end, toks))
    for p, toks in sorted(cut, key=lambda x: -x[0]):
        line = out[out.rfind("\n", 0, p) + 1:p].rstrip()
        for t in toks:
            if line.endswith(t):                         # the OCR kept it, on the line
                continue
            rest = out[p:]
            if rest.lstrip().startswith(t):              # or as the next paragraph
                p += len(rest) - len(rest.lstrip()) + len(t)
                continue
            if need[t] <= 0:
                continue
            need[t] -= 1
            out = out[:p] + "\n\n" + t + out[p:]
            p += 2 + len(t)
    return out, misses


def marks_cache(src_json, caches, out):
    """OCR caches (later ones win) with the marks put back, as one cache for apply_reocr.py."""
    text = {r["id"]: r["text"] for r in json.load(open(src_json, encoding="utf-8"))["questions"]}
    got = {}
    for c in caches:
        for ln in open(c, encoding="utf-8"):
            d = json.loads(ln)
            if d.get("latex") and d["id"] in text:
                got[d["id"]] = d
    missed = {}
    with open(out, "w", encoding="utf-8") as f:
        for qid, d in sorted(got.items()):
            latex, misses = restore_marks(text[qid], d["latex"])
            if misses:
                missed[qid] = misses
            f.write(json.dumps(dict(d, latex=latex), ensure_ascii=False) + "\n")
    print(f"{len(got)} 题 -> {out};分值没放回的:{missed or '无'}")


def fixes_cache(cache, fixes, out):
    """The questions of a fixes file (one line each: {"id", "why"} and, for a correction,
    "find" and "replace", checked against the crop) from the OCR cache, corrected, as a
    cache for apply_reocr.py without --check-text: the readings that check refused
    and a person accepted."""
    got = {}
    for ln in open(cache, encoding="utf-8"):
        d = json.loads(ln)
        if d.get("latex"):
            got[d["id"]] = d
    done, bad = {}, []
    for ln in open(fixes, encoding="utf-8"):
        if not ln.strip():
            continue
        f = json.loads(ln)
        d = done.get(f["id"]) or (dict(got[f["id"]]) if f["id"] in got else None)
        if d is None:
            bad.append(f"{f['id']}: 缓存里没有")
            continue
        if "find" in f:
            if f["find"] not in d["latex"]:
                bad.append(f"{f['id']}: 找不到 {f['find']!r}")
                continue
            d["latex"] = d["latex"].replace(f["find"], f["replace"])
        done[f["id"]] = d
    with open(out, "w", encoding="utf-8") as fh:
        for d in done.values():
            fh.write(json.dumps(d, ensure_ascii=False) + "\n")
    print(f"{len(done)} 题 -> {out}" + ("".join("\n  " + b for b in bad) if bad else ""))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("extract")
    e.add_argument("pdf")
    e.add_argument("--book", required=True, choices=list(BOOKS))
    e.add_argument("--out", help="questions.json(默认 raw/book_questions/<book>/questions.json)")
    a = sub.add_parser("add")
    a.add_argument("--book", default="hodder_edx_al1", choices=list(BOOKS))
    a.add_argument("--src")
    a.add_argument("--write", action="store_true")
    m = sub.add_parser("marks", help="把 [n] 与 [Total n Marks] 放回 OCR 结果(OCR 把右对齐的分值当页眉页脚丢掉)")
    m.add_argument("--book", default="hodder_edx_al1", choices=list(BOOKS))
    m.add_argument("--src")
    m.add_argument("cache", nargs="+", help="ocr.py 的缓存;后面的覆盖前面的(单张重读)")
    m.add_argument("--out", required=True)
    x = sub.add_parser("fixes", help="按对照题图写下的改正(或认可)取出 --check-text 拒收的题")
    x.add_argument("cache")
    x.add_argument("fixes")
    x.add_argument("--out", required=True)
    args = ap.parse_args()
    default = os.path.join(paths.RAW, "book_questions", getattr(args, "book", ""), "questions.json")
    if args.cmd == "extract":
        extract(args.pdf, args.book, args.out or default)
    elif args.cmd == "fixes":
        fixes_cache(args.cache, args.fixes, args.out)
    elif args.cmd == "marks":
        marks_cache(args.src or default, args.cache, args.out)
    else:
        add(args.src or default, args.write)


if __name__ == "__main__":
    main()
