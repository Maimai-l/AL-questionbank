#!/usr/bin/env python3
"""Assemble a question bank into a single SQLite file with full-text search.

  build_db.py <subject> <questions.json> <ms.json> <out.db>
"""
import importlib, json, os, sqlite3, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))          # 项目根目录

MONTH = {"m": ("March", 3), "s": ("June", 6), "w": ("November", 11)}

SCHEMA = """
DROP TABLE IF EXISTS questions;
CREATE TABLE questions (
  id            TEXT PRIMARY KEY,
  syllabus      TEXT NOT NULL,
  component     TEXT NOT NULL,   -- 1 / 2 / 3 / 4 / 5 / 6
  component_name TEXT NOT NULL,
  paper         TEXT NOT NULL,   -- e.g. 9709/12
  variant       TEXT NOT NULL,
  year          INTEGER NOT NULL,
  month         INTEGER NOT NULL,
  session       TEXT NOT NULL,   -- e.g. "June 2023"
  series        TEXT NOT NULL,   -- e.g. s23
  q             INTEGER NOT NULL,
  parts         TEXT,            -- JSON list, e.g. ["3(a)","3(b)"]
  marks         INTEGER,
  marks_parts   TEXT,            -- JSON list of per-part tariffs
  topic         TEXT,
  topic_name    TEXT,
  topic_all     TEXT,            -- JSON list, ranked
  topic_confident INTEGER,
  topic_margin  INTEGER,        -- keyword score gap; 0 = exact tie, tag arbitrary; NULL when model-tagged
  topic_source  TEXT,           -- 'model' = a model read the question; 'keyword' = scored guess
  topic_note    TEXT,           -- model's one-phrase reason, when topic_source='model'
  question_text TEXT,            -- lossy: superscripts/fractions flattened
  ms_text       TEXT,            -- mark scheme, layout preserved
  mark_codes    TEXT,            -- JSON list, e.g. ["B1","M1","A1","OE"]
  ms_total      INTEGER,
  totals_agree  INTEGER,         -- tariff == mark scheme total (extraction check)
  image         TEXT,            -- img9709/<file>.png  loss-free crop
  qp_pdf        TEXT,
  ms_pdf        TEXT,
  qp_pages      TEXT             -- JSON list of 0-based page indices
);
CREATE INDEX idx_topic     ON questions(component, topic);
CREATE INDEX idx_marks     ON questions(marks);
CREATE INDEX idx_year      ON questions(year, month);
CREATE INDEX idx_paper     ON questions(paper);
"""

FTS = """
DROP TABLE IF EXISTS q_fts;
CREATE VIRTUAL TABLE q_fts USING fts5(
  id UNINDEXED, question_text, ms_text, topic_name, tokenize='porter unicode61');
"""

NAMES_9709 = {"1": "Pure Mathematics 1", "2": "Pure Mathematics 2", "3": "Pure Mathematics 3",
              "4": "Mechanics", "5": "Probability & Statistics 1",
              "6": "Probability & Statistics 2"}


def component_names(subject):
    if subject == "9709":
        return NAMES_9709
    return importlib.import_module(f"pipeline.tags.topics_{subject}").COMPONENT_NAME


def main(subject, qjson, msjson, dbpath, imgdir=None):
    imgdir = imgdir or f"img{subject}"
    COMPONENT_NAME = component_names(subject)
    Q = json.load(open(qjson))
    M = json.load(open(msjson))
    mk = {(m["series"], m["component"], m["variant"], m["q"]): m for m in M}

    con = sqlite3.connect(dbpath)
    con.executescript(SCHEMA)
    con.executescript(FTS)

    rows, fts = [], []
    for q in Q:
        s = q["series"]
        mon, mnum = MONTH[s[0]]
        year = 2000 + int(s[1:])
        m = mk.get((s, q["component"], q["variant"], q["q"]))
        qid = f"{subject}_{s}_{q['component']}{q['variant']}_q{q['q']:02d}"
        ms_total = m["ms_total"] if m else None
        agree = None
        if q["marks"] and ms_total:
            agree = int(q["marks"] == ms_total)
        rows.append((
            qid, subject, q["component"], COMPONENT_NAME[q["component"]],
            q["paper"], q["variant"], year, mnum, f"{mon} {year}", s, q["q"],
            json.dumps(m["parts"]) if m else "[]",
            q["marks"], json.dumps(q["marks_parts"]),
            q["topic"], q["topic_name"], json.dumps(q["topics_all"]),
            int(bool(q["topic_confident"])), q.get("topic_margin"),
            q.get("topic_source", "keyword"), q.get("topic_note"),
            q["text"], m["ms_text"] if m else None,
            json.dumps(m["mark_codes"]) if m else "[]",
            ms_total, agree,
            f"{imgdir}/{q['image']}" if q.get("image") else None,
            q["source"], m["source"] if m else None,
            json.dumps(sorted({sp["page"] for sp in q["spans"]})),
        ))
        fts.append((qid, q["text"], (m["ms_text"] if m else "") or "",
                    q["topic_name"] or ""))

    con.executemany(f"INSERT INTO questions VALUES ({','.join('?'*30)})", rows)
    con.executemany("INSERT INTO q_fts VALUES (?,?,?,?)", fts)
    con.commit()

    n = con.execute("SELECT COUNT(*) FROM questions").fetchone()[0]
    withms = con.execute("SELECT COUNT(*) FROM questions WHERE ms_text IS NOT NULL").fetchone()[0]
    withimg = con.execute("SELECT COUNT(*) FROM questions WHERE image IS NOT NULL").fetchone()[0]
    print(f"{n} questions | {withms} with mark scheme | {withimg} with image")
    for r in con.execute("SELECT component_name, COUNT(*), SUM(marks) FROM questions GROUP BY component ORDER BY component"):
        print(f"  {r[0]:<28} {r[1]:>4} questions  {r[2]:>6} marks")
    con.close()


if __name__ == "__main__":
    main(*sys.argv[1:6])
