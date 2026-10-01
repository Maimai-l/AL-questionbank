"""Attempts: one row per time a question is done, in paths.ATTEMPTS (SQLite).

An attempt owns a handwriting board (board id qb-<question id>, then -2, -3
for later attempts), and, once marked, the ticked items of each part and the
score. The bank itself (data/caie.db) is never written by the app.
"""
import json
import os
import sqlite3
import time

from lib import paths

SCHEMA = """
CREATE TABLE IF NOT EXISTS attempts (
    id        INTEGER PRIMARY KEY,
    qid       TEXT NOT NULL,
    n         INTEGER NOT NULL,          -- 1 for the first attempt at qid
    board     TEXT NOT NULL,
    started   REAL NOT NULL,
    marked    REAL,                      -- when it was marked, NULL before
    score     REAL,
    max       REAL,
    marks     TEXT,                      -- JSON {part label: {ticks | score | choice}}
    note      TEXT,
    seconds   REAL,                      -- time spent on the board before marking
    UNIQUE (qid, n)
);
CREATE INDEX IF NOT EXISTS attempts_qid ON attempts (qid);
"""


def connect():
    os.makedirs(os.path.dirname(paths.ATTEMPTS), exist_ok=True)
    con = sqlite3.connect(paths.ATTEMPTS)
    con.row_factory = sqlite3.Row
    con.executescript(SCHEMA)
    cols = {r[1] for r in con.execute("PRAGMA table_info(attempts)")}
    if "seconds" not in cols:                  # stores made before the column existed
        con.execute("ALTER TABLE attempts ADD COLUMN seconds REAL")
    return con


def board_id(qid, n):
    return f"qb-{qid}" + ("" if n == 1 else f"-{n}")


def row(r):
    d = dict(r)
    d["marks"] = json.loads(d["marks"]) if d["marks"] else None
    return d


def for_question(con, qid):
    return [row(r) for r in con.execute(
        "SELECT * FROM attempts WHERE qid=? ORDER BY n", (qid,))]


def current(con, qid):
    """The latest attempt; for a question never attempted, the first one as it
    will be (id None: the row is written when it is marked or restarted)."""
    r = con.execute("SELECT * FROM attempts WHERE qid=? ORDER BY n DESC LIMIT 1",
                    (qid,)).fetchone()
    return row(r) if r else {"id": None, "qid": qid, "n": 1, "board": board_id(qid, 1),
                             "started": None, "marked": None, "score": None, "max": None,
                             "marks": None, "note": None, "seconds": None}


def start(con, qid):
    """A new attempt on a fresh board (the first one if there is none yet)."""
    n = (con.execute("SELECT MAX(n) FROM attempts WHERE qid=?", (qid,)).fetchone()[0] or 0) + 1
    con.execute("INSERT INTO attempts (qid, n, board, started) VALUES (?, ?, ?, ?)",
                (qid, n, board_id(qid, n), time.time()))
    con.commit()
    return current(con, qid)


def mark(con, attempt_id, marks, score, max_, note=None, qid=None, seconds=None):
    if attempt_id is None:                     # the first attempt, never saved
        attempt_id = start(con, qid)["id"]
    con.execute("UPDATE attempts SET marks=?, score=?, max=?, marked=?, note=?, "
                "seconds=COALESCE(?, seconds) WHERE id=?",
                (json.dumps(marks, ensure_ascii=False), score, max_, time.time(), note,
                 seconds, attempt_id))
    con.commit()
    return row(con.execute("SELECT * FROM attempts WHERE id=?", (attempt_id,)).fetchone())


def latest_marked(con):
    """The latest marked attempt of every question, newest first."""
    return [row(r) for r in con.execute(
        "SELECT a.* FROM attempts a JOIN (SELECT qid, MAX(n) AS n FROM attempts "
        "WHERE marked IS NOT NULL GROUP BY qid) l ON a.qid = l.qid AND a.n = l.n "
        "ORDER BY a.marked DESC")]


def history(con, limit=200):
    """Marked attempts, newest first."""
    return [row(r) for r in con.execute(
        "SELECT * FROM attempts WHERE marked IS NOT NULL ORDER BY marked DESC LIMIT ?", (limit,))]


def summary(con):
    """{qid: {attempts, last_score, last_max, marked}} for the question list."""
    out = {}
    for r in con.execute(
            "SELECT qid, COUNT(*) AS attempts, MAX(n) AS n FROM attempts GROUP BY qid"):
        last = con.execute("SELECT score, max, marked FROM attempts WHERE qid=? AND n=?",
                           (r["qid"], r["n"])).fetchone()
        out[r["qid"]] = {"attempts": r["attempts"], "score": last["score"],
                         "max": last["max"], "marked": last["marked"]}
    return out
