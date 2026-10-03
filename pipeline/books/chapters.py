#!/usr/bin/env python3
"""Index the textbook chapters — without putting the textbook in the database.

The earlier plan was to chunk the books into paragraph-sized pieces and store
them for retrieval. That plan was wrong for what this is actually for. A model
does not need a retrieved paragraph to explain integration by substitution; it
already knows the mathematics. What it does not know is what Cambridge expects
at this level, in what order, with what notation — and teaching is linear, so
the unit that matters is the chapter, not the paragraph.

So the chapters stay on disk as markdown, read whole. What goes in the database
is the *index*: which chapter belongs to which syllabus topic, which learning
outcomes it does and does not appear to cover, and where the file is. That is
the join the question bank needs, and it is small.

The coverage check is the point. "One chapter with no gaps" is only checkable
against an authority, and the syllabus is the authority: every learning outcome
Cambridge lists for a topic, matched against the chapter text. Where an outcome
has no support in the chapter, that is either a real gap in the book, a gap in
the OCR, or a mis-mapped chapter — all three are worth knowing before you teach
from it.

    python3 chapters.py index caie.db books/9709_p1  --syllabus 9709 --components 1
    python3 chapters.py index caie.db books/9709_p23 --syllabus 9709 --components 2,3
    python3 chapters.py coverage caie.db [--syllabus 9709]
"""
import json, os, re, sqlite3, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))          # 项目根目录
from lib import paths
from pipeline.tags import topic_model

SCHEMA = """
CREATE TABLE IF NOT EXISTS chapters (
  id            TEXT PRIMARY KEY,
  syllabus      TEXT,
  book          TEXT,
  chapter_no    INTEGER,
  title         TEXT,
  path          TEXT NOT NULL,
  page_from     INTEGER,
  page_to       INTEGER,
  words         INTEGER,
  topic         TEXT,
  topic_name    TEXT,
  subtopic      TEXT,
  subtopic_name TEXT,
  topic_all     TEXT,
  topic_score   REAL,
  covered       TEXT,
  missing       TEXT,
  coverage      REAL,
  checked_at    TEXT
);
CREATE INDEX IF NOT EXISTS chapters_topic ON chapters(syllabus, topic);
"""

WORD = re.compile(r"[A-Za-z][A-Za-z\-']+")
# markdown/OCR furniture that would otherwise count as chapter content.
# The maths span is deliberately not DOTALL: an odd number of '$' in a
# formula-dense chapter would otherwise swallow pages of real prose.
NOISE = re.compile(r"<!--.*?-->|!\[[^\]]*\]\([^)]*\)|"
                   r"<[^>]{1,200}>|\${1,2}[^$\n]{0,400}?\${1,2}")
MIN_TERM = 4          # shorter words carry no topic signal here


def plain(text):
    """Chapter prose, with markup and running furniture removed.

    A running header — "Pure Mathematics 2 and 3 Cambridge International..." —
    appears on every page of the chapter and is pure noise, but it is noise
    that scores: it was one of the terms that pushed the Trigonometry chapter
    onto Complex numbers. Any line repeated across many pages is furniture.
    """
    text = NOISE.sub(" ", text or "")
    lines = text.split("\n")
    freq = {}
    for ln in lines:
        s = " ".join(ln.split())
        if len(s) > 8:
            freq[s] = freq.get(s, 0) + 1
    cut = max(4, len(lines) // 200)
    return "\n".join(ln for ln in lines
                      if freq.get(" ".join(ln.split()), 0) <= cut)


TITLE_NOISE = re.compile(r"^\s*(?:chapter|unit)?\s*\d{0,2}\s*[.:)-]?\s*", re.I)


def stem_words(s):
    return {w[:5] for w in re.findall(r"[a-z]+", (s or "").lower()) if len(w) > 2}


def title_match(chapter_title, topic_name):
    """How much of the topic's name the chapter's own title reproduces.

    The strongest signal in the whole exercise and the one I left on the table:
    publishers name the chapter after the syllabus topic. "Chapter 3
    Trigonometry" is topic Trigonometry, whatever the body-text word counts say.
    """
    a = stem_words(TITLE_NOISE.sub("", chapter_title or ""))
    b = stem_words(topic_name or "")
    if not a or not b:
        return 0.0
    return len(a & b) / len(b)


def content_words(s):
    return {w.lower() for w in WORD.findall(s or "") if len(w) >= MIN_TERM
            and w.lower() not in topic_model.STOP}


def outcome_coverage(chapter_text, outcomes):
    """Per learning outcome: which of its content words the chapter contains.

    Deliberately crude — word presence, not meaning. It is a *screen*: a low
    score means go and look, not that the book is wrong. Being crude is why it
    can report which words are missing, which is the part a human can act on.
    """
    have = content_words(plain(chapter_text))
    rows = []
    for o in outcomes:
        want = content_words(o)
        if not want:
            continue
        hit = want & have
        rows.append({"outcome": o,
                     "score": round(len(hit) / len(want), 2),
                     "missing": sorted(want - hit)[:12]})
    return rows




def store_path(p):
    """Portable form: relative to qb/ if inside it, absolute if outside.

    The MCP server is started by a client from whatever directory it likes, so
    a path relative to the shell that happened to run the indexer is useless.
    Keeping in-tree files relative is what lets the whole qb/ folder be copied
    to another machine.
    """
    return paths.relative_to_data(p)


def index_folder(db, folder, syllabus, components=None, book=None):
    con = sqlite3.connect(db)
    con.executescript(SCHEMA)
    models = topic_model.load()
    if syllabus not in models:
        sys.exit(f"没有 {syllabus} 的大纲数据,先跑 syllabus.py")
    model = models[syllabus]
    book = book or os.path.basename(folder.rstrip("/"))

    idx = {}
    ipath = os.path.join(folder, "_index.json")
    if os.path.exists(ipath):
        idx = {e["file"]: e for e in json.load(open(ipath))}

    files = sorted(f for f in os.listdir(folder) if f.endswith(".md"))
    rows = []
    for f in files:
        text = open(os.path.join(folder, f), encoding="utf-8").read()
        meta = idx.get(f, {})
        no = meta.get("chapter")
        if no is None:
            # "…_ch04_…" and "04_4_Differentiation.md" are both in use
            m = re.search(r"ch(\d+)", f) or re.match(r"(\d+)", f)
            no = int(m.group(1)) if m else None
        title = meta.get("title") or (text.lstrip().split("\n", 1)[0].lstrip("# ").strip())

        # Scope to the book's own papers. "Integration" is 1.8 in Pure 1,
        # 2.5 in Pure 2 and 3.5 in Pure 3 — the chapter text alone cannot tell
        # them apart, and without this a Pure 2&3 chapter lands on 1.8.
        body = plain(text)[:120000]
        scored = []
        for comp in (components or [None]):
            scored += model.score(body, comp)
        agg = {}
        for s, c, h in scored:
            if s > agg.get(c, (-1,))[0]:
                agg[c] = (s, c, h)

        # the chapter's own title, weighed against each candidate's name
        boosted = []
        for s, c, h in agg.values():
            name = (model.topics[c]["component_name"] if syllabus == "9618"
                    else model.topics[c]["name"])
            boosted.append((s * (1 + 3 * title_match(title, name)), s, c, h))
        boosted.sort(key=lambda r: -r[0])
        # Near-ties go to where the questions are. 9709's P2 and P3 give the
        # same names to the same topics, so "Further integration" matches 2.5
        # and 3.5 equally — but the bank holds no P2 papers, and a chapter
        # pointing at 2.5 joins to nothing.
        if boosted:
            top = boosted[0][0]
            topname = (model.topics[boosted[0][2]]["component_name"]
                       if syllabus == "9618" else model.topics[boosted[0][2]]["name"])
            # 9709 P2 and P3 are the same syllabus text twice over, so 2.5 and
            # 3.5 are both called "Integration". Same name means the choice is
            # between papers, not between topics — settle it on where the
            # questions are, however wide the score gap.
            same = [b for b in boosted
                    if (model.topics[b[2]]["component_name"] if syllabus == "9618"
                        else model.topics[b[2]]["name"]) == topname]
            close = [b for b in boosted if b[0] >= top * 0.85]
            close = same if len(same) > 1 else close
            if len(close) > 1:
                def nq(code):
                    key = code.split(".")[0] if syllabus == "9618" else code
                    return con.execute(
                        "SELECT COUNT(*) FROM questions WHERE syllabus=? AND topic=?",
                        (syllabus, key)).fetchone()[0]
                # Only demote candidates the bank has nothing for. Ranking by
                # question count instead would collapse Further Maths chapters
                # 4 and 20 — "Matrices 1" and "Matrices 2", genuinely different
                # topics — onto whichever of 1.4 and 2.2 happens to be busier.
                close.sort(key=lambda b: (0 if nq(b[2]) else 1, -b[0]))
                boosted = close + [b for b in boosted if b not in close]
        scored = [(b[1], b[2], b[3]) for b in boosted]
        best = scored[0] if scored else None
        shortlist = [c for _s, c, _h in scored[:3]]
        topic = best[1] if best else None
        outcomes = model.topics[topic]["outcomes"] if topic else []
        cov = outcome_coverage(text, outcomes)
        weak = [c for c in cov if c["score"] < 0.4]
        overall = round(sum(c["score"] for c in cov) / len(cov), 2) if cov else None

        rows.append((
            f"{syllabus}_{book}_ch{no:02d}" if no else f"{syllabus}_{book}_{f}",
            syllabus, book, no, title, store_path(os.path.join(folder, f)),
            meta.get("page_from"), meta.get("page_to"),
            len(WORD.findall(plain(text))),
            # 9618's questions are tagged by syllabus section, so a chapter has
            # to be too or the join finds nothing
            (topic.split(".")[0] if (topic and syllabus == "9618") else topic),
            ((model.topics[topic]["component_name"] if syllabus == "9618"
              else model.topics[topic]["name"]) if topic else None),
            topic if (topic and syllabus == "9618") else None,
            model.topics[topic]["name"] if (topic and syllabus == "9618") else None,
            json.dumps(shortlist), round(best[0], 3) if best else None,
            json.dumps([c["outcome"] for c in cov if c["score"] >= 0.4], ensure_ascii=False),
            json.dumps(weak, ensure_ascii=False), overall,
            __import__("datetime").date.today().isoformat()))

    con.executemany(
        "INSERT OR REPLACE INTO chapters VALUES (" + ",".join("?" * 19) + ")", rows)
    con.commit()

    print(f"{book}: {len(rows)} 章入索引\n")
    print(f"{'章':<4}{'标题':<34}{'词数':>7}{'主题':>7}  {'覆盖':>5}  可疑的 learning outcome")
    for r in rows:
        no, title, words, topic, cov = r[3], r[4], r[8], r[9], r[17]
        weak = json.loads(r[16])
        print(f"{no or '?':<4}{title[:32]:<34}{words:>7}{(topic or '?'):>7}  "
              f"{(f'{cov:.0%}' if cov is not None else '  -'):>5}  "
              f"{len(weak)} 条" + (" ← 看一下" if weak else ""))
    con.close()


def report(db, syllabus=None):
    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    q = "SELECT * FROM chapters" + (" WHERE syllabus=?" if syllabus else "")
    rows = con.execute(q, (syllabus,) if syllabus else ()).fetchall()
    if not rows:
        print("还没有索引任何章节。先跑 `chapters.py index`")
        return
    for r in rows:
        weak = json.loads(r["missing"] or "[]")
        if not weak:
            continue
        print(f"\n=== {r['book']} ch{r['chapter_no']:02d} {r['title']}  "
              f"-> {r['topic']} {r['topic_name']}  整体覆盖 {r['coverage']:.0%}")
        for w in weak:
            print(f"   [{w['score']:.0%}] {w['outcome'][:88]}")
            print(f"          缺: {', '.join(w['missing'][:8])}")

    # Two chapters often share a topic — Pure Maths 1 splits topic 1.7 into
    # "Differentiation" and "Further differentiation", and neither covers it
    # alone. What matters for teaching is whether the *book* covers the topic,
    # so recompute against every chapter that maps to it.
    from pipeline.tags import topic_model as _tm
    models = _tm.load()
    by_topic = {}
    for r in con.execute("SELECT syllabus, topic, path FROM chapters "
                         "WHERE topic IS NOT NULL"):
        by_topic.setdefault((r[0], r[1]), []).append(r[2])
    gaps = []
    for (syl, topic), chapter_paths in sorted(by_topic.items()):
        m = models.get(syl)
        if not m:
            continue
        codes = [c for c in m.topics if c == topic or c.split(".")[0] == topic]
        outcomes = [o for c in codes for o in m.topics[c]["outcomes"]]
        if not outcomes:
            continue
        text = ""
        for pth in chapter_paths:
            f = paths.under_data(pth)
            if os.path.exists(f):
                text += open(f, encoding="utf-8").read()
        cov = outcome_coverage(text, outcomes)
        weak = [c for c in cov if c["score"] < 0.4]
        overall = sum(c["score"] for c in cov) / len(cov)
        if weak:
            gaps.append((syl, topic, len(chapter_paths), overall, weak))
    print("\n" + "=" * 72)
    print("按主题合并所有相关章节之后,仍然找不到着落的 learning outcome:")
    if not gaps:
        print("  没有 —— 每条大纲要求都在书里有对应内容")
    for syl, topic, n, overall, weak in sorted(gaps, key=lambda g: g[3]):
        nm = (models[syl].topics.get(topic) or {}).get("name") or ""
        print(f"\n  {syl} {topic} {nm[:34]:<36} {n} 章合看,覆盖 {overall:.0%}")
        for w in weak:
            print(f"     [{w['score']:.0%}] {w['outcome'][:74]}")
            print(f"            缺: {', '.join(w['missing'][:7])}")

    # a topic with questions but no chapter is a hole in the teaching material
    holes = con.execute("""
        SELECT q.syllabus, q.topic, q.topic_name, COUNT(*) n FROM questions q
        WHERE q.topic IS NOT NULL
          AND NOT EXISTS (SELECT 1 FROM chapters c
                          WHERE c.syllabus=q.syllabus AND c.topic=q.topic)
        GROUP BY q.syllabus, q.topic ORDER BY n DESC""").fetchall()
    if holes:
        print(f"\n有题但没有对应章节的主题({len(holes)} 个):")
        for h in holes[:20]:
            print(f"   {h[0]} {h[1]:<5} {(h[2] or '')[:38]:<40} {h[3]} 道题")
    con.close()


if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    syl = sys.argv[sys.argv.index("--syllabus") + 1] if "--syllabus" in sys.argv else None
    if not a:
        sys.exit(__doc__)
    if a[0] == "index":
        if len(a) < 3 or not syl:
            sys.exit("用法: chapters.py index caie.db <章节目录> "
                     "--syllabus 9709 [--components 2,3]")
        comps = None
        if "--components" in sys.argv:
            comps = sys.argv[sys.argv.index("--components") + 1].split(",")
        index_folder(a[1], a[2], syl, comps)
    elif a[0] == "coverage":
        report(a[1] if len(a) > 1 else paths.DB, syl)
    else:
        sys.exit(__doc__)
