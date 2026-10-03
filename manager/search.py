"""The search page (docs/data-manager.md, 搜索): a full-text index of every exam's questions
with its own columns, kept in paths.WORK/search.db and rebuilt when the bank changes.

Columns: stem (the question text), ms (the mark scheme), both as LaTeX where there is some, ex (the
explanation, its text flattened) and topic (the topic name). Words are stored as they are,
not stemmed: porter makes integration, integral and integrity one word. A typed word finds
the words that begin with it and its other forms: the words of the same stem that share a
letter past it (integrate, integration, integrated; words table).

What the search box takes (and the four keyword fields on the left write):
    integration parts        every word, as a word or the start of one
    "integration by parts"   the phrase
    parts OR substitution    either
    -substitution            not this word
    9709/32/M/J/23 Q5, s23 32 q5   that paper or question, whatever else is chosen
"""
import json
import os
import re
import sqlite3
import threading

from lib import paths
from manager import bank

INDEX = os.path.join(paths.WORK, "search.db")
VERSION = 3                              # part of the stamp: raise when the index changes
COLS = ["stem", "ms", "ex", "topic"]
_lock = threading.Lock()
_ready = None                            # the stamp of the index this process checked


# ------------------------------------------------------------------ the index

def _explanation(raw):
    """An explanation's text for the index: every part's approach, points, pitfalls and answer."""
    try:
        parts = json.loads(raw).get("parts", []) if raw else []
    except (ValueError, AttributeError):
        return ""
    out = []
    for p in parts:
        out += [p.get("label") or "", p.get("approach") or ""]
        for pt in p.get("points") or []:
            out += [pt.get("point") or "", pt.get("why") or ""]
        out += list(p.get("pitfalls") or []) + [p.get("answer") or ""]
    return "\n".join(x for x in out if x)


def _stamp():
    return f"{VERSION}:{os.path.getmtime(paths.DB)}"


def _build(path):
    src = sqlite3.connect(paths.DB)
    src.row_factory = sqlite3.Row
    con = sqlite3.connect(path)
    con.executescript("""
        CREATE VIRTUAL TABLE f USING fts5(stem, ms, ex, topic, tokenize='unicode61');
        CREATE TABLE docs(rowid INTEGER PRIMARY KEY, id TEXT, exam TEXT, code TEXT, component TEXT, paper TEXT,
                          year INT, month INT, q INT, marks INT, topic TEXT, topic_name TEXT, tasks TEXT, expl INT);
        CREATE TABLE words(w TEXT PRIMARY KEY, st TEXT);
        CREATE TABLE meta(stamp TEXT);
    """)
    text = {r["id"]: r for r in src.execute(
        "SELECT id, COALESCE(NULLIF(question_latex, ''), question_text) AS stem, "
        "COALESCE(NULLIF(ms_latex, ''), ms_text) AS ms_text, explanation, topic_name FROM questions")}
    n = 0
    for exam, _ in bank.EXAMS:
        for r in bank.rows(exam):
            t = text[r["id"]]
            n += 1
            con.execute("INSERT INTO docs VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        (n, r["id"], exam, r["code"], str(r["component"]), r["paper"], r["year"], r["month"], r["q"],
                         r["marks"], r["topic"] or "", t["topic_name"] or "", json.dumps(r["tasks"]), int(r["explanation"])))
            con.execute("INSERT INTO f(rowid, stem, ms, ex, topic) VALUES (?,?,?,?,?)",
                        (n, t["stem"] or "", t["ms_text"] or "", _explanation(t["explanation"]), t["topic_name"] or ""))
    # every word with its porter stem: the forms of a typed word (words)
    con.executescript("""
        CREATE VIRTUAL TABLE pv USING fts5vocab(f, 'row');
        CREATE VIRTUAL TABLE s USING fts5(t, tokenize='porter unicode61');
        CREATE VIRTUAL TABLE sv USING fts5vocab(s, 'instance');
    """)
    words = [r[0] for r in con.execute("SELECT term FROM pv")]
    con.executemany("INSERT INTO s(rowid, t) VALUES (?, ?)", enumerate(words))
    stems = dict(con.execute("SELECT doc, term FROM sv"))
    con.executemany("INSERT INTO words VALUES (?, ?)", ((w, stems.get(i, w)) for i, w in enumerate(words)))
    con.executescript("DROP TABLE sv; DROP TABLE s; DROP TABLE pv;")
    con.execute("CREATE INDEX words_st ON words(st)")
    con.execute("INSERT INTO meta VALUES (?)", (_stamp(),))
    con.commit()
    con.execute("VACUUM")
    con.close()


def connect():
    """The index, built first when it is missing or older than the bank."""
    global _ready
    with _lock:
        stamp = _stamp()
        if _ready != stamp:
            try:
                with sqlite3.connect(INDEX) as c:
                    ok = c.execute("SELECT stamp FROM meta").fetchone()[0] == stamp
            except sqlite3.Error:
                ok = False
            if not ok:
                os.makedirs(paths.WORK, exist_ok=True)
                tmp = f"{INDEX}.{os.getpid()}.tmp"
                if os.path.exists(tmp):
                    os.remove(tmp)
                _build(tmp)
                os.replace(tmp, INDEX)
            _ready = stamp
    con = sqlite3.connect(INDEX)
    con.row_factory = sqlite3.Row
    return con


# ------------------------------------------------------------------ the query

CODE = [
    (re.compile(r"^([msw])\s?(\d{2})\s+(\d{2})(?:\s+q?(\d{1,2}))?$"), {"m": 3, "s": 6, "w": 11}),
    (re.compile(r"^(\d{4})/(\d{2})/(f/m|m/j|o/n)/(\d{2})(?:\s+q?(\d{1,2}))?$"), {"f/m": 3, "m/j": 6, "o/n": 11}),
]


def paper_code(text):
    """(exam or None, month, yy, paper, q or None) for "s23 12 q5" or "9709/12/M/J/23 Q5", else None."""
    s = re.sub(r"\s+", " ", text.lower()).strip()
    m = CODE[0][0].match(s)
    if m:
        return None, CODE[0][1][m[1]], int(m[2]), m[3], int(m[4]) if m[4] else None
    m = CODE[1][0].match(s)
    if m:
        return m[1], CODE[1][1][m[3]], int(m[4]), m[2], int(m[5]) if m[5] else None
    return None


def tokens(text):
    """The box's text as [(kind, words)], kind one of word, phrase, or, not."""
    out = []
    for phrase, word in re.findall(r'"([^"]*)"?|(\S+)', text):
        if phrase:
            words = re.findall(r"\w+", phrase)
            if words:
                out.append(("phrase", words))
        elif word == "OR":
            out.append(("or", []))
        elif word.startswith("-") and len(word) > 1:
            words = re.findall(r"\w+", word[1:])
            if words:
                out.append(("not", words))
        else:
            words = re.findall(r"\w+", word)
            if words:
                out.append(("word", words))
    return out


ENDINGS = {"", "s", "es", "e", "ed", "d", "ing", "er", "ers", "ly"}


def forms(con, w):
    """Other forms of a whole typed word: the words of its stem that share at least one letter
    past the stem (integration: integrate, integrated; integrity shares only integr), or
    that are the same base with another ending (vectors: vector; solve: solving). A
    beginning (integrat) needs none: its prefix finds every word it begins."""
    row = con.execute("SELECT st FROM words WHERE w = ?", (w,)).fetchone()
    if not row:
        return []
    st = row[0]
    lcp = lambda a, b: next((i for i, (x, y) in enumerate(zip(a, b)) if x != y), min(len(a), len(b)))
    def form(v):
        n = lcp(v, w)
        # past the stem (integrate, integration), or the same base with another ending
        # (vectors, vector; sorted, sorting; solve, solving)
        return not v.startswith(w) and (n > len(st) or (w[n:] in ENDINGS and v[n:] in ENDINGS))
    return sorted(v for (v,) in con.execute("SELECT w FROM words WHERE st = ?", (st,)) if form(v))[:20]


def _word(con, words):
    """One typed word (or the parts of x-axis in a row) as an FTS5 term."""
    if len(words) > 1:
        return '"' + " ".join(words) + '"*'
    w = words[0].lower()
    extra = forms(con, w) if len(w) >= 4 else []
    return "(" + " OR ".join([f'"{w}"*'] + [f'"{x}"' for x in extra]) + ")" if extra else f'"{w}"*'


def fts(con, text):
    """(positive expression or None, negative expression or None) for FTS5. Words joined by
    OR form one group; groups are all required: a b OR c is a AND (b OR c)."""
    groups, neg, join = [], [], False
    for kind, words in tokens(text):
        if kind == "or":
            join = bool(groups)
            continue
        if kind == "not":
            neg.append(_word(con, words))
            continue
        term = '"' + " ".join(words) + '"' if kind == "phrase" else _word(con, words)
        if join:
            groups[-1].append(term)
        else:
            groups.append([term])
        join = False
    pos = " AND ".join(g[0] if len(g) == 1 else "(" + " OR ".join(g) + ")" for g in groups)
    return (pos or None), (" OR ".join(neg) or None)


def terms(con, text):
    """What the page marks in the question it shows: regular expressions, one per word or phrase."""
    out = []
    for kind, words in tokens(text):
        if kind in ("or", "not"):
            continue
        if kind == "phrase":
            out.append(r"\b" + r"\s+".join(re.escape(w) for w in words) + r"\b")
        elif len(words) == 1:
            w = words[0].lower()
            alts = [re.escape(w) + r"\w*"] + [re.escape(x) + r"\b" for x in (forms(con, w) if len(w) >= 4 else [])]
            out.append(r"\b(?:" + "|".join(alts) + ")")
        else:
            out.append(r"\b" + r"\W".join(re.escape(x) for x in words) + r"\w*")
    return out


def _snippet(text, width=90):
    """The text around its marked matches (\x01..\x02), on one line: the stretch that holds the
    most different terms, whole formulas and words kept."""
    if "\x01" not in text:
        return None
    text = re.sub(r"\s*\|\s*", " · ", re.sub(r"[ \t]*\n\s*", " · ", text.strip()))
    # a term by its first five letters: integral and integration are one term, by parts another
    spans = [(m.start(), m.end(), m[1].lower()[:5]) for m in re.finditer("\x01(.*?)\x02", text, re.S)]
    best, anchor = (0, 0), spans[0][0]
    for a in spans:                          # from each match: most distinct terms, then the shortest stretch
        seen, reach = set(), a[1]
        for s, e, t in spans:
            if a[0] <= s and e <= a[0] + 2 * width and t not in seen:
                seen.add(t)
                reach = e
        if (len(seen), a[0] - reach) > best:
            best, anchor = (len(seen), a[0] - reach), a[0]
    start, end = max(0, anchor - width // 3), min(len(text), anchor + 2 * width)
    dollars = lambda a, b: len(re.findall(r"(?<!\\)\$", text[a:b]))
    if dollars(0, start) % 2:                # starts inside a formula: from its beginning
        start = text.rfind("$", 0, start)
    if dollars(start, end) % 2:              # ends inside one: to its end
        nxt = text.find("$", end)
        end = nxt + 1 if nxt >= 0 else len(text)
    if text.count("\x01", start, end) > text.count("\x02", start, end):
        end = text.find("\x02", end) + 1    # a match cut at the end
    while start > 0 and text[start - 1].isalnum() and text[start] != "$":
        start -= 1                           # not in the middle of a word
    while end < len(text) and text[end - 1].isalnum() and text[end].isalnum():
        end += 1
    return ("…" if start > 0 else "") + text[start:end].strip(" ·") + ("…" if end < len(text) else "")


def find(p, limit=200):
    """The page's search: p = {q, exams, topics ["9709:3.5"], from, to, mmin, mmax, cols,
    comps, tasks, expl ("any" | "y" | "n"), sort ("rel" | "year")}. Returns the count and
    the matches per exam (whatever exams are chosen) and per paper (whatever papers are
    chosen), the tasks of the matches, the first `limit` rows with their snippets, and the terms to mark."""
    con = connect()
    text = (p.get("q") or "").strip()
    code = paper_code(text)
    where, args = [], []
    if code:                                 # a paper or a question, as on the query page
        exam, month, yy, paper, q = code
        where += ["d.month = ?", "d.year % 100 = ?", "d.paper = ?"]
        args += [month, yy, paper]
        if exam:
            where.append("d.exam = ?")
            args.append(exam)
        if q:
            where.append("d.q = ?")
            args.append(q)
        pos = neg = None
    else:
        pos, neg = fts(con, text)
        if not pos and not neg:
            return {"total": 0, "counts": {}, "papers": {}, "tasks": {}, "rows": [], "terms": []}
        cols = [c for c in p.get("cols") or COLS if c in COLS] or COLS
        scope = (lambda e: e) if len(cols) == len(COLS) else (lambda e: "{" + " ".join(cols) + "} : (" + e + ")")
        if pos:
            where.append("f MATCH ?")
            args.append(scope(f"({pos}) NOT ({neg})" if neg else pos))
        else:                                # only words to leave out
            where.append("d.rowid NOT IN (SELECT rowid FROM f WHERE f MATCH ?)")
            args.append(scope(neg))
        for key, col, op in (("from", "year", ">="), ("to", "year", "<="), ("mmin", "marks", ">="), ("mmax", "marks", "<=")):
            if str(p.get(key, "")).strip():
                where.append(f"d.{col} {op} ?")
                args.append(float(p[key]))
        if p.get("expl") in ("y", "n"):
            where.append("d.expl = ?")
            args.append(int(p["expl"] == "y"))
    rank = "bm25(f, 4.0, 2.0, 1.0, 1.0)" if pos else "0"
    sql = (f"SELECT d.*, {rank} AS score FROM {'f JOIN docs d ON d.rowid = f.rowid' if pos else 'docs d'} "
           f"WHERE {' AND '.join(where) or '1'}")
    rows = [dict(r) for r in con.execute(sql, args)]
    for r in rows:
        r["tasks"] = json.loads(r["tasks"])
    if not code and p.get("topics"):         # a topic narrows its own exam only
        chosen = set(p["topics"])
        narrowed = {t.split(":")[0] for t in chosen}
        rows = [r for r in rows if r["exam"] not in narrowed or f'{r["exam"]}:{r["topic"]}' in chosen]
    task_counts = {}
    for r in rows:
        for t in r["tasks"]:
            task_counts[t] = task_counts.get(t, 0) + 1
    if not code and p.get("tasks") is not None:
        want = set(p["tasks"])
        rows = [r for r in rows if not r["tasks"] or want & set(r["tasks"])]
    counts = {}
    for r in rows:
        counts[r["exam"]] = counts.get(r["exam"], 0) + 1
    if (not code or not code[0]) and p.get("exams") is not None:
        rows = [r for r in rows if r["exam"] in p["exams"]]
    papers = {}                              # matches per paper, whatever papers are chosen
    for r in rows:
        papers[r["component"]] = papers.get(r["component"], 0) + 1
    if not code and p.get("comps") is not None:
        want = {str(c) for c in p["comps"]}
        rows = [r for r in rows if r["component"] in want]
    if p.get("sort") == "year":
        rows.sort(key=lambda r: (-r["year"], -r["month"], r["code"], r["q"]))
    else:
        rows.sort(key=lambda r: (r["score"], -r["year"], r["code"], r["q"]))
    page = rows[:limit]
    snips = {}
    if pos and page:
        expr = args[where.index("f MATCH ?")] if "f MATCH ?" in where else None
        ids = [r["rowid"] for r in page]
        for h in con.execute(
                f"SELECT rowid, highlight(f, 0, char(1), char(2)), highlight(f, 1, char(1), char(2)), "
                f"highlight(f, 2, char(1), char(2)), highlight(f, 3, char(1), char(2)) FROM f "
                f"WHERE f MATCH ? AND rowid IN ({','.join('?' * len(ids))})", [expr] + ids):
            # the topic name is on the result's first line already
            snips[h[0]] = [[c, s] for c, s in zip(COLS[:3], (_snippet(x or "") for x in h[1:4])) if s]
    out = [{"id": r["id"], "exam": r["exam"], "code": r["code"], "q": r["q"], "marks": r["marks"], "year": r["year"],
            "topic": r["topic"], "topic_name": r["topic_name"], "snippets": snips.get(r["rowid"], [])} for r in page]
    return {"total": len(rows), "counts": counts, "papers": papers, "tasks": task_counts,
            "rows": out, "terms": terms(con, text) if not code else []}
