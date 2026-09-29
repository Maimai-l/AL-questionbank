#!/usr/bin/env python3
"""Measure the syllabus-derived tagger against the hand-written keyword one.

Ground truth is the 768 questions a model re-tagged by reading the question
itself. Two caveats worth stating plainly:

* those are not gold labels, they are a second opinion — a good one, but a
  model's;
* they are also the *hardest* three groups in the bank (9709 Mechanics,
  9231 Further Mechanics, 9618 Practical and Problem-solving), chosen at the
  time precisely because keyword scoring did worst on them. Accuracy here is a
  floor, not an average.

Both taggers are fed exactly the same text so the comparison is about the
evidence, not about who got the cleaner input.

    python3 eval_tags.py caie.db
"""
import re, sqlite3, sys
from collections import defaultdict

sys.path.insert(0, __file__.rsplit("/", 1)[0] if "/" in __file__ else ".")
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))          # 项目根目录
from lib import paths
from pipeline.tags import tag_any, topic_model


def rows(db):
    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    return con.execute(
        "SELECT id, syllabus, component, topic, "
        "COALESCE(question_latex, question_text) AS q, "
        "COALESCE(ms_latex, ms_text) AS ms "
        "FROM questions WHERE topic_source='model' AND topic IS NOT NULL"
    ).fetchall()


def keyword_pick(subject, component, text):
    TOPICS, COMPONENT_TOPICS = tag_any.load(subject)
    codes = COMPONENT_TOPICS.get(str(component), list(TOPICS))
    scored = sorted(((tag_any.score(text, TOPICS[c][1]), i, c)
                     for i, c in enumerate(codes)), key=lambda x: (-x[0], x[1]))
    scored = [(s, c) for s, i, c in scored]
    if not scored or scored[0][0] == 0:
        return None, 0
    margin = scored[0][0] - (scored[1][0] if len(scored) > 1 else 0)
    return tag_any.break_tie(subject, scored), margin


def main(db=None):
    models = topic_model.load()
    data = rows(db)
    print(f"验证集:{len(data)} 道模型逐题重标的题\n")

    stat = defaultdict(lambda: {"n": 0, "kw": 0, "syl": 0, "syl3": 0,
                                "either": 0, "both_wrong": 0})
    misses = []
    for r in data:
        syl, comp, truth = r["syllabus"], str(r["component"]), r["topic"]
        text = re.sub(r"\s+", " ", (r["q"] or "") + " " + (r["ms"] or "")).lower()

        kw, _ = keyword_pick(syl, comp, text)
        ranked = models[syl].score(r["q"] or "", comp, r["ms"] or "")
        # 9618 tags by section; the syllabus model scores sub-topics
        ordered = [c.split(".")[0] if syl == "9618" else c for _, c, _ in ranked]
        seen, top = set(), []
        for c in ordered:
            if c not in seen:
                seen.add(c); top.append(c)
        pick = top[0] if top else None

        k = f"{syl} P{comp}"
        s = stat[k]
        s["n"] += 1
        s["kw"] += kw == truth
        s["syl"] += pick == truth
        s["syl3"] += truth in top[:3]
        s["either"] += (kw == truth or pick == truth)
        if kw != truth and pick != truth:
            s["both_wrong"] += 1
        if pick != truth and len(misses) < 400:
            misses.append((r["id"], truth, pick, kw, top[:3]))

    hdr = f"{'组':<10}{'题数':>6}{'关键词':>9}{'大纲模型':>11}{'大纲前三':>11}{'两者取一':>11}"
    print(hdr)
    print("-" * len(hdr.encode('utf-8')) // 2 * "-" if False else "-" * 58)
    tot = {"n": 0, "kw": 0, "syl": 0, "syl3": 0, "either": 0}
    for k in sorted(stat):
        s = stat[k]
        for f in tot:
            tot[f] += s[f]
        print(f"{k:<10}{s['n']:>6}{s['kw']/s['n']*100:>8.1f}%"
              f"{s['syl']/s['n']*100:>10.1f}%{s['syl3']/s['n']*100:>10.1f}%"
              f"{s['either']/s['n']*100:>10.1f}%")
    print("-" * 58)
    print(f"{'合计':<10}{tot['n']:>6}{tot['kw']/tot['n']*100:>8.1f}%"
          f"{tot['syl']/tot['n']*100:>10.1f}%{tot['syl3']/tot['n']*100:>10.1f}%"
          f"{tot['either']/tot['n']*100:>10.1f}%")

    print("\n大纲模型判错的样本(真值 -> 模型 / 关键词):")
    for qid, truth, pick, kw, top3 in misses[:20]:
        print(f"  {qid:<20} {truth:<5} -> {str(pick):<5} / {str(kw):<5}   前三 {top3}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else paths.DB)


# --------------------------------------------------------------- strategies
def strategies(db=None):
    """The syllabus model has excellent top-3 recall but mediocre top-1, and
    the keyword table is the other way round. Measure the obvious ways of
    putting them together."""
    models = topic_model.load()
    data = rows(db)
    res = defaultdict(lambda: defaultdict(int))
    for r in data:
        syl, comp, truth = r["syllabus"], str(r["component"]), r["topic"]
        text = re.sub(r"\s+", " ", (r["q"] or "") + " " + (r["ms"] or "")).lower()

        TOPICS, COMPONENT_TOPICS = tag_any.load(syl)
        codes = COMPONENT_TOPICS.get(comp, list(TOPICS))
        kwscore = {c: tag_any.score(text, TOPICS[c][1]) for c in codes}
        kw, _ = keyword_pick(syl, comp, text)

        ranked = models[syl].score(r["q"] or "", comp, r["ms"] or "")
        agg = {}
        for s, c, _h in ranked:
            k = c.split(".")[0] if syl == "9618" else c
            agg[k] = max(agg.get(k, 0.0), s)
        top = sorted(agg, key=lambda c: -agg[c])

        kmax = max(kwscore.values()) or 1
        smax = max(agg.values()) if agg else 1

        picks = {
            "关键词": kw,
            "大纲": top[0] if top else None,
            "关键词优先,大纲前三兜底": kw if kw in top[:3] else (top[0] if top else kw),
            "大纲前三 + 关键词重排": (max(top[:3], key=lambda c: kwscore.get(c, 0))
                                     if top else kw),
            "分数相加": (max(agg, key=lambda c: agg[c] / smax + kwscore.get(c, 0) / kmax)
                        if agg else kw),
        }
        for name, p in picks.items():
            res[name]["n"] += 1
            res[name]["ok"] += p == truth
            res[f"{name}|{syl} P{comp}"]["n"] += 1
            res[f"{name}|{syl} P{comp}"]["ok"] += p == truth

    print("\n\n组合策略(同一验证集)")
    names = ["关键词", "大纲", "关键词优先,大纲前三兜底", "大纲前三 + 关键词重排", "分数相加"]
    groups = sorted({k.split("|")[1] for k in res if "|" in k})
    print(f"{'策略':<26}" + "".join(f"{g:>11}" for g in groups) + f"{'合计':>10}")
    for nm in names:
        line = f"{nm:<26}"
        for g in groups:
            d = res[f"{nm}|{g}"]
            line += f"{d['ok']/d['n']*100:>10.1f}%"
        d = res[nm]
        line += f"{d['ok']/d['n']*100:>9.1f}%"
        print(line)
