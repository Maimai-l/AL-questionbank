#!/usr/bin/env python3
"""Question and mark scheme text from the question bank (Maimai-l/AL-questionbank), without the PDFs.

    python3 qbank.py paper 9231_w21_13            every question of a paper, with its mark scheme
    python3 qbank.py show 9618_s24_11_q02 [...]   single questions
    python3 qbank.py find --syllabus 9618 [--topic 8] [--text "ALTER TABLE"] [--limit 30]
    python3 qbank.py stats
    add --json for machine-readable output, --no-ms to leave the mark scheme out,
    --explain to add the worked explanation (9618 only)

The bank (caie.db, about 75 MB) is downloaded once from GitHub into --cache
(default ~/.cache/qbank). It holds 9709, 9231 and 9618 papers 2021-2026 and
TMUA, TSA, BMAT. Question and scheme text was checked against the original papers;
diagrams are described in the text only, so look at the PDF when a question has one
(has_diagram = 1). Mark scheme text is the scheme as printed, split by question.
"""
import argparse, json, os, sqlite3, sys, urllib.error, urllib.request

URL = "https://raw.githubusercontent.com/Maimai-l/AL-questionbank/data/caie.db"


def download(path, tries=8):
    """Download URL to path, resuming a cut-off transfer with a Range request."""
    part = path + ".part"
    for k in range(tries):
        have = os.path.getsize(part) if os.path.exists(part) else 0
        req = urllib.request.Request(URL, headers={"Range": f"bytes={have}-"} if have else {})
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                total = have + int(r.headers.get("Content-Length") or 0)
                if have and r.status != 206:          # server ignored the range: start over
                    have, total = 0, int(r.headers.get("Content-Length") or 0)
                with open(part, "ab" if have else "wb") as f:
                    while True:
                        chunk = r.read(1 << 20)
                        if not chunk:
                            break
                        f.write(chunk)
            if os.path.getsize(part) >= total > 0:
                os.replace(part, path)
                return
        except urllib.error.HTTPError as e:
            if e.code == 416 and have:                # already complete
                os.replace(part, path)
                return
            if e.code in (403, 404):
                sys.exit(f"下载失败(HTTP {e.code}):网络设置里要允许 raw.githubusercontent.com")
        except OSError as e:
            if k == tries - 1:
                sys.exit(f"下载失败({e}):网络设置里要允许 raw.githubusercontent.com")
    sys.exit("下载多次中断,再运行一次会接着下载")


def connect(cache):
    path = os.path.join(os.path.expanduser(cache), "caie.db")
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        print(f"下载题库 {URL}(约 75 MB,只下载一次)", file=sys.stderr)
        download(path)
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    return con


def row(r, a):
    d = {"id": r["id"], "marks": r["marks"], "topic": r["topic_name"], "has_diagram": r["has_diagram"],
         "question": r["question_latex"] or r["question_text"]}
    if not a.no_ms:
        d["mark_scheme"] = r["ms_latex"] or r["ms_text"]
    if a.explain and r["explanation"]:
        d["explanation"] = json.loads(r["explanation"])
    if r["answer"]:
        d["answer"] = r["answer"]
    return d


def emit(rows, a):
    if a.json:
        print(json.dumps(rows, ensure_ascii=False, indent=1))
        return
    for d in rows:
        head = f"=== {d['id']}  [{d['marks'] or '?'} 分]  {d['topic'] or ''}"
        print(head + ("  (有图,看原卷)" if d["has_diagram"] else ""))
        print(d["question"] or "(无题干文本)")
        if "answer" in d:
            print(f"\n--- 答案: {d['answer']}")
        if "mark_scheme" in d:
            print("\n--- mark scheme\n" + (d["mark_scheme"] or "(无)"))
        if "explanation" in d:
            print("\n--- 详解\n" + json.dumps(d["explanation"], ensure_ascii=False, indent=1))
        print()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["paper", "show", "find", "stats"])
    ap.add_argument("ids", nargs="*")
    ap.add_argument("--syllabus")
    ap.add_argument("--topic", help="topic code, e.g. 8 or 1.2")
    ap.add_argument("--text")
    ap.add_argument("--limit", type=int, default=30)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--no-ms", action="store_true")
    ap.add_argument("--explain", action="store_true")
    ap.add_argument("--cache", default="~/.cache/qbank")
    a = ap.parse_args()
    con = connect(a.cache)
    if a.cmd == "stats":
        for r in con.execute("SELECT syllabus, COUNT(*) n, COUNT(DISTINCT qp_pdf) p, MIN(year) y0, MAX(year) y1 "
                             "FROM questions GROUP BY syllabus"):
            print(f"{r['syllabus']:5} {r['n']:5} 题  {r['p']:4} 份卷  {r['y0']}-{r['y1']}")
        return
    if a.cmd == "paper":
        rows = []
        for p in a.ids:
            rows += con.execute("SELECT * FROM questions WHERE id LIKE ? ORDER BY q", (p.rstrip("_") + "_q%",)).fetchall()
    elif a.cmd == "show":
        rows = [r for i in a.ids for r in con.execute("SELECT * FROM questions WHERE id = ?", (i,))]
    else:
        sql, args = "SELECT * FROM questions WHERE 1", []
        if a.syllabus:
            sql += " AND syllabus = ?"; args.append(a.syllabus)
        if a.topic:
            sql += " AND (topic = ? OR subtopic = ? OR subtopic LIKE ?)"; args += [a.topic, a.topic, a.topic + ".%"]
        if a.text:
            sql += " AND (COALESCE(question_latex, question_text) LIKE ? OR COALESCE(ms_latex, ms_text) LIKE ?)"
            args += [f"%{a.text}%"] * 2
        rows = con.execute(sql + " ORDER BY id LIMIT ?", args + [a.limit]).fetchall()
        if not a.json:
            for r in rows:
                first = (r["question_latex"] or r["question_text"] or "").strip().splitlines()[:1]
                print(f"{r['id']:22} {r['marks'] or '?':>3} 分  {(first[0] if first else '')[:90]}")
            print(f"{len(rows)} 题")
            return
    if not rows:
        sys.exit("没有找到。题号写法:9618_s24_11_q02;卷写法:9618_s24_11")
    emit([row(r, a) for r in rows], a)


if __name__ == "__main__":
    main()
