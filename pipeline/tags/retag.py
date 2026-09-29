#!/usr/bin/env python3
"""Re-tag the bank using the syllabus model as a second opinion.

The measurement (`eval_tags.py`, 768 model-read questions) said something I
did not expect: the syllabus-derived scorer is **worse** than the hand-written
keyword table on top-1 overall — 62.6% against 75.7% — but far better exactly
where the keyword table is uncertain.

    subset                  n     keyword   syllabus   summed   syllabus top-3
    tie, margin = 0        48       41.7%      62.5%    75.0%       95.8%
    margin = 1             84       52.4%      47.6%    63.1%       92.9%
    margin >= 2           636       81.3%      64.6%    80.3%       95.4%

So replacing the tagger wholesale would make the bank worse. What the syllabus
model is actually good for is the third column and the fourth:

* where the keyword table found no separation (margin <= 1, ~15% of the bank),
  the summed score beats it by 11-33 points;
* its top-3 contains the right topic 95% of the time, in every group. That is
  a genuinely new thing to offer — `topic_all` stops being "the runners-up in
  a scoring scheme I invented" and becomes a shortlist worth reading.

Hence: keyword keeps the confident cases, the sum decides the uncertain ones,
and every row gets an evidence-ranked shortlist. Rows a model already read are
never touched.

One caveat, stated rather than hidden: the margin <= 1 threshold was chosen by
looking at the table above, i.e. on the same 768 questions used to report the
result. The mechanism — defer to the second opinion only where the first is
undecided — is principled, but the exact cut is fitted to that sample.

    python3 retag.py caie.db            # apply
    python3 retag.py caie.db --dry-run  # report only
"""
import json, re, sqlite3, sys
from collections import Counter

sys.path.insert(0, __file__.rsplit("/", 1)[0] if "/" in __file__ else ".")
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))          # 项目根目录
from lib import paths
from pipeline.tags import tag_any, topic_model

UNCERTAIN_MARGIN = 1     # keyword margin at or below which we defer


def combined(syl, comp, qtext, mstext, models):
    """(pick, shortlist, keyword_margin, method) for one question."""
    text = re.sub(r"\s+", " ", (qtext or "") + " " + (mstext or "")).lower()
    TOPICS, COMPONENT_TOPICS = tag_any.load(syl)
    codes = COMPONENT_TOPICS.get(str(comp), list(TOPICS))

    kwscore = {c: tag_any.score(text, TOPICS[c][1]) for c in codes}
    ranked = sorted(((kwscore[c], i, c) for i, c in enumerate(codes)),
                    key=lambda x: (-x[0], x[1]))
    kw_margin = ranked[0][0] - (ranked[1][0] if len(ranked) > 1 else 0)
    kw = (tag_any.break_tie(syl, [(s, c) for s, _i, c in ranked])
          if ranked and ranked[0][0] > 0 else None)

    scored = models[syl].score(qtext or "", comp, mstext or "")
    # 9618 tags at section level; the syllabus describes sub-topics
    agg, sub = {}, {}
    for s, c, _hits in scored:
        k = c.split(".")[0] if syl == "9618" else c
        if s > agg.get(k, -1):
            agg[k], sub[k] = s, c
    shortlist = sorted(agg, key=lambda c: -agg[c])[:3]

    if kw is not None and kw_margin > UNCERTAIN_MARGIN:
        return kw, _order(kw, shortlist), kw_margin, "keyword", sub
    if not agg:
        return kw, _order(kw, shortlist), kw_margin, "keyword", sub
    kmax = max(kwscore.values()) or 1
    smax = max(agg.values()) or 1
    pick = max(agg, key=lambda c: agg[c] / smax + kwscore.get(c, 0) / kmax)
    return pick, _order(pick, shortlist), kw_margin, "syllabus+keyword", sub


def _order(pick, shortlist):
    """Shortlist with the chosen topic first, duplicates removed."""
    out = [pick] if pick else []
    for c in shortlist:
        if c not in out:
            out.append(c)
    return out[:3]


def main(db=None, dry=False):
    models = topic_model.load()
    names = {s: {c: t["name"] for c, t in m.topics.items()}
             for s, m in models.items()}
    sec_names = {s: {t["component"]: t["component_name"] for t in m.topics.values()}
                 for s, m in models.items()}

    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    cols = {r[1] for r in con.execute("PRAGMA table_info(questions)")}
    if not dry and "subtopic" not in cols:
        con.execute("ALTER TABLE questions ADD COLUMN subtopic TEXT")
        con.execute("ALTER TABLE questions ADD COLUMN subtopic_name TEXT")

    rows = con.execute(
        "SELECT id, syllabus, component, topic, topic_source, "
        "COALESCE(question_latex, question_text) AS q, "
        "COALESCE(ms_latex, ms_text) AS ms FROM questions").fetchall()

    changed, upd, method_count, moved = 0, [], Counter(), Counter()
    for r in rows:
        syl = r["syllabus"]
        if syl not in models:
            continue
        pick, shortlist, margin, method, submap = combined(
            syl, r["component"], r["q"], r["ms"], models)

        if r["topic_source"] == "model":
            # a model read these questions one by one; nothing here beats that
            method, pick = "model", r["topic"]
            shortlist = _order(pick, shortlist)
        # the finest syllabus code *inside the chosen topic* — for 9618 that is
        # the sub-topic, for the maths syllabuses it is the topic itself
        subtopic = submap.get(pick)
        method_count[method] += 1
        if pick != r["topic"]:
            changed += 1
            moved[f"{syl} P{r['component']}: {r['topic']} -> {pick}"] += 1

        # 9618's topic is a syllabus section, whose name lives on the section
        # heading; the maths syllabuses name the topic directly.
        nm = (sec_names[syl].get(pick) if syl == "9618"
              else names[syl].get(pick)) if pick else None
        # only worth storing where it says something the topic does not
        sub = subtopic if subtopic and subtopic != pick else None
        upd.append((pick, nm, json.dumps(shortlist), margin, method,
                    sub, names[syl].get(sub) if sub else None, r["id"]))

    print(f"{len(rows)} 道题;标签变动 {changed} 道")
    for k, v in method_count.most_common():
        print(f"  {k:<20}{v}")
    print("\n变动最多的方向:")
    for k, v in moved.most_common(12):
        print(f"  {v:>4}  {k}")

    if dry:
        print("\n(--dry-run,未写入)")
        return
    con.executemany(
        "UPDATE questions SET topic=?, topic_name=?, topic_all=?, topic_margin=?, "
        "topic_source=?, subtopic=?, subtopic_name=? WHERE id=?", upd)
    con.execute("DELETE FROM q_fts")
    con.execute("INSERT INTO q_fts(id,question_text,ms_text,topic_name) SELECT id, "
                "COALESCE(question_latex,question_text), COALESCE(ms_latex,ms_text), "
                "topic_name FROM questions")
    con.commit()
    print("\n写回完成。")
    for r in con.execute("SELECT topic_source, COUNT(*) FROM questions GROUP BY 1"):
        print(f"  {r[0]:<20}{r[1]}")
    print(f"  未标注: {con.execute('SELECT COUNT(*) FROM questions WHERE topic IS NULL').fetchone()[0]}")


if __name__ == "__main__":
    a = sys.argv[1:]
    main([x for x in a if not x.startswith("--")][0] if any(
        not x.startswith("--") for x in a) else paths.DB, "--dry-run" in a)
