"""What can be ticked when marking an attempt, part by part.

Three kinds, by the exam:

  codes   9709 / 9231: every row of the scheme with award codes in its
          Marks cell ("M1", "A1 B1", "*M1", "DM1", "B2,1,0", "A1FT") gives
          one item per code, with the row's answer and guidance. An A or DM
          mark depends on the method mark before it in the same part
          (A on the last M, DM on the last *M), which the page enforces.
  points  9618: the marking points of the worked explanation (explain_batches
          .py), each with how it is awarded ("1", "1 per bullet, max 2");
          the part scores at most its marks.
  choice  TMUA / TSA / BMAT: the options and the key; the page marks it.

Where the scheme lists alternative methods, the items of the first method
are used (the shortest run of rows worth the part's marks).

A part whose scheme gives no items (or items that do not add up to its
marks) is marked by entering a score, "score".
"""
import json
import re

CODE = r"\*?(?:DM|DB|SC ?B|M|A|B)\d(?:,\d)*(?:FT|ft)?"
CODE_CELL = re.compile(rf"(?:{CODE})+")
CODE_TOKEN = re.compile(CODE)


def _clean(cell):
    return re.sub(r"[\$\^\{\}\s]", "", cell)


def code_items(ms):
    """Award-code items of one part's scheme, in order."""
    items, pending = [], []
    for line in (ms or "").splitlines():
        cells = [c.strip() for c in line.split("|")]
        at = next((i for i, c in enumerate(cells) if c and CODE_CELL.fullmatch(_clean(c))), None)
        if at is None:
            if line.strip():
                pending.append(line.strip())
            continue
        answer = " ".join(pending + [c for c in cells[:at] if c])
        answer = re.sub(r"^\d+(\([a-z]+\))*\s+", "", answer).strip()
        guidance = " | ".join(c for c in cells[at + 1:] if c)
        pending = []
        for tok in CODE_TOKEN.findall(_clean(cells[at])):
            values = [int(v) for v in re.findall(r"\d", tok.split("FT")[0].split("ft")[0])]
            kind = re.sub(r"[\d,*]|FT|ft", "", tok).replace(" ", "")
            items.append({"code": tok, "kind": kind, "value": values[0],
                          "partial": values[1:] if len(values) > 1 else [],
                          "star": tok.startswith("*"), "ft": "FT" in tok.upper(),
                          "answer": answer, "guidance": guidance})
    # dependencies: A on the last M, DM / DB on the last *M
    last_m = last_star = None
    for i, it in enumerate(items):
        if it["kind"] == "M":
            last_m = i
            if it["star"]:
                last_star = i
        elif it["kind"] == "A" and last_m is not None:
            it["depends"] = last_m
        elif it["kind"] in ("DM", "DB") and last_star is not None:
            it["depends"] = last_star
    return items


def main_method(items, marks):
    """The items of the first method when the scheme lists alternatives after
    it (Method 2, OR ...): the shortest prefix worth exactly the part's marks."""
    if not marks or sum(i["value"] for i in items) <= marks:
        return items
    total = 0
    for n, it in enumerate(items, 1):
        total += it["value"]
        if total == marks:
            return items[:n]
    return items


def point_items(points):
    out = []
    for p in points or []:
        mark = str(p.get("mark", "1"))
        m = re.match(r"\s*(\d+)", mark)
        out.append({"code": mark, "value": int(m.group(1)) if m else 1,
                    "answer": p.get("point", ""), "guidance": p.get("why", "")})
    return out


def parts(row):
    """[{label, marks, kind, items, max}] for one question row (sqlite3.Row / dict)."""
    syl = row["syllabus"]
    if syl in ("TMUA", "TSA", "BMAT"):
        opts = json.loads(row["option_texts"]) if row["option_texts"] else None
        return [{"label": "", "marks": 1, "kind": "choice", "options": opts,
                 "answer": (row["answer"] or "").strip()}]
    pd = json.loads(row["part_data"]) if row["part_data"] else {}
    ex = json.loads(row["explanation"]) if row["explanation"] else {}
    ex_by = {p["label"]: p for p in ex.get("parts", [])}
    labels = pd.get("parts") or [{"label": "", "marks": row["marks"], "ms": None}]
    whole_ms = row["ms_latex"] or row["ms_text"]
    out = []
    for p in labels:
        marks = p.get("marks") or (row["marks"] if len(labels) == 1 else None)
        if syl == "9618":
            items = point_items((ex_by.get(p["label"]) or {}).get("points"))
            kind = "points" if items else "score"
        else:
            items = main_method(code_items(p.get("ms") or (whole_ms if len(labels) == 1 else None)),
                                marks)
            full = sum(i["value"] for i in items)
            kind = "codes" if items and (marks is None or full == marks) else "score"
        out.append({"label": p["label"], "marks": marks, "kind": kind,
                    "items": items, "ms": p.get("ms")})
    return out
