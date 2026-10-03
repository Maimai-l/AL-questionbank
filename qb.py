#!/usr/bin/env python3
"""Query the CAIE question bank (9709 Maths, 9231 Further Maths, 9618 Computer Science).

  qb.py stats                                        what is in the bank
  qb.py topics --syllabus 9231                       topic codes and counts
  qb.py find --syllabus 9709 --topic 1.7 --marks 6-8
  qb.py find --text "recursion" --syllabus 9618
  qb.py show 9709_s23_12_q05 --full                  one question + mark scheme
  qb.py paper --syllabus 9231 --component 3          assemble a mock paper
  qb.py chapters                                     教材章节体检(主题码 / 标题 / 能配上多少题)
  qb.py serve                                        起本地服务并打开网页(教材/刷题)

Add --json to any command for machine-readable output.
"""
import argparse, json, sqlite3, sys

from lib import paths
from lib.db import connect

DB = paths.DB

SYLLABUS = {"9709": "Mathematics", "9231": "Further Mathematics",
            "9618": "Computer Science",
            "TMUA": "Mathematics Admissions Test",
            "TSA": "Thinking Skills Assessment (TARA preparation)",
            "BMAT": "BMAT Section 1 (TARA preparation)"}

PAPER_TOTAL = {
    ("9709", "1"): 75, ("9709", "3"): 75, ("9709", "4"): 50, ("9709", "5"): 50,
    ("9231", "1"): 75, ("9231", "2"): 75, ("9231", "3"): 50, ("9231", "4"): 50,
    ("9618", "1"): 75, ("9618", "2"): 75, ("9618", "3"): 75, ("9618", "4"): 75,
}


def con():
    return connect(DB)


def marks_clause(spec):
    if not spec:
        return "", []
    if "-" in spec:
        lo, hi = spec.split("-")
        return " AND marks BETWEEN ? AND ?", [int(lo), int(hi)]
    if spec.startswith(">="):
        return " AND marks >= ?", [int(spec[2:])]
    if spec.startswith("<="):
        return " AND marks <= ?", [int(spec[2:])]
    return " AND marks = ?", [int(spec)]


def do_find(a):
    sql, args = "SELECT * FROM questions WHERE 1=1", []
    if a.text:
        sql = ("SELECT q.* FROM questions q JOIN q_fts f ON f.id = q.id "
               "WHERE q_fts MATCH ?")
        args = [a.text]
    for col, val in (("syllabus", a.syllabus), ("component", a.component),
                     ("topic", a.topic), ("subtopic", getattr(a, "subtopic", None)),
                     ("paper", a.paper)):
        if val:
            sql += f" AND {col} = ?"; args.append(val)
    c, ar = marks_clause(a.marks); sql += c; args += ar
    if a.year_from:
        sql += " AND year >= ?"; args.append(a.year_from)
    if a.year_to:
        sql += " AND year <= ?"; args.append(a.year_to)
    for y in (a.exclude_year or []):
        sql += " AND year != ?"; args.append(y)
    if a.confident:
        sql += " AND topic_confident = 1"
    if a.exclude_ties:
        # model-tagged rows have no keyword margin — they are the *most*
        # reliable, so NULL must not be treated as a tie
        sql += " AND (topic_margin IS NULL OR topic_margin > 0)"
    if a.verified:
        sql += " AND topic_source = 'model'"
    if a.diagram:
        sql += " AND has_diagram = ?"; args.append(1 if a.diagram == "yes" else 0)
    if a.with_ms:
        sql += " AND (ms_latex IS NOT NULL OR ms_text IS NOT NULL)"
    if a.readable_ms:
        sql += " AND ms_latex IS NOT NULL"
    if a.clean:
        sql += " AND q_quality = 'ok' AND ms_quality IN ('ok','degraded')"
    if not a.text:
        sql += " ORDER BY year DESC, month DESC, q"
    sql += f" LIMIT {int(a.n)}"
    return [dict(r) for r in con().execute(sql, args)]


def fmt(rows, full=False):
    out = []
    for r in rows:
        sub = f"  ({r['subtopic']} {r['subtopic_name'] or ''})" \
            if r.get("subtopic") else ""
        out.append(f"[{r['id']}]  {r['paper']}  {r['session']}  Q{r['q']}  "
                   f"[{r['marks']} marks]  {r['topic'] or '?'} "
                   f"{r['topic_name'] or ''}{sub}")
        body = r.get("question_latex") or r["question_text"] or ""
        out.append("  " + body[: None if full else 300])
        flag = "  [has diagram]" if r.get("has_diagram") else ""
        if r.get("image") and not paths.resolve(r["image"]):
            flag += "  [IMAGE NOT FOUND — run `python3 sync.py pull`]"
        src = "" if r.get("topic_source") != "model" else \
              f"  [topic verified: {r.get('topic_note') or 'model-read'}]"
        out.append(f"  image: {r['image']}{flag}{src}")
        ms = r.get("ms_latex") or r["ms_text"]
        if full and ms:
            tag = "mark scheme" if r.get("ms_latex") else "mark scheme (raw text layer)"
            out.append(f"  --- {tag} ---")
            out.append("\n".join("  " + l for l in ms.split("\n")))
        out.append("")
    return "\n".join(out)


def do_paper(syllabus, component, exclude_years=None):
    """One question per topic, ascending tariff, topped up to the paper total."""
    target = PAPER_TOTAL[(syllabus, component)]
    c = con()
    ex = "".join(" AND year != %d" % int(y) for y in (exclude_years or []))
    topics = [r[0] for r in c.execute(
        "SELECT DISTINCT topic FROM questions WHERE syllabus=? AND component=? "
        "AND topic IS NOT NULL ORDER BY topic", (syllabus, component))]
    picked, used = [], 0
    for t in topics:
        row = c.execute(
            f"SELECT * FROM questions WHERE syllabus=? AND component=? AND topic=? "
            f"AND marks IS NOT NULL AND (ms_latex IS NOT NULL OR ms_text IS NOT NULL){ex} "
            f"ORDER BY ABS(marks - ?), RANDOM() LIMIT 1",
            (syllabus, component, t,
             max(2, (target - used) // max(1, len(topics))))).fetchone()
        if row and used + row["marks"] <= target:
            picked.append(dict(row)); used += row["marks"]
    while used < target and len(picked) < 16:
        row = c.execute(
            f"SELECT * FROM questions WHERE syllabus=? AND component=? "
            f"AND marks IS NOT NULL AND marks <= ? AND (ms_latex IS NOT NULL OR ms_text IS NOT NULL){ex} "
            f"AND id NOT IN ({','.join('?' * len(picked))}) "
            f"ORDER BY marks DESC, RANDOM() LIMIT 1",
            [syllabus, component, target - used] + [p["id"] for p in picked]).fetchone()
        if not row:
            break
        picked.append(dict(row)); used += row["marks"]
    picked.sort(key=lambda r: (r["marks"], r["id"]))
    return picked, used, target


def do_serve(port, open_browser=True):
    """刷题服务端(app/server.py):页面、题目、做题记录与手写板同步。需要 aiohttp。"""
    try:
        from app.server import run
    except ImportError as e:
        sys.exit(f"缺少依赖:{e.name}。运行 pip install aiohttp(手写板同步另需 inksync 2.0)")
    if open_browser:
        import threading, webbrowser
        threading.Timer(1.0, lambda: webbrowser.open(f"http://localhost:{port}/")).start()
    run(port)


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    f = sub.add_parser("find")
    f.add_argument("--syllabus", choices=list(SYLLABUS))
    f.add_argument("--component")
    f.add_argument("--topic")
    f.add_argument("--subtopic", help="9618 only: syllabus sub-topic, e.g. 15.2")
    f.add_argument("--paper")
    f.add_argument("--marks", help="5 | 5-8 | >=6 | <=4")
    f.add_argument("--text", help="full-text search over question + mark scheme")
    f.add_argument("--year-from", type=int)
    f.add_argument("--year-to", type=int)
    f.add_argument("--exclude-year", type=int, nargs="*")
    f.add_argument("--confident", action="store_true")
    f.add_argument("--diagram", choices=["yes", "no"])
    f.add_argument("--exclude-ties", action="store_true",
                   help="drop questions whose topic tag was an exact score tie")
    f.add_argument("--verified", action="store_true",
                   help="only questions whose topic was checked by a model")
    f.add_argument("--with-ms", action="store_true")
    f.add_argument("--readable-ms", action="store_true",
                   help="only questions whose mark scheme was OCR'd into readable LaTeX")
    f.add_argument("--clean", action="store_true",
                   help="drop the few questions whose text still reads badly")
    f.add_argument("-n", default=10)
    f.add_argument("--full", action="store_true")
    f.add_argument("--json", action="store_true")

    s = sub.add_parser("show"); s.add_argument("id")
    s.add_argument("--json", action="store_true")
    s.add_argument("--full", action="store_true", help="(show is always full)")
    t = sub.add_parser("topics")
    t.add_argument("--syllabus", choices=list(SYLLABUS)); t.add_argument("--json", action="store_true")
    sub.add_parser("stats").add_argument("--json", action="store_true")
    sub.add_parser("chapters").add_argument("--json", action="store_true")

    sv = sub.add_parser("serve")
    sv.add_argument("--port", type=int, default=8900)
    sv.add_argument("--no-open", action="store_true")

    m = sub.add_parser("paper")
    m.add_argument("--syllabus", required=True, choices=list(SYLLABUS))
    m.add_argument("--component", required=True)
    m.add_argument("--exclude-year", type=int, nargs="*")
    m.add_argument("--json", action="store_true")

    a = p.parse_args()

    if a.cmd == "chapters":
        c = con()
        try:
            rows = [dict(r) for r in c.execute(
                "SELECT syllabus, COUNT(*) chapters, SUM(topic IS NULL) no_topic, "
                "SUM(title IS NULL OR title='') no_title, COUNT(DISTINCT book) books "
                "FROM chapters GROUP BY syllabus ORDER BY syllabus")]
        except sqlite3.OperationalError:
            print("库里没有 chapters 表 —— 先跑 pipeline.books.chapters index"); return
        sample = [dict(r) for r in c.execute(
            "SELECT id, book, chapter_no, title, topic, topic_name FROM chapters LIMIT 8")]
        if a.json:
            print(json.dumps({"summary": rows, "sample": sample}, indent=1, ensure_ascii=False)); return
        for r in rows:
            print(f"{r['syllabus']}: {r['chapters']:>3} 章 / {r['books']} 本  "
                  f"没有主题码 {r['no_topic']}  没有标题 {r['no_title']}")
        print("\n前几行:")
        for r in sample:
            print(f"  {r['id']:<16} book={r['book']!r:<22} no={r['chapter_no']!r:<5} "
                  f"title={r['title']!r:<34} topic={r['topic']!r}")
        n = c.execute("SELECT COUNT(*) FROM questions q JOIN chapters ch "
                      "ON ch.syllabus=q.syllabus AND ch.topic=q.topic").fetchone()[0]
        print(f"\n按 (syllabus, topic) 能配上章节的题:{n} 道")
        return

    if a.cmd == "serve":
        do_serve(a.port, not a.no_open); return

    if a.cmd == "find":
        rows = do_find(a)
        print(json.dumps(rows, indent=1, ensure_ascii=False) if a.json else fmt(rows, a.full))

    elif a.cmd == "show":
        r = con().execute("SELECT * FROM questions WHERE id=?", (a.id,)).fetchone()
        if not r:
            sys.exit(f"no such question: {a.id}")
        print(json.dumps(dict(r), indent=1, ensure_ascii=False) if a.json
              else fmt([dict(r)], full=True))

    elif a.cmd == "topics":
        q = ("SELECT syllabus, component, component_name, topic, topic_name, "
             "COUNT(*) n FROM questions WHERE topic IS NOT NULL "
             + ("AND syllabus = ? " if a.syllabus else "")
             + "GROUP BY syllabus, component, topic ORDER BY syllabus, component, topic")
        rows = [dict(r) for r in con().execute(q, (a.syllabus,) if a.syllabus else ())]
        if a.json:
            print(json.dumps(rows, indent=1, ensure_ascii=False)); return
        cur = None
        for r in rows:
            key = (r["syllabus"], r["component"])
            if key != cur:
                cur = key
                print(f"\n{r['syllabus']} {SYLLABUS.get(r['syllabus'], r['syllabus'])} "
                      f"— Paper {r['component']} {r['component_name']}")
            print(f"  {r['topic']:<5} {r['topic_name']:<48} {r['n']:>4}")

    elif a.cmd == "stats":
        c = con()
        rows = [dict(r) for r in c.execute(
            "SELECT syllabus, COUNT(*) questions, "
            "SUM(ms_latex IS NOT NULL OR ms_text IS NOT NULL) with_ms, "
            "SUM(ms_latex IS NOT NULL) readable_ms, "
            "SUM(question_latex IS NOT NULL) with_latex, SUM(has_diagram) with_diagram, "
            "COUNT(DISTINCT paper||series) papers, MIN(year) y0, MAX(year) y1 "
            "FROM questions GROUP BY syllabus ORDER BY syllabus")]
        if a.json:
            print(json.dumps(rows, indent=1, ensure_ascii=False)); return
        tot = 0
        for r in rows:
            tot += r["questions"]
            print(f"{r['syllabus']} {SYLLABUS.get(r['syllabus'], r['syllabus']):<42} "
                  f"{r['questions']:>4} questions from {r['papers']:>3} papers "
                  f"({r['y0']}-{r['y1']})  ms={r['with_ms']}"
                  f"(ocr {r['readable_ms']}) qlatex={r['with_latex']} "
                  f"diagrams={r['with_diagram']}")
        print(f"{'total':<32} {tot:>4} questions")
        root = paths.image_root_report()
        print(f"image folders: {root}" if root else
              "image folders: NOT FOUND — data/ is missing or empty; "
              "run `python3 sync.py pull` (see docs/data-sync.md)")

    elif a.cmd == "paper":
        picked, used, target = do_paper(a.syllabus, a.component, a.exclude_year)
        if a.json:
            print(json.dumps({"total": used, "target": target, "questions": picked},
                             indent=1, ensure_ascii=False)); return
        name = picked[0]["component_name"] if picked else ""
        print(f"{a.syllabus} Paper {a.component} {name} — mock paper, "
              f"{used}/{target} marks, {len(picked)} questions\n")
        for i, r in enumerate(picked, 1):
            print(f"{i}. ({r['topic']} {r['topic_name']}) [{r['marks']}]  {r['id']}")
            print(f"   {r['image']}")


if __name__ == "__main__":
    main()
