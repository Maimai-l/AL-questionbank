#!/usr/bin/env python3
"""Fold model re-tagging results back into the question JSON.

Keyword scoring is weakest where vocabulary does not separate the topics
(9709 Mechanics, 9231 Further Mechanics, 9618 Practical). Those groups were
re-read question by question by a model; this applies the result and records
`topic_source` so a caller can tell a verified tag from a scored guess.
"""
import glob, importlib, json, os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))          # 项目根目录


def topic_names(subject):
    if subject == "9709":
        from pipeline.tags import tag as m
        return {k: v[0] for k, v in m.TOPICS.items()}
    m = importlib.import_module(f"pipeline.tags.topics_{subject}")
    return {k: v[0] for k, v in m.TOPICS.items()}


def main(retagdir, pairs):
    results = {}
    for f in sorted(glob.glob(os.path.join(retagdir, "out_*.json"))):
        for r in json.load(open(f)):
            results[r["id"]] = r
    print(f"{len(results)} model tags loaded")

    for subject, qjson in pairs:
        names = topic_names(subject)
        Q = json.load(open(qjson))
        changed = applied = 0
        for q in Q:
            qid = f"{subject}_{q['series']}_{q['component']}{q['variant']}_q{q['q']:02d}"
            r = results.get(qid)
            if not r:
                q.setdefault("topic_source", "keyword")
                continue
            applied += 1
            if q.get("topic") != r["topic"]:
                changed += 1
            q["topic"] = r["topic"]
            q["topic_name"] = names.get(r["topic"], r["topic"])
            q["topic_source"] = "model"
            q["topic_note"] = r.get("note", "")
            q["topic_confident"] = r.get("confidence") == "high"
            # a model read the question; the keyword margin no longer applies
            q["topic_margin"] = None
            if r["topic"] not in q.get("topics_all", []):
                q["topics_all"] = [r["topic"]] + [c for c in q.get("topics_all", [])
                                                  if c != r["topic"]][:2]
        json.dump(Q, open(qjson, "w"), ensure_ascii=False, indent=1)
        print(f"  {subject}: applied {applied}, changed {changed}")


if __name__ == "__main__":
    main(sys.argv[1], [("9709", "questions_raw.json"),
                       ("9231", "q9231.json"),
                       ("9618", "q9618.json")])
