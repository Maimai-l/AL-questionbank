#!/usr/bin/env python3
"""Key terms of the worked explanations, counted and arranged by syllabus.

    python3 pipeline/explain/term_tree.py [--syllabus 9618] [--min 1]

Reads the terms of questions.explanation (explain_batches.py): each part
lists the terms a student has to be able to state, with the wording the mark
scheme accepts and a syllabus subsection code. Terms are merged by their
normalised name (lower case, singular, no punctuation); a term tagged with
several subsections goes under the one it is tagged with most often.

Writes to exports/ (paths.EXPORTS):
    <syllabus>_terms.md    section > subsection > term, most frequent first;
                           each term with its count, the accepted wording that
                           occurs most often and up to three question ids
    <syllabus>_terms.json  the same, for other tools (flashcards, the page)
"""
import argparse, json, os, re, sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))
from lib import db, paths  # noqa: E402


def norm(term):
    t = re.sub(r"[^a-z0-9+#/ -]", "", term.lower()).strip()
    t = re.sub(r"\s+", " ", t)
    if len(t) > 4 and t.endswith("ies"):
        t = t[:-3] + "y"
    elif len(t) > 3 and t.endswith("s") and not t.endswith(("ss", "us", "is")):
        t = t[:-1]
    return t


def collect(con, syllabus):
    terms = defaultdict(lambda: {"n": 0, "topics": Counter(), "wording": Counter(),
                                 "names": Counter(), "ids": []})
    for qid, raw in con.execute("SELECT id, explanation FROM questions "
                                "WHERE syllabus=? AND explanation IS NOT NULL "
                                "ORDER BY id", (syllabus,)):
        for part in json.loads(raw)["parts"]:
            for t in part.get("terms") or []:
                key = norm(t.get("term") or "")
                if not key:
                    continue
                e = terms[key]
                e["n"] += 1
                e["topics"][t.get("topic")] += 1
                e["names"][t["term"].strip()] += 1
                if t.get("wording"):
                    e["wording"][t["wording"].strip()] += 1
                if qid not in e["ids"]:
                    e["ids"].append(qid)
    return terms


def tree(terms, spec, minimum):
    out = defaultdict(lambda: defaultdict(list))
    for key, e in terms.items():
        if e["n"] < minimum:
            continue
        topic = e["topics"].most_common(1)[0][0]
        out[topic.split(".")[0]][topic].append({
            "term": e["names"].most_common(1)[0][0], "count": e["n"],
            "questions": len(e["ids"]),
            "wording": e["wording"].most_common(1)[0][0] if e["wording"] else "",
            "other_wordings": [w for w, _ in e["wording"].most_common(3)[1:]],
            "examples": e["ids"][:3]})
    ordered = []
    key = lambda c: [int(x) for x in c.split(".")]
    for sec in sorted(out, key=lambda s: int(s)):
        subs = []
        for sub in sorted(out[sec], key=key):
            items = sorted(out[sec][sub], key=lambda t: (-t["count"], t["term"]))
            subs.append({"code": sub, "name": spec.get(sub, {}).get("name", ""),
                         "terms": items})
        ordered.append({"code": sec, "name": spec.get(sec, {}).get("name")
                        or next((spec[k].get("component_name") for k in spec
                                 if k.split(".")[0] == sec), ""),
                        "subsections": subs})
    return ordered


def markdown(syllabus, ordered):
    lines = [f"# {syllabus} 关键术语", "",
             "按大纲小节排列,每节内按出现次数从多到少。次数为该术语在详解中"
             "被列为关键术语的小问数。", ""]
    for sec in ordered:
        lines += [f"## {sec['code']} {sec['name']}", ""]
        for sub in sec["subsections"]:
            lines += [f"### {sub['code']} {sub['name']}", ""]
            for t in sub["terms"]:
                lines.append(f"- **{t['term']}**({t['count']})— {t['wording']}")
                for w in t["other_wordings"]:
                    lines.append(f"  - 另一表述:{w}")
                lines.append(f"  - 例题:{', '.join(t['examples'])}")
            lines.append("")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--syllabus", default="9618")
    ap.add_argument("--min", type=int, default=1, help="至少出现几次才列入")
    a = ap.parse_args()
    spec = json.load(open(paths.SYLLABUS))[a.syllabus]["topics"]
    terms = collect(db.connect(), a.syllabus)
    ordered = tree(terms, spec, a.min)
    os.makedirs(paths.EXPORTS, exist_ok=True)
    base = os.path.join(paths.EXPORTS, f"{a.syllabus}_terms")
    json.dump(ordered, open(base + ".json", "w"), ensure_ascii=False, indent=1)
    open(base + ".md", "w").write(markdown(a.syllabus, ordered))
    n = sum(len(s["terms"]) for sec in ordered for s in sec["subsections"])
    top = sorted(((e["n"], k) for k, e in terms.items()), reverse=True)[:10]
    print(f"{len(terms)} 个术语(列入 {n} 个)-> {base}.md / .json")
    print("最常见:", ", ".join(f"{k}({c})" for c, k in top))


if __name__ == "__main__":
    main()
