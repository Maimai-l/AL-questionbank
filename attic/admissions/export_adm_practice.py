#!/usr/bin/env python3
"""Question data for the TMUA / TARA practice page (assets/adm_practice.html).

    python3 pipeline/export/export_adm_practice.py      data/adm_practice.js

Writes window.ADM: the papers (TMUA papers 1 and 2; TARA = TSA section 1 and BMAT
section 1) and their questions. A question whose figure or options are drawn is shown
as its original image (img_adm/) with letter-only options; the others as text with
their option texts. Practice records are not here: the page keeps them in the
browser and exports them to a separate file.
"""
import json, os, re, sqlite3, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from lib import paths  # noqa: E402

EXAMS = {"TMUA": ("TMUA", "Paper", 75), "TSA": ("TARA", "Section", 90), "BMAT": ("TARA", "Section", 60)}
OPT = re.compile(r"^\s*([A-H])(\s|$)")
MATH = re.compile(r"(\$\$.*?\$\$|\$[^$]*\$|!\[[^\]]*\]\([^)]*\)|`[^`]*`)", re.S)
SYM = {"≤": r"\leq ", "≥": r"\geq ", "≠": r"\neq ", "−": "-", "×": r"\times ", "π": r"\pi "}
TOK = r"(?:\d+(?:\.\d+)?[a-z]?(?![A-Za-z])|[A-Za-z]\([^()$]{1,8}\)|[A-Za-z](?![A-Za-z'’(])|\([^()$]{1,12}\))"
EXPR = re.compile(r"(?<![\w$\\])-?" + TOK + r"(?:\s*[=<>≤≥≠+\-−]\s*-?" + TOK + r")+(?![\w$])")
VAR = re.compile(r"(?<![\w$\\'’(-])([b-zB-HJ-Z])(?![\w$'’()-])")
COORD = re.compile(r"(?<![\w$])\(\s*-?\d+(?:\.\d+)?\s*,\s*-?\d+(?:\.\d+)?\s*\)")
NUM = re.compile(r"^\s*[-−]\s*\d+(?:\.\d+)?\s*$")


USD = "\ue000"   # a dollar sign that is money, not maths; the page shows it as "$"


def money(text):
    """TSA/BMAT write prices as $100: mark those dollars so KaTeX does not pair them
    up as maths. A "$" is money when a digit follows it directly, or when the text up to
    the next "$" is ordinary words; $$…$$ and $ x^{2} $ stay maths."""
    out, i, t = [], 0, text or ""
    while i < len(t):
        if t.startswith("$$", i):
            j = t.find("$$", i + 2)
            j = len(t) if j < 0 else j + 2
            out.append(t[i:j]); i = j
            continue
        if t[i] != "$":
            out.append(t[i]); i += 1
            continue
        j = t.find("$", i + 1)
        inner = t[i + 1:j] if j > 0 else t[i + 1:]
        if j < 0 or re.match(r"\d", t[i + 1:i + 2]) or (
                not re.search(r"[\\^_{}]", inner) and re.search(r"[A-Za-z]{3,}", inner)):
            out.append(USD); i += 1
            continue
        out.append(t[i:j + 1]); i = j + 1
    return "".join(out)


def tidy(text):
    """TMUA text written outside $…$ (x = 1, -2 < c < 7, values of x) set as maths, so
    it reads like the paper; only for the practice page, the bank keeps its text."""
    out = []
    for i, part in enumerate(MATH.split(text or "")):
        if i % 2:
            out.append(part)
            continue
        def wrap(m):
            t = m.group(0)
            for k, v in SYM.items():
                t = t.replace(k, v)
            return "$" + t.strip() + "$"
        if NUM.match(part):
            return "$" + re.sub(r"[-−]\s*", "-", part.strip()) + "$"
        part = COORD.sub(wrap, EXPR.sub(wrap, part))
        out.append(VAR.sub(lambda m: "$" + m.group(1) + "$", part) if "$" not in part else
                   "".join(VAR.sub(lambda m: "$" + m.group(1) + "$", x) if j % 2 == 0 else x
                           for j, x in enumerate(re.split(r"(\$[^$]*\$)", part))))
    return "".join(out)


def stem(text, letters):
    """The question text without its number and option lines, or None if the option
    block is not found."""
    lines = text.strip().splitlines()
    for i in range(len(lines) - 1, -1, -1):
        m = OPT.match(lines[i])
        if m and m.group(1) == letters[0] and any(OPT.match(x) and OPT.match(x).group(1) == letters[1] for x in lines[i + 1:]):
            return re.sub(r"^\d+\s+", "", "\n".join(lines[:i]).strip())
    return None


def main(out=os.path.join(paths.DATA, "adm_practice.js")):
    con = sqlite3.connect(paths.DB)
    con.row_factory = sqlite3.Row
    papers, qs, topics, images = {}, {}, {}, 0
    for r in con.execute("SELECT * FROM questions WHERE syllabus IN ('TMUA','TSA','BMAT') ORDER BY syllabus, series, component, q"):
        group, part, minutes = EXAMS[r["syllabus"]]
        pid = r["id"].rsplit("-q", 1)[0]
        when = "Specimen" if r["series"] == "spec" else str(r["year"])
        p = papers.setdefault(pid, {"id": pid, "exam": group, "test": r["syllabus"], "year": r["year"],
                                    "title": f'{r["syllabus"]} {when} {part} {r["component"]}', "minutes": minutes, "q": []})
        p["q"].append(r["id"])
        topics.setdefault(group, {})[r["topic"]] = r["topic_name"]
        letters = json.loads(r["options"] or "[]") or list("ABCDE")
        opts = json.loads(r["option_texts"]) if r["option_texts"] else None
        text = r["question_latex"] or r["question_text"] or ""
        s = stem(text, letters) if opts else None
        drawn = r["has_diagram"] or not opts or s is None or any(not v or "图形选项" in v for v in opts.values())
        q = {"p": pid, "n": r["q"], "t": r["topic"], "a": r["answer"], "L": "".join(letters),
             "x": re.sub(r"^\*\*答案[::]\s*[A-H]\*\*\s*", "", (r["ms_latex"] or r["ms_text"] or "").strip())}
        if drawn:
            q["img"] = r["image"]
            images += 1
        else:
            fix = tidy if r["syllabus"] == "TMUA" else money
            q["s"] = fix(s)
            q["img0"] = r["image"]
            q["o"] = [fix(opts.get(k, "")) for k in letters]
        qs[r["id"]] = q
    data = {"papers": sorted(papers.values(), key=lambda p: (p["exam"], p["test"], -p["year"], p["title"])),
            "topics": topics, "q": qs}
    with open(out, "w", encoding="utf-8") as f:
        f.write("window.ADM=" + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";\n")
    print(f"{len(papers)} 份卷 {len(qs)} 题(其中 {images} 题显示原题图)-> {os.path.relpath(out, paths.ROOT)}")


if __name__ == "__main__":
    main()
