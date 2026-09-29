#!/usr/bin/env python3
"""Stdio MCP server exposing the CAIE question bank (9709 / 9231 / 9618).

No dependencies beyond the standard library — speaks JSON-RPC over stdin/stdout
directly, so it runs anywhere Python 3 does.

Register it with any MCP-speaking client, e.g. in Claude Desktop's config:

  "mcpServers": {
    "caie-question-bank": {
      "command": "python3",
      "args": ["/绝对路径/question_bank/mcp_server.py"]
    }
  }
"""
import datetime, json, os, sqlite3, sys

import os, sys
_here = os.path.dirname(os.path.abspath(__file__))
for _p in (_here, os.path.dirname(_here)):      # 放在 attic/ 里也照样找得到 lib/
    if os.path.isdir(os.path.join(_p, "lib")) and _p not in sys.path:
        sys.path.insert(0, _p)
import progress
from lib import paths
from lib.db import connect

try:
    from pipeline.books import chapters as chapters_mod
except Exception:
    chapters_mod = None

DB = paths.DB
PAPER_TOTAL = {
    ("9709", "1"): 75, ("9709", "3"): 75, ("9709", "4"): 50, ("9709", "5"): 50,
    ("9231", "1"): 75, ("9231", "2"): 75, ("9231", "3"): 50, ("9231", "4"): 50,
    ("9618", "1"): 75, ("9618", "2"): 75, ("9618", "3"): 75, ("9618", "4"): 75,
}


def db():
    return connect(DB)


def slim(r):
    d = dict(r)
    # the OCR'd mark scheme is the readable one; the pdftotext layer loses every
    # '=' and fraction bar in maths, so surface it only as a fallback
    if d.get("ms_latex"):
        d["mark_scheme"] = d["ms_latex"]
        d["mark_scheme_source"] = "ocr"
    else:
        d["mark_scheme"] = d.get("ms_text")
        d["mark_scheme_source"] = "text-layer"
    d["image_path"] = paths.resolve(d.get("image"))
    if d.get("subtopic"):
        d["subtopic_label"] = f"{d['subtopic']} {d.get('subtopic_name') or ''}".strip()
    for k in ("qp_pages", "marks_parts", "parts", "mark_codes", "topic_all"):
        if d.get(k):
            try:
                d[k] = json.loads(d[k])
            except Exception:
                pass
    return d


# ---------------------------------------------------------------- tools

def t_search(syllabus=None, topic=None, component=None, marks_min=None,
             marks_max=None, text=None, year_from=None, year_to=None,
             exclude_years=None, require_mark_scheme=True, has_diagram=None,
             exclude_tied_topics=False, verified_topic_only=False,
             readable_mark_scheme=False, clean_text_only=False, limit=10):
    sql = "SELECT * FROM questions WHERE 1=1"
    args = []
    if text:
        sql = "SELECT q.* FROM questions q JOIN q_fts f ON f.id=q.id WHERE q_fts MATCH ?"
        args = [text]
    if syllabus:
        sql += " AND syllabus = ?"; args.append(str(syllabus))
    if topic:
        sql += " AND topic = ?"; args.append(topic)
    if component:
        sql += " AND component = ?"; args.append(str(component))
    if marks_min is not None:
        sql += " AND marks >= ?"; args.append(marks_min)
    if marks_max is not None:
        sql += " AND marks <= ?"; args.append(marks_max)
    if year_from:
        sql += " AND year >= ?"; args.append(year_from)
    if year_to:
        sql += " AND year <= ?"; args.append(year_to)
    for y in (exclude_years or []):
        sql += " AND year != ?"; args.append(y)
    if require_mark_scheme:
        sql += " AND (ms_latex IS NOT NULL OR ms_text IS NOT NULL)"
    if readable_mark_scheme:
        sql += " AND ms_latex IS NOT NULL"
    if clean_text_only:
        sql += " AND q_quality = 'ok' AND ms_quality IN ('ok','degraded')"
    if has_diagram is not None:
        sql += " AND has_diagram = ?"; args.append(1 if has_diagram else 0)
    if exclude_tied_topics:
        # model-tagged rows have no keyword margin and are the most reliable
        sql += " AND (topic_margin IS NULL OR topic_margin > 0)"
    if verified_topic_only:
        sql += " AND topic_source = 'model'"
    sql += f" LIMIT {int(limit)}"
    return [slim(r) for r in db().execute(sql, args)]


def t_get(id):
    r = db().execute("SELECT * FROM questions WHERE id=?", (id,)).fetchone()
    return slim(r) if r else {"error": f"no such question: {id}"}


def t_topics(syllabus=None):
    q = ("SELECT syllabus, component, component_name, topic, topic_name, "
         "COUNT(*) AS n FROM questions WHERE topic IS NOT NULL "
         + ("AND syllabus = ? " if syllabus else "")
         + "GROUP BY syllabus, component, topic ORDER BY syllabus, component, topic")
    return [dict(r) for r in db().execute(q, (str(syllabus),) if syllabus else ())]


def t_build_paper(syllabus, component, exclude_years=None):
    syllabus, component = str(syllabus), str(component)
    target = PAPER_TOTAL[(syllabus, component)]
    c = db()
    topics = [r[0] for r in c.execute(
        "SELECT DISTINCT topic FROM questions WHERE syllabus=? AND component=? "
        "AND topic IS NOT NULL ORDER BY topic", (syllabus, component))]
    ex = "".join(" AND year != %d" % y for y in (exclude_years or []))
    picked, used = [], 0
    for t in topics:
        row = c.execute(
            f"SELECT * FROM questions WHERE syllabus=? AND component=? AND topic=? "
            f"AND marks IS NOT NULL AND (ms_latex IS NOT NULL OR ms_text IS NOT NULL){ex} "
            f"ORDER BY ABS(marks - ?), RANDOM() LIMIT 1",
            (syllabus, component, t,
             max(2, (target - used) // max(1, len(topics))))).fetchone()
        if row and used + row["marks"] <= target:
            picked.append(slim(row)); used += row["marks"]

    # one per topic rarely reaches the official total; top up with the largest
    # questions that still fit, so the mock is a full-length paper
    while used < target and len(picked) < 16:
        row = c.execute(
            f"SELECT * FROM questions WHERE syllabus=? AND component=? "
            f"AND marks IS NOT NULL AND marks <= ? AND (ms_latex IS NOT NULL OR ms_text IS NOT NULL){ex} "
            f"AND id NOT IN ({','.join('?' * len(picked))}) "
            f"ORDER BY marks DESC, RANDOM() LIMIT 1",
            [syllabus, component, target - used] + [p["id"] for p in picked]).fetchone()
        if not row:
            break
        picked.append(slim(row)); used += row["marks"]

    picked.sort(key=lambda r: r["marks"])
    return {"syllabus": syllabus, "component": component, "total_marks": used,
            "target_marks": target, "questions": picked}


def _syllabus():
    path = paths.SYLLABUS
    return json.load(open(path)) if os.path.exists(path) else {}


def t_topic_detail(syllabus, topic):
    """The syllabus's own words for a topic — what teaching it means."""
    spec = _syllabus().get(str(syllabus))
    if not spec:
        return {"error": "syllabus.json not found; run syllabus.py first"}
    codes = [c for c in spec["topics"]
             if c == str(topic) or c.split(".")[0] == str(topic)]
    if not codes:
        return {"error": f"no such topic: {syllabus} {topic}"}
    pre = progress.load_prereq()
    c = db()
    out = {"syllabus": str(syllabus), "topic": str(topic), "sections": []}
    for code in sorted(codes, key=lambda x: [int(i) for i in x.split(".")]):
        t = spec["topics"][code]
        out["sections"].append({
            "code": code, "name": t["name"],
            "component": t["component"], "component_name": t["component_name"],
            "learning_outcomes": t["outcomes"], "notes": t["notes"]})
    out["assumes"] = progress.upstream(pre, str(syllabus), str(topic))
    out["related"] = [e["b"] if e["a"] == f"{syllabus}:{topic}" else e["a"]
                      for e in pre["topic_related"]
                      if f"{syllabus}:{topic}" in (e["a"], e["b"])]
    row = c.execute("SELECT COUNT(*), MIN(marks), MAX(marks) FROM questions "
                    "WHERE syllabus=? AND topic=?", (str(syllabus), str(topic))).fetchone()
    out["questions_in_bank"] = row[0]
    out["marks_range"] = [row[1], row[2]]
    return out


def t_record_attempt(question_id, grade, note=None, seconds=None, date=None):
    """Write one attempt to the learner record."""
    c = progress.init(DB)
    if not c.execute("SELECT 1 FROM questions WHERE id=?", (question_id,)).fetchone():
        return {"error": f"no such question: {question_id}"}
    at = date or datetime.date.today().isoformat()
    try:
        progress.add(c, question_id, grade, at, seconds, note, "mcp")
    except ValueError as e:
        return {"error": str(e)}
    n = c.execute("SELECT COUNT(*) FROM attempts WHERE question_id=?",
                  (question_id,)).fetchone()[0]
    return {"recorded": question_id, "grade": grade, "date": at,
            "attempts_on_this_question": n,
            "total_attempts": c.execute("SELECT COUNT(*) FROM attempts").fetchone()[0]}


def t_weak_topics(syllabus=None, component=None, limit=10):
    """Topics ranked weakest first, each with its prerequisite context."""
    c = progress.init(DB)
    rows = progress.weak_report(c, syllabus, component, limit)
    if not rows:
        return {"note": "no attempts recorded yet — call record_attempt, or "
                        "import the practice page's export with progress.py",
                "topics": []}
    return {"topics": rows}


def t_next_lesson(syllabus=None, component=None, questions=5):
    """Pick what to work on next, and assemble the material for it.

    Weakest-first, but skipping any topic whose own prerequisites are still
    weak — teaching 9231 2.3 to someone who cannot do 9709 3.4 wastes the
    session. The chosen topic comes back with the syllabus text and a ladder
    of real questions, easiest first, previously-missed ones included.
    """
    c = progress.init(DB)
    ranked = progress.weak_report(c, syllabus, component, limit=40)
    if not ranked:
        # nothing attempted yet: start at the beginning of the component
        row = c.execute(
            "SELECT syllabus, topic FROM questions WHERE topic IS NOT NULL"
            + (" AND syllabus=?" if syllabus else "")
            + (" AND component=?" if component else "")
            + " ORDER BY syllabus, topic LIMIT 1",
            tuple(x for x in (syllabus, component) if x)).fetchone()
        if not row:
            return {"error": "no questions match"}
        target = {"syllabus": row[0], "topic": row[1], "score": None,
                  "diagnosis": "还没有作答记录,从这个部分的第一个主题开始"}
    else:
        ready = [t for t in ranked if not t["diagnosis"].startswith("先补先修")]
        target = ready[0] if ready else ranked[0]
        if not ready:
            # everything is blocked; teach the upstream gap instead
            up = target["prerequisites"][0]["topic"].split(":")
            target = {"syllabus": up[0], "topic": up[1],
                      "score": target["prerequisites"][0]["score"],
                      "diagnosis": f"先修 {up[0]} {up[1]} 还没过关,先补这个"}

    syl, topic = target["syllabus"], target["topic"]
    seen = {r[0] for r in c.execute(
        "SELECT DISTINCT question_id FROM attempts")}
    # a separate handle: progress' connection returns plain tuples, and slim()
    # needs the named-column rows that db() sets up
    pool = [slim(r) for r in db().execute(
        "SELECT * FROM questions WHERE syllabus=? AND topic=? AND marks IS NOT NULL "
        "AND (ms_latex IS NOT NULL OR ms_text IS NOT NULL) AND q_quality='ok' "
        "ORDER BY marks", (syl, topic))]
    missed = [q for q in pool if q["id"] in seen]
    fresh = [q for q in pool if q["id"] not in seen]
    ladder, step = [], max(1, len(fresh) // max(1, questions))
    ladder += missed[:1]                       # revisit one that was missed
    ladder += fresh[::step][:questions - len(ladder)]
    return {"teach": t_topic_detail(syl, topic),
            "why": target.get("diagnosis"),
            "current_score": target.get("score"),
            "questions": ladder}


def _chapter_rows(where="", args=()):
    c = db()
    try:
        return c.execute("SELECT * FROM chapters " + where, args).fetchall()
    except sqlite3.OperationalError:
        return None          # chapters.py has not been run yet


def t_list_chapters(syllabus=None, book=None):
    """The teaching material, in reading order."""
    w, a = [], []
    if syllabus:
        w.append("syllabus=?"); a.append(str(syllabus))
    if book:
        w.append("book=?"); a.append(book)
    rows = _chapter_rows(("WHERE " + " AND ".join(w) if w else "")
                         + " ORDER BY book, chapter_no", a)
    if rows is None:
        return {"error": "no chapters indexed yet — run chapters.py index"}
    c = db()
    out = []
    for r in rows:
        n = c.execute("SELECT COUNT(*) FROM questions WHERE syllabus=? AND topic=?",
                      (r["syllabus"], r["topic"])).fetchone()[0]
        out.append({"id": r["id"], "book": r["book"], "chapter": r["chapter_no"],
                    "title": r["title"], "topic": r["topic"],
                    "topic_name": r["topic_name"], "words": r["words"],
                    "syllabus_coverage": r["coverage"], "questions_available": n})
    return {"chapters": out}


def t_get_chapter(id=None, syllabus=None, topic=None, book=None,
                  include_text=False, questions=6):
    """Everything needed to teach one chapter end to end.

    Returns the chapter's own path and outline, the syllabus outcomes it is
    supposed to deliver, which of those the text appears to miss, and past-paper
    questions for the same topic. `include_text` returns the whole chapter —
    tens of thousands of tokens — so leave it off when the client can read the
    file itself.
    """
    if id:
        rows = _chapter_rows("WHERE id=?", (id,))
    elif syllabus and topic:
        # more than one book can cover a topic (Pure 1 and Pure 2&3 both have
        # an Integration chapter); prefer the one that covers the syllabus best
        w, a = "WHERE syllabus=? AND topic=?", [str(syllabus), str(topic)]
        if book:
            w += " AND book=?"; a.append(book)
        rows = _chapter_rows(w + " ORDER BY coverage DESC NULLS LAST", a)
    else:
        return {"error": "give either id, or syllabus + topic"}
    if rows is None:
        return {"error": "no chapters indexed yet — run chapters.py index"}
    if not rows:
        return {"error": "no chapter matches"}
    r = rows[0]

    path = r["path"]
    if not os.path.isabs(path):
        path = paths.under_data(path)
    text, outline = None, []
    if os.path.exists(path):
        raw = open(path, encoding="utf-8").read()
        outline = [ln.strip() for ln in raw.split("\n")
                   if ln.startswith("#") or ln.strip().startswith("##")][:60]
        if include_text:
            text = raw

    detail = t_topic_detail(r["syllabus"], r["topic"]) if r["topic"] else {}
    qs = [slim(x) for x in db().execute(
        "SELECT * FROM questions WHERE syllabus=? AND topic=? AND marks IS NOT NULL "
        "AND (ms_latex IS NOT NULL OR ms_text IS NOT NULL) AND q_quality='ok' "
        "ORDER BY marks LIMIT ?", (r["syllabus"], r["topic"], int(questions)))]

    return {
        "id": r["id"], "book": r["book"], "chapter": r["chapter_no"],
        "title": r["title"], "path": path, "words": r["words"],
        "pages": [r["page_from"], r["page_to"]],
        "topic": r["topic"], "topic_name": r["topic_name"],
        "outline": outline,
        "syllabus": detail.get("sections"),
        "assumes": detail.get("assumes"),
        "coverage": r["coverage"],
        "outcomes_possibly_missing": json.loads(r["missing"] or "[]"),
        "questions": qs,
        "text": text,
    }


TOOLS = {
    "search_questions": (t_search, "Search real CAIE past-paper questions (9709 Maths, 9231 Further Maths, 9618 Computer Science) by topic code, paper, mark tariff, year, diagram presence, or full text. Returns the question as LaTeX (question_latex), its mark scheme, and the path to a loss-free image crop of the original.", {
        "type": "object", "properties": {
            "syllabus": {"type": "string", "enum": ["9709", "9231", "9618"], "description": "9709 Mathematics, 9231 Further Mathematics, 9618 Computer Science"},
            "topic": {"type": "string", "description": "Topic code. 9709: 1.1-1.8/3.1-3.9/4.1-4.5/5.1-5.5. 9231: 1.1-1.7/2.1-2.6/3.1-3.6/4.1-4.5. 9618: section number '1'-'20'. Call list_topics first."},
            "component": {"type": "string", "enum": ["1", "2", "3", "4", "5"], "description": "Paper number within the syllabus"},
            "marks_min": {"type": "integer"}, "marks_max": {"type": "integer"},
            "text": {"type": "string", "description": "Full-text search over question and mark scheme"},
            "year_from": {"type": "integer"}, "year_to": {"type": "integer"},
            "exclude_years": {"type": "array", "items": {"type": "integer"}, "description": "Hold years out, e.g. to keep a mock unseen"},
            "require_mark_scheme": {"type": "boolean", "default": True},
            "clean_text_only": {"type": "boolean", "description": "Keep only questions whose text is clean and complete. q_quality is 'ok' (clean), 'partial' (readable but the OCR degenerated partway, so later parts are missing — the image is still complete), 'garbled', or 'missing'."},
            "readable_mark_scheme": {"type": "boolean", "description": "Only questions whose mark scheme was re-read by OCR into clean LaTeX. Maths mark schemes taken from the PDF text layer lose every '=' and fraction bar and are not worth reading."},
            "has_diagram": {"type": "boolean", "description": "Filter to questions that do / do not include a figure"},
            "exclude_tied_topics": {"type": "boolean", "description": "Drop questions whose topic tag came from an exact score tie (topic_margin = 0, about 5% of the bank). Those tags are unreliable — roughly a fifth of them have the true topic outside the listed candidates."},
            "verified_topic_only": {"type": "boolean", "description": "Only questions whose topic was checked by a model reading the question (540 of them: 9709 Mechanics, 9231 Further Mechanics, 9618 Practical — the three groups keyword scoring handled worst)."},
            "limit": {"type": "integer", "default": 10}}}),
    "get_question": (t_get, "Fetch one question by id (e.g. 9709_s23_12_q05, 9231_w22_31_q04, 9618_s24_21_q03) with its full mark scheme.", {
        "type": "object", "properties": {"id": {"type": "string"}}, "required": ["id"]}),
    "list_topics": (t_topics, "List topic codes in the bank with question counts. Call this before searching by topic, since the three syllabuses number their topics differently.", {
        "type": "object", "properties": {
            "syllabus": {"type": "string", "enum": ["9709", "9231", "9618"]}}}),
    "topic_detail": (t_topic_detail, "The syllabus's own definition of a topic: every learning outcome and note Cambridge publishes for it, what it assumes as prior knowledge, and how many questions the bank has. Use this to teach a topic rather than only quiz it.", {
        "type": "object", "properties": {
            "syllabus": {"type": "string", "enum": ["9709", "9231", "9618"]},
            "topic": {"type": "string", "description": "Topic code, e.g. '1.7' for maths, '15' for Computer Science"}},
        "required": ["syllabus", "topic"]}),
    "record_attempt": (t_record_attempt, "Record that the learner attempted a question and how it went. Attempts are append-only, so grading the same question again later shows progress rather than overwriting it.", {
        "type": "object", "properties": {
            "question_id": {"type": "string"},
            "grade": {"type": "string", "enum": ["good", "ok", "bad"], "description": "good = solved it, ok = solved with difficulty or partially, bad = could not do it"},
            "note": {"type": "string", "description": "What went wrong, in the learner's or your words"},
            "seconds": {"type": "integer"},
            "date": {"type": "string", "description": "ISO date; defaults to today"}},
        "required": ["question_id", "grade"]}),
    "weak_topics": (t_weak_topics, "Where the learner is weakest, worst first, with a mastery score from 0 to 1 and — crucially — the state of each topic's prerequisites, so you can tell whether the gap is in this topic or upstream of it.", {
        "type": "object", "properties": {
            "syllabus": {"type": "string", "enum": ["9709", "9231", "9618"]},
            "component": {"type": "string"},
            "limit": {"type": "integer", "default": 10}}}),
    "next_lesson": (t_next_lesson, "Decide what to work on next and return the material for it: the weakest topic whose prerequisites are solid, its syllabus learning outcomes, and a ladder of real questions from easy to hard. Falls back to the upstream gap when everything weak is blocked by a prerequisite.", {
        "type": "object", "properties": {
            "syllabus": {"type": "string", "enum": ["9709", "9231", "9618"]},
            "component": {"type": "string"},
            "questions": {"type": "integer", "default": 5}}}),
    "list_chapters": (t_list_chapters, "The textbook chapters available for teaching, in reading order, each with the syllabus topic it covers, how completely it covers that topic's learning outcomes, and how many past-paper questions exist for it.", {
        "type": "object", "properties": {
            "syllabus": {"type": "string", "enum": ["9709", "9231", "9618"]},
            "book": {"type": "string"}}}),
    "get_chapter": (t_get_chapter, "Everything needed to teach one chapter: its file path and heading outline, the syllabus learning outcomes it should deliver, which of those the text appears to be missing, what it assumes as prior knowledge, and past-paper questions on the same topic. Teaching is linear, so this is the unit to work in — read the file at `path` rather than setting include_text, unless you have no file access.", {
        "type": "object", "properties": {
            "id": {"type": "string", "description": "Chapter id from list_chapters"},
            "syllabus": {"type": "string", "enum": ["9709", "9231", "9618"]},
            "topic": {"type": "string", "description": "Use with syllabus instead of id"},
            "book": {"type": "string", "description": "Narrow to one book when several cover the topic"},
            "include_text": {"type": "boolean", "default": False, "description": "Return the whole chapter body — tens of thousands of tokens"},
            "questions": {"type": "integer", "default": 6}}}),
    "build_paper": (t_build_paper, "Assemble a mock paper from real past-paper questions: one per topic, ascending tariff, hitting that paper's official mark total.", {
        "type": "object", "properties": {
            "syllabus": {"type": "string", "enum": ["9709", "9231", "9618"]},
            "component": {"type": "string", "enum": ["1", "2", "3", "4", "5"]},
            "exclude_years": {"type": "array", "items": {"type": "integer"}}},
        "required": ["syllabus", "component"]}),
}


def handle(req):
    m, rid = req.get("method"), req.get("id")
    if m == "initialize":
        return {"protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "caie-question-bank", "version": "3.0.0"}}
    if m == "tools/list":
        return {"tools": [{"name": n, "description": d, "inputSchema": s}
                          for n, (_, d, s) in TOOLS.items()]}
    if m == "tools/call":
        p = req.get("params", {})
        fn = TOOLS.get(p.get("name"))
        if not fn:
            return {"isError": True, "content": [{"type": "text", "text": "unknown tool"}]}
        try:
            out = fn[0](**(p.get("arguments") or {}))
        except Exception as e:
            return {"isError": True,
                    "content": [{"type": "text", "text": f"{type(e).__name__}: {e}"}]}
        return {"content": [{"type": "text",
                             "text": json.dumps(out, ensure_ascii=False, indent=1)}]}
    return None


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except Exception:
            continue
        res = handle(req)
        if req.get("id") is None:      # notification
            continue
        msg = {"jsonrpc": "2.0", "id": req["id"]}
        msg["result" if res is not None else "error"] = \
            res if res is not None else {"code": -32601, "message": "method not found"}
        sys.stdout.write(json.dumps(msg, ensure_ascii=False) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
