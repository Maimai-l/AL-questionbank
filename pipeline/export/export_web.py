#!/usr/bin/env python3
"""Export the bank to a JS file the practice page can load from file://.

`fetch()` is blocked on file:// URLs, so the data has to arrive as a script
tag. Fields are shortened because the whole bank ships in one file and every
byte is parsed on load.
"""
import json, os, sqlite3, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))
from lib import paths  # noqa: E402

FIELDS = ["id", "syllabus", "component", "component_name", "paper", "year",
          "session", "series", "q", "marks", "topic", "topic_name",
          "subtopic", "subtopic_name",
          "question_latex", "question_text", "ms_latex", "ms_text",
          "has_diagram", "image", "q_quality", "ms_quality",
          "topic_source", "topic_margin", "parts", "marks_parts",
          "answer", "qtype", "options"]


def main(db=paths.DB, out=os.path.join(paths.DATA, "data.js")):
    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    rows = []
    for r in con.execute(f"SELECT {','.join(FIELDS)} FROM questions ORDER BY id"):
        d = dict(r)
        ms = d.pop("ms_latex") or d.pop("ms_text", None)
        d.pop("ms_text", None)
        rows.append({
            "id": d["id"], "s": d["syllabus"], "c": d["component"],
            "cn": d["component_name"], "p": d["paper"], "y": d["year"],
            "ses": d["session"], "ser": d["series"], "q": d["q"],
            "m": d["marks"], "t": d["topic"], "tn": d["topic_name"],
            "qt": d["question_latex"] or d["question_text"],
            "ms": ms, "msq": d["ms_quality"], "qq": d["q_quality"],
            "dia": d["has_diagram"], "img": d["image"],
            "tsrc": d["topic_source"], "tmar": d["topic_margin"],
            "st": d["subtopic"], "stn": d["subtopic_name"],
            "pt": json.loads(d["parts"] or "[]"),
            "mp": json.loads(d["marks_parts"] or "[]"),
            # admissions MCQ extras; null/empty on CAIE rows
            "ans": d["answer"], "qty": d["qtype"],
            "opt": json.loads(d["options"] or "[]"),
        })
    with open(out, "w") as f:
        f.write("window.QB=")
        json.dump(rows, f, ensure_ascii=False, separators=(",", ":"))
        f.write(";\n")
        # the prerequisite graph rides along so the stats view can say whether
        # a weak topic is the problem or merely downstream of one
        pre = {}
        path = paths.PREREQ
        if os.path.exists(path):
            pre = json.load(open(path))
        f.write("window.PRE=")
        json.dump(pre, f, ensure_ascii=False, separators=(",", ":"))
        f.write(";\n")
    print(f"{len(rows)} 题 -> {out}" + ("(含先修图)" if pre else ""))


if __name__ == "__main__":
    main(*(sys.argv[1:] or []))
