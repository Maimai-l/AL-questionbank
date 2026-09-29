#!/usr/bin/env python3
"""The learner-state layer: what has been attempted, and what that implies.

Everything above this file is about the *content* of the bank. This is the
first piece that is about the person using it, and it is what lets a model
teach rather than only fetch: without a record of what was missed, every
session starts from nothing and the best it can do is hand out random
questions.

Two design choices worth stating.

* **Attempts are append-only.** A question graded "bad" in March and "good" in
  June is a different thing from a question that was always "good", and the
  difference is the only evidence of learning in the whole system. Storing one
  mutable grade per question would erase it.
* **Weakness is measured per topic, not per question**, and always alongside
  the topic's prerequisites. "You are weak on 9231 2.3" is not actionable on
  its own; "you are weak on 9231 2.3 and also on 9709 3.4, which it assumes"
  says where to actually go.

    python3 progress.py init
    python3 progress.py import ~/Downloads/caie-记录-2026-08-05.json
    python3 progress.py export out.json
    python3 progress.py weak --syllabus 9709

页面导出的 JSON 形如 {"q": {题号: {...}}, "ch": {章节: {...}}};2026-08 之前
那版只有一层 {题号: {...}},两种都收。
"""
import json, os, sqlite3, sys
from collections import defaultdict

import os, sys
_here = os.path.dirname(os.path.abspath(__file__))
for _p in (_here, os.path.dirname(_here)):      # 放在 attic/ 里也照样找得到 lib/
    if os.path.isdir(os.path.join(_p, "lib")) and _p not in sys.path:
        sys.path.insert(0, _p)
from lib import paths
GRADES = ("good", "ok", "bad")
# a "bad" costs more than a "good" earns: one clean solve after a miss is not
# yet mastery, and the point of the score is to surface what still needs work
WEIGHT = {"good": 1.0, "ok": 0.5, "bad": 0.0}
RECENCY = 0.6            # each older attempt on the same question counts less

SCHEMA = """
CREATE TABLE IF NOT EXISTS attempts (
  id          INTEGER PRIMARY KEY,
  question_id TEXT NOT NULL,
  grade       TEXT NOT NULL CHECK (grade IN ('good','ok','bad')),
  at          TEXT NOT NULL,
  seconds     INTEGER,
  note        TEXT,
  source      TEXT
);
CREATE INDEX IF NOT EXISTS attempts_q  ON attempts(question_id);
CREATE INDEX IF NOT EXISTS attempts_at ON attempts(at);
CREATE UNIQUE INDEX IF NOT EXISTS attempts_dedup
  ON attempts(question_id, at, grade, IFNULL(source,''));

-- 教材侧的状态。章节没有"做对/做错",只有读到哪了,所以不进 attempts。
CREATE TABLE IF NOT EXISTS chapter_status (
  chapter_id TEXT PRIMARY KEY,
  status     TEXT NOT NULL CHECK (status IN ('reading','done')),
  at         TEXT
);
"""


def init(db):
    con = sqlite3.connect(db)
    con.executescript(SCHEMA)
    con.commit()
    return con


def add(con, question_id, grade, at, seconds=None, note=None, source="mcp"):
    if grade not in GRADES:
        raise ValueError(f"grade must be one of {GRADES}")
    con.execute("INSERT OR IGNORE INTO attempts"
                "(question_id, grade, at, seconds, note, source) VALUES (?,?,?,?,?,?)",
                (question_id, grade, at, seconds, note, source))
    con.commit()


# ------------------------------------------------------------------ scoring

def topic_scores(con, syllabus=None, component=None):
    """Per topic: attempts, a 0-1 mastery score, and the questions still missed.

    Newer attempts on the same question dominate older ones, so a topic that
    was failed and then relearned climbs instead of being held down forever.
    """
    q = """SELECT a.question_id, a.grade, a.at, q.syllabus, q.component,
                  q.topic, q.topic_name, q.subtopic, q.subtopic_name
           FROM attempts a JOIN questions q ON q.id = a.question_id
           WHERE q.topic IS NOT NULL"""
    args = []
    if syllabus:
        q += " AND q.syllabus = ?"; args.append(str(syllabus))
    if component:
        q += " AND q.component = ?"; args.append(str(component))
    q += " ORDER BY a.at DESC, a.id DESC"

    per_q = defaultdict(list)
    meta = {}
    for r in con.execute(q, args):
        per_q[r[0]].append(r[1])
        meta[r[0]] = r[3:]

    topics = defaultdict(lambda: {"questions": 0, "attempts": 0, "num": 0.0,
                                  "den": 0.0, "weak_ids": [], "last": None})
    for qid, grades in per_q.items():
        syl, comp, topic, tname, sub, subname = meta[qid]
        key = (syl, topic)
        t = topics[key]
        t["syllabus"], t["component"], t["topic"], t["topic_name"] = syl, comp, topic, tname
        t["questions"] += 1
        t["attempts"] += len(grades)
        w = 1.0
        for g in grades:                       # newest first
            t["num"] += WEIGHT[g] * w
            t["den"] += w
            w *= RECENCY
        if grades[0] != "good":
            t["weak_ids"].append(qid)

    out = []
    for (syl, topic), t in topics.items():
        t["score"] = round(t["num"] / t["den"], 3) if t["den"] else None
        t.pop("num"); t.pop("den")
        t["weak_ids"] = t["weak_ids"][:8]
        out.append(t)
    out.sort(key=lambda t: (t["score"], -t["questions"]))
    return out


def load_prereq(path=None):
    p = path or paths.PREREQ
    if not os.path.exists(p):
        return {"components": {}, "topic_prerequisites": [], "topic_related": []}
    return json.load(open(p))


def upstream(pre, syllabus, topic):
    """Topics this one assumes, as 'syllabus:code' strings."""
    key = f"{syllabus}:{topic}"
    return [e["from"] for e in pre["topic_prerequisites"] if e["to"] == key]


def weak_report(con, syllabus=None, component=None, limit=10, pre=None):
    pre = pre or load_prereq()
    scores = {(t["syllabus"], t["topic"]): t
              for t in topic_scores(con)}
    rows = topic_scores(con, syllabus, component)
    out = []
    for t in rows[:limit]:
        ups = []
        for u in upstream(pre, t["syllabus"], t["topic"]):
            us, uc = u.split(":")
            s = scores.get((us, uc))
            ups.append({"topic": u,
                        "score": s["score"] if s else None,
                        "name": s["topic_name"] if s else None,
                        "attempted": bool(s)})
        t = dict(t)
        t["prerequisites"] = ups
        # the useful distinction: is the gap here, or upstream?
        weak_up = [u for u in ups if u["score"] is not None and u["score"] < 0.6]
        t["diagnosis"] = ("先补先修:" + ", ".join(u["topic"] for u in weak_up)
                          if weak_up else
                          "先修没做过,无法判断" if ups and not any(u["attempted"] for u in ups)
                          else "问题就在这个主题本身")
        out.append(t)
    return out


# ------------------------------------------------------------------- CLI

def cmd_import(db, path, source="web"):
    """Import the JSON the offline page exports.

    That file is a snapshot — one grade per question — so it carries a single
    attempt each. Re-importing the same file adds nothing, because
    (question, date, grade, source) is unique.
    """
    con = init(db)
    data = json.load(open(path))
    # 新版:{"q": {...}, "ch": {...}};旧版:{题号: {...}}
    qrec = data.get("q") if isinstance(data.get("q"), dict) else None
    chrec = data.get("ch") if isinstance(data.get("ch"), dict) else {}
    if qrec is None:
        qrec = {k: v for k, v in data.items() if not k.startswith("chapter:")}
        chrec = {k[8:]: v for k, v in data.items() if k.startswith("chapter:")}

    known = {r[0] for r in con.execute("SELECT id FROM questions")}
    n, skipped = 0, 0
    for qid, rec in qrec.items():
        if qid not in known:
            skipped += 1
            continue
        g = (rec or {}).get("g")
        if g not in GRADES:
            continue
        con.execute("INSERT OR IGNORE INTO attempts"
                    "(question_id,grade,at,source) VALUES (?,?,?,?)",
                    (qid, g, rec.get("at") or "1970-01-01", source))
        n += 1

    chn = 0
    for cid, rec in (chrec or {}).items():
        st = (rec or {}).get("g")
        if st not in ("reading", "done"):
            continue
        con.execute("INSERT INTO chapter_status(chapter_id,status,at) VALUES (?,?,?) "
                    "ON CONFLICT(chapter_id) DO UPDATE SET status=excluded.status, "
                    "at=excluded.at",
                    (cid, st, rec.get("at")))
        chn += 1
    con.commit()

    total = con.execute("SELECT COUNT(*) FROM attempts").fetchone()[0]
    msg = f"导入 {n} 条做题记录;库里现有 {total} 次作答"
    if chn:
        msg += f";{chn} 章学习状态"
    if skipped:
        msg += f";{skipped} 条对应不上题号,已跳过"
    print(msg)


def cmd_export(db, path):
    """Write the page's own format back out, so a wiped browser can be refilled."""
    con = init(db)
    q = {}
    for qid, g, at in con.execute(
            "SELECT question_id, grade, at FROM attempts ORDER BY at, id"):
        q[qid] = {"g": g, "at": at, "n": q.get(qid, {}).get("n", 0) + 1}
    ch = {}
    try:
        for cid, st, at in con.execute(
                "SELECT chapter_id, status, at FROM chapter_status"):
            ch[cid] = {"g": st, "at": at}
    except sqlite3.OperationalError:
        pass
    json.dump({"q": q, "ch": ch}, open(path, "w"), ensure_ascii=False, indent=1)
    print(f"{len(q)} 道题 + {len(ch)} 章 -> {path}(可直接在页面「记录」里导入)")


def cmd_weak(db, syllabus=None):
    con = init(db)
    rows = weak_report(con, syllabus, limit=15)
    if not rows:
        print("还没有作答记录。先在 data/practice.html 里刷几题,"
              "在「记录」页导出 JSON,再 `python3 progress.py import <文件>`")
        return
    print(f"{'主题':<34}{'掌握':>7}{'题数':>6}{'作答':>6}  诊断")
    for t in rows:
        print(f"{t['syllabus']+' '+t['topic']+' '+(t['topic_name'] or ''):<34}"
              f"{t['score']:>7.2f}{t['questions']:>6}{t['attempts']:>6}  {t['diagnosis']}")


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        sys.exit(__doc__)
    cmd, rest = a[0], [x for x in a[1:] if not x.startswith("--")]
    # 第一个位置参数若是 .db 文件就当数据库,否则用默认库
    db = paths.DB
    if rest and rest[0].endswith(".db"):
        db, rest = rest[0], rest[1:]
    if cmd == "init":
        init(db); print(f"{db}: attempts 表就绪")
    elif cmd == "import":
        if not rest:
            sys.exit("用法: progress.py import <页面导出的.json>")
        cmd_import(db, rest[0])
    elif cmd == "export":
        cmd_export(db, rest[0] if rest else "progress.json")
    elif cmd == "weak":
        syl = None
        if "--syllabus" in a:
            syl = a[a.index("--syllabus") + 1]
        cmd_weak(db, syl)
    else:
        sys.exit(__doc__)
