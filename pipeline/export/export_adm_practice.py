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
            q["s"] = s
            q["img0"] = r["image"]
            q["o"] = [opts.get(k, "") for k in letters]
        qs[r["id"]] = q
    data = {"papers": sorted(papers.values(), key=lambda p: (p["exam"], p["test"], -p["year"], p["title"])),
            "topics": topics, "q": qs}
    with open(out, "w", encoding="utf-8") as f:
        f.write("window.ADM=" + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";\n")
    print(f"{len(papers)} 份卷 {len(qs)} 题(其中 {images} 题显示原题图)-> {os.path.relpath(out, paths.ROOT)}")


if __name__ == "__main__":
    main()
