#!/usr/bin/env python3
"""Syllabus sections for 9702 Physics questions.

    python3 pipeline/tags/physics_topics.py [--write]

topic_model.py scores a question against the syllabus outcomes alone. For physics
that is a few lines per subsection, and common words ("density", "charge") occur in
several sections: on 100 hand-checked questions it put 70 in the right section.
Here each section is described by its coursebook chapter (data/books/9702, mapped
to the sections by pipeline/books/chapters.py) together with its syllabus text,
and a question is placed by TF-IDF cosine similarity with those descriptions plus
the section terms of terms_9702.py. On the same 100 questions this places 88
(85% on the 40 that were not used to choose the terms). The subsection is then the
best syllabus-model match inside the chosen section.

Paper 1 and 2 questions compete among sections 1-11, paper 4 among 12-25 and paper
5 among 2-25: a planning question always talks about uncertainty and measurement,
so section 1 would win every time. Paper 1 is scored on the question alone (its
scheme is a letter). Rows whose topic_source is 'model' are left alone.

The 2021 papers were set on the 2019-2021 syllabus, whose A Level part still had
communication (amplitude modulation, analogue and digital transmission) and
electronics (the operational amplifier). Those 14 paper 4 questions have no
section in the current syllabus: their topic is left empty, with a topic_note.
"""
import argparse, collections, json, math, os, re, sqlite3, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))
from lib import paths  # noqa: E402
from pipeline.tags import topic_model  # noqa: E402
from pipeline.tags.terms_9702 import TERMS  # noqa: E402

SECTIONS = {"1": [str(i) for i in range(1, 12)], "2": [str(i) for i in range(1, 12)],
            "4": [str(i) for i in range(12, 26)], "5": [str(i) for i in range(2, 26)]}
TERM_WEIGHT = 0.15          # chosen on the first 60 hand-checked questions
OLD_SYLLABUS = re.compile(r"operational amplifier|op-amp|modulat|analogue signal", re.I)
OLD_NOTE = "2019–2021 考纲的通信或电子学内容，现行考纲(2022 年起)已删除"
STOP = set("the a an of to and in is are be by for on at as with that this which what from "
           "it its or not their they was were has have will can each than then when where how "
           "into these there also any all two one more most such may must".split())


def tokens(text):
    w = [x for x in re.findall(r"[a-z][a-z\-]+", (text or "").lower())
         if x not in STOP and len(x) > 2]
    return w + [a + " " + b for a, b in zip(w, w[1:])]


def term_scores(text):
    t = " " + (text or "").lower() + " "
    return {s: sum(w * sum(p in t for p in lst) for w, lst in d.items())
            for s, d in TERMS.items()}


class Classifier:
    def __init__(self, con=None):
        con = con or sqlite3.connect(paths.DB)
        spec = json.load(open(paths.SYLLABUS, encoding="utf-8"))["9702"]
        self.model = topic_model.load()["9702"]
        self.sec_name = {t["component"]: t["component_name"] for t in spec["topics"].values()}
        self.sub_name = {c: t["name"] for c, t in spec["topics"].items()}
        docs = collections.defaultdict(collections.Counter)
        for topic, path in con.execute("SELECT topic, path FROM chapters "
                                       "WHERE syllabus = '9702' AND topic IS NOT NULL"):
            docs[topic].update(tokens(open(os.path.join(paths.DATA, path), encoding="utf-8").read()))
        if not docs:
            sys.exit("chapters 表里没有 9702 教材章节(pipeline/books/chapters.py index)")
        for code, t in spec["topics"].items():      # the syllabus wording counts five times
            for k, v in collections.Counter(tokens(" . ".join(
                    [t["name"]] * 3 + t["outcomes"] + t["notes"]))).items():
                docs[code.split(".")[0]][k] += 5 * v
        self.n = len(docs)
        self.df = collections.Counter()
        for d in docs.values():
            self.df.update(set(d))
        self.vec = {s: self._unit(d) for s, d in docs.items()}

    def _unit(self, counts):
        w = {k: (1 + math.log(v)) * math.log(self.n / self.df[k])
             for k, v in counts.items() if 0 < self.df.get(k, 0) < self.n}
        norm = math.sqrt(sum(x * x for x in w.values())) or 1.0
        return {k: x / norm for k, x in w.items()}

    def classify(self, text, ms, component, year=None):
        comp = str(component)
        if year and int(year) <= 2021 and comp == "4" and OLD_SYLLABUS.search(text):
            return {"topic": None, "topic_name": None, "topics_all": [], "topic_margin": None,
                    "subtopic": None, "subtopic_name": None, "topic_note": OLD_NOTE}
        body = text + " " + (ms or "" if comp != "1" else "")
        q, terms = self._unit(collections.Counter(tokens(body))), term_scores(body)
        ranked = sorted(((sum(x * self.vec[s].get(k, 0) for k, x in q.items())
                          + TERM_WEIGHT * terms.get(s, 0), s)
                         for s in SECTIONS.get(comp, SECTIONS["5"]) if s in self.vec), reverse=True)
        sec = ranked[0][1]
        subs = [c for _s, c, _h in self.model.score(text, comp, ms if comp != "1" else "")
                if c.split(".")[0] == sec]
        sub = subs[0] if subs else None
        return {"topic": sec, "topic_name": self.sec_name.get(sec),
                "topics_all": [s for _x, s in ranked[:3]],
                "topic_margin": round(ranked[0][0] - ranked[1][0], 4) if len(ranked) > 1 else None,
                "subtopic": sub, "subtopic_name": self.sub_name.get(sub), "topic_note": None}


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    con = sqlite3.connect(paths.DB)
    clf = Classifier(con)
    rows = con.execute("SELECT id, component, question_text, ms_text, topic, year FROM questions "
                       "WHERE syllabus = '9702' AND COALESCE(topic_source, '') != 'model'").fetchall()
    upd, moved = [], 0
    for qid, comp, text, ms, old, year in rows:
        r = clf.classify(text or "", ms, comp, year)
        moved += r["topic"] != old
        upd.append((r["topic"], r["topic_name"], json.dumps(r["topics_all"]), r["topic_margin"],
                    r["subtopic"], r["subtopic_name"], r["topic_note"], qid))
    print(f"9702 {len(rows)} 题;节变动 {moved} 题;旧考纲内容 {sum(1 for u in upd if u[6])} 题")
    if not a.write:
        print("(dry run;加 --write 写入)")
        return
    con.executemany("UPDATE questions SET topic=?, topic_name=?, topic_all=?, topic_margin=?, "
                    "topic_source='syllabus', subtopic=?, subtopic_name=?, topic_note=? WHERE id=?", upd)
    con.executemany("UPDATE q_fts SET topic_name=? WHERE id=?", [(u[1], u[-1]) for u in upd])
    con.commit()
    print("已写入")


if __name__ == "__main__":
    main()
