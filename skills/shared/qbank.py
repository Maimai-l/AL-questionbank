#!/usr/bin/env python3
"""Question and mark scheme text from the question bank (Maimai-l/AL-questionbank), without the PDFs.

    python3 qbank.py paper 9231_w21_13            every question of a paper, with its mark scheme
    python3 qbank.py show 9618_s24_11_q02 [...]   single questions
    python3 qbank.py find --syllabus 9618 [--topic 8] [--text "ALTER TABLE"] [--limit 30]
    python3 qbank.py stats
    python3 qbank.py chapter [--syllabus 9702] [--topic 17]    list textbook chapters
    python3 qbank.py chapter 9702 2 [3 ...] [--save DIR]      chapter text (markdown)
    add --json for machine-readable output, --no-ms to leave the mark scheme out,
    --explain to add the worked explanation (9618 only)

The bank (caie.db, about 65 MB) is downloaded once from GitHub into --cache
(default ~/.cache/qbank). It holds 9709, 9231, 9618 and 9702 papers 2021-2026
(the admissions tests were archived in 2026-11). Practice material tagged 精选 (find --tag):
314 Edexcel physics questions under syllabus WPH (220 end-of-chapter questions of Hodder's
Edexcel A Level Physics 1, ids WPH_hb1_ch03_q11, no mark scheme; 94 kinematics questions,
WPH_kpmt_*/WPH_ktop_* without schemes and 56 multiple choice WPH_kmcq_* with answers), and
145 9709 paper 4 questions from a mechanics workbook (9709_mwb_ch05_q03, 139 with the
scheme of their source paper). Figures in their text are images under imgWPH/fig/ and
img9709/fig/. Question and scheme text was checked against the original papers
(not yet for 9702: its text is OCR or, where q_quality is partial, the PDF text layer);
diagrams are described in the text only, so look at the PDF when a question has one
(has_diagram = 1). Mark scheme text is the scheme as printed, split by question.

Textbook chapters (books 9709_p1, 9709_p23, 9709_p4, 9709_p5, 9231, 9618, 9702, and
edx_ial_phy1 and edx_ial_phy2: Edexcel International A Level Physics Books 1 and 2,
syllabus WPH) are
markdown files on the same branch. `chapter` downloads only the chapters asked for into
the cache and prints them, with figure links pointing at GitHub; --save DIR writes the
chapter and its figures to DIR instead (the 9702 chapters are text only). Each CAIE chapter
is mapped to a syllabus topic: list with --topic to find the chapter for a weak topic
(the bank holds no Edexcel syllabus or papers yet, so the WPH chapters have no topic).
--refresh downloads again what the command uses (the bank changes as it is checked).
"""
import argparse, json, os, re, sqlite3, sys, urllib.error, urllib.parse, urllib.request

BASE = "https://raw.githubusercontent.com/Maimai-l/AL-questionbank/data/"
URL = BASE + "caie.db"


def download(path, tries=8, url=URL):
    """Download url to path, resuming a cut-off transfer with a Range request."""
    part = path + ".part"
    for k in range(tries):
        have = os.path.getsize(part) if os.path.exists(part) else 0
        req = urllib.request.Request(url, headers={"Range": f"bytes={have}-"} if have else {})
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


def connect(cache, refresh=False):
    path = os.path.join(os.path.expanduser(cache), "caie.db")
    if refresh and os.path.exists(path):
        os.remove(path)
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        print(f"下载题库 {URL}(约 65 MB,只下载一次)", file=sys.stderr)
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


IMG = re.compile(r'(<img [^>]*src=")(imgs/[^"]+)(")|(!\[[^\]]*\]\()(imgs/[^)\s]+)(\))')


def fetch(rel, cache, refresh=False):
    """A file of the data branch, cached under cache/ at the same relative path."""
    path = os.path.join(os.path.expanduser(cache), *rel.split("/"))
    if refresh and os.path.exists(path):
        os.remove(path)
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        download(path, url=BASE + urllib.parse.quote(rel))
    return path


def topic_match(r, t):
    codes = [r["topic"], r["subtopic"]] + json.loads(r["topic_all"] or "[]")
    return any(c and (c == t or c.startswith(t + ".")) for c in codes)


def chapters(con, a):
    if not con.execute("SELECT name FROM sqlite_master WHERE name = 'chapters'").fetchone():
        sys.exit("这份题库没有 chapters 表;加 --refresh 重新下载")
    rows = con.execute("SELECT * FROM chapters ORDER BY book, chapter_no").fetchall()
    book, nums = (a.ids[0], a.ids[1:]) if a.ids else (None, [])
    rows = [r for r in rows if (not book or r["book"] == book)
            and (not a.syllabus or r["syllabus"] == a.syllabus)
            and (not a.topic or topic_match(r, a.topic))]
    if book and not rows:
        sys.exit("没有这本教材。教材:" + " ".join(
            r[0] for r in con.execute("SELECT DISTINCT book FROM chapters ORDER BY book")))
    if not nums:                                     # a list
        if a.json:
            print(json.dumps([{k: r[k] for k in ("book", "chapter_no", "title", "topic", "topic_name",
                                                 "subtopic", "words", "path")} for r in rows],
                             ensure_ascii=False, indent=1))
            return
        for r in rows:
            topic = " ".join(x for x in (r["topic"] or r["subtopic"], r["topic_name"]) if x)
            print(f"{r['book']:9} {r['chapter_no']:>3}  {r['title'][:46]:46}  {r['words']:>6} 词  {topic}")
        print(f"{len(rows)} 章。取正文:python3 qbank.py chapter <教材> <章号>")
        return
    want = {int(n) for n in nums}
    rows = [r for r in rows if r["chapter_no"] in want]
    if len(rows) < len(want):
        sys.exit(f"{book} 没有第 {' '.join(str(n) for n in sorted(want - {r['chapter_no'] for r in rows}))} 章")
    for r in rows:
        text = open(fetch(r["path"], a.cache, a.refresh), encoding="utf-8").read()
        folder = r["path"].rsplit("/", 1)[0]
        if a.save:
            os.makedirs(a.save, exist_ok=True)
            imgs = sorted({m.group(2) or m.group(5) for m in IMG.finditer(text)})
            for i in imgs:
                dst = os.path.join(a.save, *i.split("/"))
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                with open(fetch(f"{folder}/{i}", a.cache), "rb") as f, open(dst, "wb") as g:
                    g.write(f.read())
            out = os.path.join(a.save, os.path.basename(r["path"]))
            with open(out, "w", encoding="utf-8") as f:
                f.write(text)
            print(f"{out}  ({len(imgs)} 张图)")
            continue
        text = IMG.sub(lambda m: (m.group(1) + BASE + folder + "/" + m.group(2) + m.group(3)) if m.group(1)
                       else (m.group(4) + BASE + folder + "/" + m.group(5) + m.group(6)), text)
        if a.json:
            print(json.dumps({"book": r["book"], "chapter_no": r["chapter_no"], "title": r["title"],
                              "topic": r["topic"], "text": text}, ensure_ascii=False))
        else:
            print(f"=== {r['book']} 第 {r['chapter_no']} 章  {r['title']}  (考纲 {r['topic'] or r['subtopic'] or '-'})\n")
            print(text)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["paper", "show", "find", "stats", "chapter"])
    ap.add_argument("ids", nargs="*")
    ap.add_argument("--syllabus")
    ap.add_argument("--topic", help="topic code, e.g. 8 or 1.2")
    ap.add_argument("--text")
    ap.add_argument("--limit", type=int, default=30)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--no-ms", action="store_true")
    ap.add_argument("--explain", action="store_true")
    ap.add_argument("--cache", default="~/.cache/qbank")
    ap.add_argument("--save", metavar="DIR", help="chapter: write the chapter and its figures to DIR")
    ap.add_argument("--refresh", action="store_true", help="download the bank (and chapters) again")
    a = ap.parse_args()
    con = connect(a.cache, a.refresh)
    if a.cmd == "chapter":
        chapters(con, a)
        return
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
    try:
        main()
    except BrokenPipeError:          # output piped into head
        sys.stderr.close()
