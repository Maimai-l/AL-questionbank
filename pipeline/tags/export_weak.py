#!/usr/bin/env python3
"""Export the weakest-tagged groups for model re-tagging.

Keyword scoring fails where the vocabulary does not separate the topics:
9709 Paper 4 Mechanics, 9231 Paper 3 Further Mechanics, 9618 Paper 4 Practical.
Now that question_latex exists, a model can read the actual question instead.
"""
import json, os, sqlite3, sys

GROUPS = [("9709", "4"), ("9231", "3"), ("9618", "4"), ("9618", "2")]
BATCH = 60


def main(dbpath, outdir):
    os.makedirs(outdir, exist_ok=True)
    con = sqlite3.connect(dbpath)
    con.row_factory = sqlite3.Row
    manifest = []
    for syl, comp in GROUPS:
        rows = con.execute(
            "SELECT id, syllabus, component, q, marks, topic, topic_margin, "
            "       question_latex, question_text, ms_text, image "
            "FROM questions WHERE syllabus=? AND component=? ORDER BY id",
            (syl, comp)).fetchall()
        items = []
        for r in rows:
            body = (r["question_latex"] or r["question_text"] or "")[:1400]
            ms = (r["ms_text"] or "")[:700]
            items.append({"id": r["id"], "marks": r["marks"],
                          "image": r["image"], "question": body,
                          "mark_scheme_excerpt": ms,
                          "keyword_tag": r["topic"],
                          "was_tie": r["topic_margin"] == 0})
        for i in range(0, len(items), BATCH):
            name = f"{syl}_p{comp}_batch{i//BATCH + 1}.json"
            json.dump(items[i:i + BATCH], open(os.path.join(outdir, name), "w"),
                      ensure_ascii=False, indent=1)
            manifest.append((name, len(items[i:i + BATCH])))
        print(f"{syl} P{comp}: {len(items)} questions")
    for n, c in manifest:
        print(f"  {n}  ({c})")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
