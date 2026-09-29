#!/usr/bin/env python3
"""Build the prerequisite graph — what you need to know before topic X.

This is the piece that separates a drill tool from a teacher. When a student
misses a question on 9231 2.3 Differentiation, the useful response is rarely
"do more 2.3": the gap is usually upstream, in 9709 3.4 or 1.7. Without an
ordering there is nothing to say except "try again".

Every edge records where it came from, because the three sources are not
equally trustworthy:

  syllabus      Cambridge states it outright — the 9231 prior-knowledge table,
                and sentences like "Knowledge of the content of Paper 1 is
                assumed". Authoritative.
  name-match    the same topic name reappearing in a later component
                (1.7 Differentiation -> 3.4 Differentiation -> 9231 2.3
                Differentiation). Direction comes from the component edges
                above, so this is derived, not asserted.
  co-occurrence two topics that keep sharing a question's shortlist. This is
                *relatedness*, not precedence, and is labelled as such.

Nothing here is my opinion about what depends on what.

    python3 prereq.py syllabus.json caie.db
"""
import json, re, sqlite3, sys
from collections import Counter, defaultdict

import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))          # 项目根目录
from lib import paths

# "9231 Paper 3: Further Mechanics" ... "9709 Papers 1, 3 and 4"
TABLE_RE = re.compile(
    r"9231 Paper (\d)\s*:.*?9709 Papers?\s+([\d,\sand]+?)(?=\s*(?:9231 Paper|Please see|$))",
    re.S)
# "Knowledge of the content of Paper 1: Pure Mathematics 1 is assumed"
SELF_RE = re.compile(r"[Kk]nowledge of (?:the content (?:of|for) )?"
                     r"(?:Paper (\d)|.*?Paper (\d))[^.]*?is assumed")


def component_edges(spec):
    """(syllabus, component) -> list of prerequisite (syllabus, component)."""
    edges = defaultdict(list)

    fm = spec.get("9231")
    if fm:
        blob = fm.get("prior_knowledge") or ""
        for comp, papers in TABLE_RE.findall(blob):
            for n in re.findall(r"\d", papers):
                edges[("9231", comp)].append(("9709", n))

    for code, s in spec.items():
        for p in s["prerequisites"]:
            m = SELF_RE.search(p["text"])
            if m and p["component"]:
                src = m.group(1) or m.group(2)
                if src and src != p["component"]:
                    edges[(code, p["component"])].append((code, src))
    # 9618 states no prerequisites in prose, but its contents tree splits the
    # sections into an AS half and an A Level half, and the A Level papers are
    # taken after the AS ones. Derive the edge from that split rather than
    # asserting it: sections 1-12 sit under "AS content", 13-20 under
    # "A Level content", and papers 1-2 / 3-4 follow the same line.
    cs = spec.get("9618")
    if cs and set(cs.get("levels") or []) == {"AS", "A Level"}:
        for later in ("3", "4"):
            edges[("9618", later)] += [("9618", "1"), ("9618", "2")]

    for k in edges:
        edges[k] = sorted(set(edges[k]))
    return edges


def norm(name):
    n = re.sub(r"\(.*?\)", " ", (name or "").lower())
    n = re.sub(r"[^a-z ]", " ", n)
    n = re.sub(r"\b(further|introduction to|and|the|of|its)\b", " ", n)
    return " ".join(sorted(set(n.split())))


def reachable(edges, node, seen=None):
    seen = seen if seen is not None else set()
    for p in edges.get(node, ()):
        if p not in seen:
            seen.add(p)
            reachable(edges, p, seen)
    return seen


def main(spec_path=None, db=None, out=None):
    spec_path = spec_path or paths.SYLLABUS
    db = db or paths.DB
    out = out or paths.PREREQ
    spec = json.load(open(spec_path))
    comp_edges = component_edges(spec)

    topics = {}
    for code, s in spec.items():
        for tc, t in s["topics"].items():
            topics[(code, tc)] = t

    # ---- name matches, directed by the component graph -------------------
    by_name = defaultdict(list)
    for key, t in topics.items():
        by_name[norm(t["name"])].append(key)

    edges = []
    for nm, group in by_name.items():
        if len(group) < 2 or not nm:
            continue
        for a in group:
            up = reachable(comp_edges, (a[0], topics[a]["component"]))
            for b in group:
                if a == b:
                    continue
                if (b[0], topics[b]["component"]) in up:
                    edges.append({"from": f"{b[0]}:{b[1]}", "to": f"{a[0]}:{a[1]}",
                                  "kind": "prerequisite", "source": "name-match",
                                  "name": topics[a]["name"]})

    # ---- co-occurrence in the bank's own shortlists -----------------------
    con = sqlite3.connect(db)
    pair = Counter()
    seen_topic = Counter()
    for syl, ta in con.execute(
            "SELECT syllabus, topic_all FROM questions WHERE topic_all IS NOT NULL"):
        try:
            lst = json.loads(ta)[:2]
        except Exception:
            continue
        for c in lst:
            seen_topic[(syl, c)] += 1
        if len(lst) == 2 and lst[0] != lst[1]:
            pair[(syl,) + tuple(sorted(lst))] += 1

    related = []
    for (syl, a, b), n in pair.most_common():
        base = min(seen_topic[(syl, a)], seen_topic[(syl, b)]) or 1
        if n >= 12 and n / base >= 0.18:
            related.append({"a": f"{syl}:{a}", "b": f"{syl}:{b}",
                            "kind": "related", "source": "co-occurrence",
                            "questions": n, "share": round(n / base, 2)})

    doc = {
        "components": {f"{k[0]}:P{k[1]}": [f"{s}:P{c}" for s, c in v]
                       for k, v in sorted(comp_edges.items())},
        "topic_prerequisites": edges,
        "topic_related": related,
    }
    json.dump(doc, open(out, "w"), ensure_ascii=False, indent=1)

    print("卷与卷之间的先修(大纲明文):")
    for k, v in sorted(doc["components"].items()):
        print(f"  {k:<12} <- {', '.join(v)}")
    print(f"\n同名主题的先修链(由上表定向):{len(edges)} 条")
    for e in edges[:12]:
        print(f"  {e['from']:<12} -> {e['to']:<12} {e['name']}")
    print(f"\n常同时出现的主题(题库统计,只是相关不是先修):{len(related)} 对")
    for e in related[:10]:
        print(f"  {e['a']:<10} ~ {e['b']:<10} {e['questions']} 题 ({e['share']:.0%})")
    print(f"\n-> {out}")


if __name__ == "__main__":
    a = sys.argv[1:]
    main(*a)
