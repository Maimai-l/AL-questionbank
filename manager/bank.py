"""Read-only views of the bank for the data manager (docs/data-manager.md, F1 and F2)."""
import json
import os
import re
import struct

from lib import db, paths

EXAMS = [("9709", "9709 Mathematics"), ("9231", "9231 Further Mathematics"),
         ("9618", "9618 Computer Science"), ("TMUA", "TMUA"), ("TSA", "TSA"), ("BMAT", "BMAT")]
CIE = {"9709", "9231", "9618"}
SEASON = {"m": "F/M", "s": "M/J", "w": "O/N"}
MONTH = {"m": 3, "s": 6, "w": 11}


def paper_code(r):
    """9709/12/M/J/23 for CAIE; TMUA/1/2016 for the admissions tests."""
    if r["syllabus"] in CIE:
        return f'{r["paper"]}/{SEASON.get(r["series"][0], "?")}/{r["series"][1:]}'
    return f'{r["paper"]}/{r["year"]}'


def task_label(t):
    return t.replace("_", " ").capitalize()


def _tasks(part_data):
    if not part_data:
        return []
    try:
        parts = json.loads(part_data).get("parts", [])
    except ValueError:
        return []
    return sorted({p["task"] for p in parts if p.get("task")})


def rows(exam):
    """Every question of one exam, as the query table needs it."""
    con = db.connect()
    qs = con.execute(
        "SELECT id, syllabus, component, paper, series, year, month, q, marks, parts, topic, "
        "topic_name, subtopic, has_diagram, part_data, "
        "explanation IS NOT NULL AND explanation != '' AS has_expl "
        "FROM questions WHERE syllabus = ?", (exam,)).fetchall()
    last = {}
    for r in qs:
        key = (r["paper"], r["series"])
        last[key] = max(last.get(key, 0), r["q"])
    out = []
    for r in qs:
        parts = json.loads(r["parts"] or "[]")
        out.append({
            "id": r["id"], "code": paper_code(r), "component": r["component"],
            "paper": r["paper"].split("/")[-1], "year": r["year"],
            "month": MONTH.get(r["series"][0], r["month"]) if r["syllabus"] in CIE else r["month"],
            "q": r["q"], "marks": r["marks"] or 0, "parts": len(parts) or 1,
            "position": round(r["q"] / last[(r["paper"], r["series"])], 3),
            "topic": r["topic"], "subtopic": r["subtopic"],
            "tasks": _tasks(r["part_data"]),
            "diagram": bool(r["has_diagram"]), "explanation": bool(r["has_expl"]),
        })
    return out


def meta():
    """What the condition panel offers for each exam, with counts."""
    con = db.connect()
    out = []
    for exam, label in EXAMS:
        comps = con.execute(
            "SELECT component, component_name, COUNT(*) n FROM questions WHERE syllabus = ? "
            "GROUP BY component ORDER BY component", (exam,)).fetchall()
        topics = con.execute(
            "SELECT component, topic, topic_name, COUNT(*) n FROM questions WHERE syllabus = ? "
            "AND topic IS NOT NULL GROUP BY component, topic ORDER BY topic", (exam,)).fetchall()
        years = [r[0] for r in con.execute(
            "SELECT DISTINCT year FROM questions WHERE syllabus = ? ORDER BY year", (exam,))]
        out.append({
            "exam": exam, "label": label, "cie": exam in CIE, "years": years,
            "components": [{"value": r["component"], "label": _component_label(exam, r), "n": r["n"]}
                           for r in comps],
            "topics": [{"component": r["component"], "value": r["topic"],
                        "label": f'{r["topic"]} {r["topic_name"]}', "n": r["n"]} for r in topics],
        })
    return out


def _component_label(exam, r):
    if exam in CIE:
        return f'Paper {r["component"]}'
    return r["component_name"].split(" (")[0]


# ------------------------------------------------------------------ one question

def _png_size(path):
    with open(path, "rb") as f:
        head = f.read(24)
    return struct.unpack(">II", head[16:24]) if head[:8] == b"\x89PNG\r\n\x1a\n" else None


def _image(path):
    if not path:
        return None
    size = _png_size(path)
    rel = paths.relative_to_data(path)
    return {"src": "/q/" + rel, "width": size[0], "height": size[1]} if size else None


MARK = re.compile(r"^(\*|D|SC\s*)?[A-Z]{1,2}\d")
PART = re.compile(r"^\s*(\d+(?:\([a-z]+\))?(?:\([ivx]+\))?)\s+")


def scheme_rows(ms):
    """Mark-scheme text (rows of `answer | marks | guidance`) as a list of rows.
    Lines without a bar continue the guidance of the row above; a bare number
    is the part total and is dropped."""
    out = []
    for line in (ms or "").splitlines():
        if not line.strip():
            continue
        if "|" not in line:
            if re.fullmatch(r"\s*\d+\s*", line) or not out:
                continue
            out[-1]["guide"] = (out[-1]["guide"] + "\n" + line.strip()).strip()
            continue
        cells = [c.strip() for c in line.split("|")]
        answer, code = cells[0], cells[1] if len(cells) > 1 else ""
        guide = " | ".join(cells[2:]) if len(cells) > 2 else ""
        m = PART.match(answer)
        part = m.group(1) if m and not re.fullmatch(r"\d+", answer.strip()) else ""
        if part:
            answer = answer[m.end():]
        if re.fullmatch(r"\d+", answer.strip()) and not MARK.match(code):
            if out and code:                 # part total, then guidance that ran on
                out[-1]["guide"] = (out[-1]["guide"] + "\n" + code).strip()
            continue
        out.append({"part": part, "answer": answer, "code": code, "guide": guide})
    return out


def detail(qid):
    con = db.connect()
    r = con.execute("SELECT * FROM questions WHERE id = ?", (qid,)).fetchone()
    if not r:
        return None
    img = paths.resolve(r["image"])
    expl = json.loads(r["explanation"]) if r["explanation"] else None
    return {
        "id": r["id"], "exam": r["syllabus"], "code": paper_code(r), "q": r["q"],
        "marks": r["marks"], "topic": r["topic"], "topic_name": r["topic_name"],
        "diagram": bool(r["has_diagram"]),
        "image": _image(img), "image_space": _image(paths.answer_space(r["image"])),
        "text": r["question_latex"] or r["question_text"],
        "scheme": scheme_rows(r["ms_latex"] or r["ms_text"]) if r["syllabus"] in CIE else None,
        "solution": None if r["syllabus"] in CIE else (r["ms_latex"] or r["ms_text"]),
        "answer": r["answer"],
        "options": json.loads(r["option_texts"]) if r["option_texts"] else None,
        "explanation": expl,
        "pages": json.loads(r["qp_pages"] or "[]"),
        "paper_pdf": bool(paper_pdf(r)),
    }


def paper_pdf(r):
    """The original question paper, if it is on this machine."""
    name = r["qp_pdf"]
    if not name:
        return None
    for base in (paths.PAPERS, os.path.join(paths.RAW, "pdf"), paths.RAW):
        p = os.path.join(base, name)
        if os.path.exists(p):
            return p
    return None


def search(exam, text):
    """Question ids of one exam whose text or mark scheme matches."""
    con = db.connect()
    try:
        return [r[0] for r in con.execute(
            "SELECT q.id FROM questions q JOIN q_fts f ON f.id = q.id "
            "WHERE q.syllabus = ? AND q_fts MATCH ?", (exam, text))]
    except Exception:                       # a query the full-text index cannot parse
        return []


def exists(ids):
    con = db.connect()
    found = set()
    for i in range(0, len(ids), 500):
        chunk = ids[i:i + 500]
        found |= {r[0] for r in con.execute(
            f"SELECT id FROM questions WHERE id IN ({','.join('?' * len(chunk))})", chunk)}
    return found
