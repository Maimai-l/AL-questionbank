#!/usr/bin/env python3
"""Assign syllabus topic codes, for any subject with a topic table.

  tag_any.py 9231 q9231.json ms9231.json

Scored keyword matching, scoped to the topics the component may actually
examine. Evidence is the question text plus its mark scheme, which usually
names the technique more explicitly than the question does.
"""
import collections, importlib, json, re, sys

import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))          # 项目根目录


def load(subject):
    if subject == "9709":
        from pipeline.tags import tag as m
        return m.TOPICS, {c: [k for k in m.TOPICS if k.startswith(c)] for c in "1345"}
    m = importlib.import_module(f"pipeline.tags.topics_{subject}")
    return m.TOPICS, m.COMPONENT_TOPICS


# A tie means the keyword scorer found equal evidence for two topics. Verified
# on 32 sampled ties: a *global* preference is a coin flip (11 vs 11), but the
# right direction differs by subject — in maths the earlier code is usually the
# vehicle (trig, logs, algebra) and the later code the technique being examined;
# in CS the earlier code (algorithm design) leaks programming vocabulary from
# the mark scheme and is usually right. ~21% of ties have the true topic in
# neither slot, so topic_margin == 0 should be treated as "needs review", not
# as a considered choice.
TIE_PREFERS_LATER = {"9709": True, "9231": False, "9618": False}

# Pair-level overrides where sampling gave a clear, repeatable answer.
PAIR_RULES = {
    "9709": {frozenset({"1.7", "1.8"}): "1.8",   # "f'(x) given, find f(x)"
             frozenset({"5.3", "5.4"}): "5.4"},  # geometric distribution wording
    "9231": {frozenset({"2.1", "2.4"}): "2.4",   # sum-of-rectangles bound on a series
             frozenset({"4.2", "4.3"}): "4.2"},  # t-test with tabular data
    "9618": {frozenset({"16", "19"}): "16",      # RPN belongs to translation software
             frozenset({"9", "10"}): "9",
             frozenset({"9", "11"}): "9"},
}


def break_tie(subject, scored):
    """scored is [(score, code), ...] ordered by score desc, then syllabus
    order. Returns the code to use as `topic`.

    Ties are often three-way, so the whole tied group has to be considered —
    looking only at the top two picks the middle of a 3-way tie, which is the
    worst of both directions.
    """
    top = scored[0][0]
    tied = [c for sc, c in scored if sc == top]
    if len(tied) < 2:
        return tied[0]
    rules = PAIR_RULES.get(subject, {})
    for i, a in enumerate(tied):
        for b in tied[i + 1:]:
            r = rules.get(frozenset({a, b}))
            if r:
                return r
    return tied[-1] if TIE_PREFERS_LATER.get(subject) else tied[0]


def score(text, groups):
    s = 0
    for w, kws in groups.items():
        for kw in kws:
            if kw in text:
                s += w
    return s


def main(subject, qjson, msjson):
    TOPICS, COMPONENT_TOPICS = load(subject)
    Q = json.load(open(qjson))
    M = json.load(open(msjson))
    mk = {(m["series"], m["component"], m["variant"], m["q"]): m for m in M}

    for q in Q:
        m = mk.get((q["series"], q["component"], q["variant"], q["q"]))
        text = (q["text"] + " " + (m["ms_text"] if m else "")).lower()
        text = re.sub(r"\s+", " ", text)
        codes = COMPONENT_TOPICS.get(q["component"], list(TOPICS))
        # Sort by score only; ties fall to syllabus order, not string order.
        scored = sorted(((score(text, TOPICS[c][1]), i, c)
                         for i, c in enumerate(codes)), key=lambda x: (-x[0], x[1]))
        scored = [(s, c) for s, i, c in scored]
        best = scored[0]
        second = scored[1][0] if len(scored) > 1 else 0
        chosen = break_tie(subject, scored) if best[0] > 0 else None
        q.update({
            "topic": chosen,
            "topic_name": TOPICS[chosen][0] if chosen else None,
            "topics_all": ([chosen] + [c for s, c in scored if s > 0 and c != chosen])[:3]
                          if chosen else [],
            "topic_margin": best[0] - second,
            "topic_confident": best[0] >= 5 and best[0] >= second + 3,
        })

    json.dump(Q, open(qjson, "w"), ensure_ascii=False, indent=1)
    un = sum(1 for q in Q if not q["topic"])
    conf = sum(1 for q in Q if q["topic_confident"])
    print(f"{subject}: tagged {len(Q)-un}/{len(Q)}  untagged={un}  "
          f"confident={conf} ({conf/len(Q)*100:.0f}%)")
    for comp in sorted(COMPONENT_TOPICS):
        c = collections.Counter(q["topic"] for q in Q if q["component"] == comp)
        line = ", ".join(f"{k}:{v}" for k, v in
                         sorted(c.items(), key=lambda x: (x[0] is None, str(x[0]))))
        print(f"  P{comp}: {line}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])
