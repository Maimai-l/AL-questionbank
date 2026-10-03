#!/usr/bin/env python3
"""Merge OCR'd page markdown into chapters, using the PDF's own bookmarks.

Replaces a hand-written page table. Four of the six textbooks carry an embedded
contents tree — Pure Maths 2&3 has 97 entries across 3 levels — so the chapter
boundaries are already in the file and do not need to be typed in or guessed.
A typed table is also silent when it is wrong: nothing checks that "chapter 1 =
pages 3-7" is true, and a book whose chapters average 32 pages will happily
produce eleven 7-page files that look fine until you read them.

So this reads the ranges from the PDF, and refuses to run when the OCR output
does not cover them.

    python3 split_chapters.py <book.pdf> <page_md_dir> <out_dir> \
            [--prefix 9709_p23] [--level 2] [--table chapters.json] \
            [--syllabus 9231]

Two of the six books are scans with no bookmarks at all. For those the script
proposes a chapter table from the OCR'd headings, writes it next to the output,
and stops — edit it and re-run with --table.

`page_md_dir` holds page_0001.md ... as produced by the OCR script; page
numbers must be 1-based PDF pages.
"""
import json, os, re, shutil, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))          # 项目根目录
from lib import paths

try:
    import fitz
except ImportError:
    fitz = None      # only needed when reading a PDF rather than a toc.json

# front and back matter carry no teachable content and confuse topic matching
SKIP = re.compile(r"^\s*(cover|title|book title|copyright|contents|"
                  r"introduction|how to use|series introduction|acknowledge|"
                  r"index|answers|glossary|key to symbols|the cambridge)",
                  re.I)
SLUG = re.compile(r"[^a-z0-9]+")


def slug(s):
    return SLUG.sub("_", s.lower()).strip("_")[:48]


# "1 Quadratics", "Chapter 4 Differentiation", "10 Momentum"
CHNUM = re.compile(r"^\s*(?:chapter\s+)?(\d{1,2})\s*[.:)]?\s+\S", re.I)


def level_entries(toc, level, n_pages, numbered_only=False):
    """Entries at one TOC level, with end pages filled in.

    End pages are taken from the *next entry at this level*, including the ones
    about to be filtered out — the index letter "A" at page 350 is what tells
    us chapter 11 ends at 349, so it has to be seen before it is dropped.
    """
    at = [(t.strip(), p) for lv, t, p in toc if lv == level and p > 0]
    out = []
    for i, (title, page) in enumerate(at):
        end = (at[i + 1][1] - 1) if i + 1 < len(at) else n_pages
        if SKIP.match(title) or end < page:
            continue
        if numbered_only and not CHNUM.match(title):
            continue
        out.append((len(out) + 1, title, page, end))
    return out


def read_source(pdf):
    """(toc, page_count) from a PDF, or from a toc.json entry.

    Accepts "toc.json::exact file name.pdf" so the chapter split can run on a
    machine that has the OCR output but not the hundreds of megabytes of PDF.
    """
    if "::" in pdf or pdf.lower().endswith(".json"):
        path, _, key = pdf.partition("::")
        data = json.load(open(path))
        if not key:
            if len(data) != 1:
                sys.exit("toc.json 里有多本书,用 toc.json::<书名.pdf> 指定哪一本\n  "
                         + "\n  ".join(data))
            key = next(iter(data))
        if key not in data:
            hit = [k for k in data if key.lower() in k.lower()]
            if len(hit) != 1:
                sys.exit(f"{key!r} 在 toc.json 里找不到唯一匹配。有:\n  "
                         + "\n  ".join(data))
            key = hit[0]
        return [tuple(e) for e in data[key]["toc"]], data[key]["pages"], key
    import fitz
    d = fitz.open(pdf)
    toc = [tuple(e) for e in d.get_toc()]
    n = d.page_count
    d.close()
    return toc, n, os.path.basename(pdf)


def chapters_from_toc(pdf, level=None):
    """(number, title, first_page, last_page) for each real chapter, 1-based.

    Which level holds the chapters differs by book. Pure Maths 2&3 keeps only
    a couple of entries at level 1 — the AS/A Level split — and puts the real
    chapters at level 2, so taking level 1 blindly yields two "chapters" of a
    hundred pages each. Pick the level that looks like a chapter list instead,
    and print the alternatives so the choice can be overridden.
    """
    toc, n, _name = read_source(pdf)
    if not toc:
        return [], n, {}

    depths = sorted({l for l, _t, _p in toc})
    levels = {lv: level_entries(toc, lv, n) for lv in depths if lv <= 3}
    if level:
        return level_entries(toc, int(level), n, True) or levels.get(int(level), []), \
               n, levels

    # Chapters announce themselves with a number. Counting how many entries at
    # each level do that beats guessing from entry counts: Computer Science has
    # 69 entries at level 2 and Pure Maths 2&3 has 31, neither of which fits a
    # "between 4 and 40" rule, yet both levels are exactly right once the
    # unnumbered ones (index letters, appendices) are dropped.
    numbered = {lv: level_entries(toc, lv, n, True) for lv in depths if lv <= 3}
    best = max(numbered, key=lambda lv: (len(numbered[lv]), -lv), default=None)
    if best is not None and len(numbered[best]) >= 4:
        return numbered[best], n, levels

    # nothing numbered anywhere — fall back to whichever level looks least
    # like a list of one-page entries
    def plausible(ents):
        if not (4 <= len(ents) <= 60):
            return -1
        span = sum(z - a + 1 for _n, _t, a, z in ents) / len(ents)
        return span if span >= 4 else -1

    best = max(levels, key=lambda lv: (plausible(levels[lv]), -lv))
    return (levels[best] if plausible(levels[best]) > 0 else []), n, levels


CH_HEAD = re.compile(r"^#{1,4}\s*(?:chapter\s*)?(\d{1,2})\b[\s.:)\-]*(.*)$", re.I)
ANY_HEAD = re.compile(r"^#{1,4}\s*(.+?)\s*$")


def clean_title(s):
    s = re.sub(r"^[#\s.:)\-]+", "", s or "").strip()
    return re.sub(r"\s{2,}", " ", s)[:60]


def norm_words(s):
    # first five letters stand in for a stemmer: "representing" and
    # "representation" are the same chapter, and 9709 5.1 is called
    # "Representation of data" while the book calls it "Representing data"
    return {w[:5] for w in re.findall(r"[a-z]+", (s or "").lower()) if len(w) > 2}


def syllabus_titles(code):
    """Topic names Cambridge uses, as a fallback anchor for unnumbered headings."""
    path = paths.SYLLABUS
    if not code or not os.path.exists(path):
        return []
    spec = json.load(open(path)).get(str(code))
    if not spec:
        return []
    return [t["name"] for t in spec["topics"].values()]


def longest_run(cands):
    """Longest strictly-increasing chain of chapter numbers, in page order.

    The previous rule demanded 1,2,3,... with no gaps, so a single missed
    heading threw away every chapter after it — which is why Further Maths
    stopped at page 390 of 646. A chain that tolerates gaps keeps the rest.
    """
    if not cands:
        return []
    n = len(cands)
    best = [1] * n
    prev = [-1] * n
    for i in range(n):
        for j in range(i):
            if cands[j][1] < cands[i][1] and best[j] + 1 > best[i]:
                best[i], prev[i] = best[j] + 1, j
    i = max(range(n), key=lambda k: best[k])
    out = []
    while i >= 0:
        out.append(cands[i])
        i = prev[i]
    return out[::-1]


def propose_chapters(md_dir, n_pages, syllabus=None):
    """Guess chapter starts from the OCR'd headings of a scanned book.

    Two kinds of evidence, both weak on their own: a heading that carries a
    chapter number, and a heading whose words match a syllabus topic name.
    Only the top of each page is considered — a chapter opens a page, a
    cross-reference to "chapter 4" mid-paragraph does not.

    The result is a starting point for a human, which is why every candidate is
    written out, not only the ones that were kept.
    """
    known = [(t, norm_words(t)) for t in syllabus_titles(syllabus)]
    numbered, named, seen_titles = [], [], set()
    for f in sorted(os.listdir(md_dir)):
        m = re.match(r"page_(\d+)\.md$", f)
        if not m:
            continue
        page = int(m.group(1))
        lines = open(os.path.join(md_dir, f), encoding="utf-8").read().split("\n")[:8]
        for ln in lines:
            hn = CH_HEAD.match(ln)
            if hn:
                numbered.append((page, int(hn.group(1)), clean_title(hn.group(2))))
                break
            ha = ANY_HEAD.match(ln)
            if ha and known:
                w = norm_words(ha.group(1))
                if not w:
                    continue
                for title, kw in known:
                    if kw and len(w & kw) / len(kw) >= 0.6 and title not in seen_titles:
                        seen_titles.add(title)
                        named.append((page, None, clean_title(ha.group(1)) or title))
                        break
                else:
                    continue
                break

    kept = longest_run(numbered)
    # a syllabus-named heading is worth keeping when no numbered chapter starts
    # anywhere near it
    pages = {p for p, _n, _t in kept}
    for p, _n, t in named:
        if all(abs(p - q) > 5 for q in pages):
            kept.append((p, None, t)); pages.add(p)
    kept.sort()

    out = []
    for i, (page, num, title) in enumerate(kept):
        end = (kept[i + 1][0] - 1) if i + 1 < len(kept) else n_pages
        out.append({"chapter": i + 1, "title": title or f"Chapter {i+1}",
                    "page_from": page, "page_to": end,
                    "from_number": num})
    dropped = [{"page": p, "number": n, "title": t}
               for p, n, t in numbered if (p, n, t) not in kept]
    return out, dropped


def load_table(path, n_pages):
    tbl = json.load(open(path))
    return [(int(e["chapter"]), e["title"], int(e["page_from"]),
             int(e.get("page_to") or n_pages)) for e in tbl]


def main(pdf, md_dir, out_dir, prefix=None, level=None, table=None,
         syllabus=None):
    if table:
        _toc, n, _nm = read_source(pdf)
        chs, total_pages, levels = load_table(table, n), n, {}
        print(f"用手工章节表 {table}:{len(chs)} 章")
    else:
        chs, total_pages, levels = chapters_from_toc(pdf, level)
    if levels:
        print("书签各层的样子:")
        chosen_pages = {(t, a) for _n, t, a, _z in chs}
        for lv, ents in levels.items():
            span = (sum(z - a + 1 for _n, _t, a, z in ents) / len(ents)) if ents else 0
            nnum = sum(1 for _n, t, _a, _z in ents if CHNUM.match(t))
            mark = "  <- 用这一层" if ents and {(t, a) for _n, t, a, _z in ents} >= chosen_pages else ""
            print(f"  第 {lv} 层: {len(ents):>3} 条(带章号 {nnum} 条),平均 {span:>5.1f} 页"
                  f"  例:{ents[0][1][:30] if ents else '-'}{mark}")
        print()
    if not chs:
        prop, dropped = propose_chapters(md_dir, total_pages, syllabus)
        os.makedirs(out_dir, exist_ok=True)
        dst = os.path.join(out_dir, "chapters_proposed.json")
        json.dump(prop, open(dst, "w"), ensure_ascii=False, indent=1)
        print(f"{read_source(pdf)[2]} 的书签认不出章节层。")
        print(f"已从 OCR 出来的标题猜了 {len(prop)} 章,写到:\n  {dst}")
        for e in prop:
            src = f"#{e['from_number']}" if e["from_number"] else "按大纲名匹配"
            print(f"   ch{e['chapter']:02d} p{e['page_from']:>4}-{e['page_to']:<4} "
                  f"{(e['page_to']-e['page_from']+1):>4} 页  {e['title'][:40]:<42}{src}")
        if dropped:
            print(f"\n  另有 {len(dropped)} 个带章号的标题没被采纳(章号不递增),"
                  f"写在 chapters_dropped.json 里,漏了章就去那里找")
            json.dump(dropped, open(os.path.join(out_dir, "chapters_dropped.json"),
                                    "w"), ensure_ascii=False, indent=1)
        print("\n核对/改完之后:\n  python3 split_chapters.py <pdf> <page_md> "
              f"<out> --table {dst}")
        sys.exit(0)

    have = {}
    for f in os.listdir(md_dir):
        m = re.match(r"page_(\d+)\.md$", f)
        if m:
            have[int(m.group(1))] = os.path.join(md_dir, f)

    label = read_source(pdf)[2]
    print(f"{label}: {total_pages} 页,书签给出 {len(chs)} 章")
    print(f"OCR 产出 {len(have)} 页 markdown")

    # only the pages a chapter actually claims matter; front matter, answers
    # and the index are not worth OCR'ing and their absence is not a gap
    wanted = {p for _n, _t, a, z in chs for p in range(a, z + 1)}
    missing = sorted(wanted - set(have))
    print(f"章节共占 {len(wanted)} 页,其中有 markdown 的 {len(wanted) - len(missing)} 页")
    if missing:
        print(f"\n⚠️  章节范围内缺 {len(missing)} 页(最早 p{missing[0]},"
              f"最晚 p{missing[-1]})。")
        if len(missing) > len(wanted) * 0.3:
            print("    缺得太多,合出来的章节一定是残的。")
            print("    先补 OCR:python3 ocr_books.py <pdf目录> <pages目录>")
            sys.exit(1)

    os.makedirs(out_dir, exist_ok=True)
    index = []
    for num, title, first, last in chs:
        pages = [p for p in range(first, last + 1) if p in have]
        gap = [p for p in range(first, last + 1) if p not in have]
        name = f"{prefix + '_' if prefix else ''}ch{num:02d}_{slug(title)}.md"
        path = os.path.join(out_dir, name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"# {title}\n\n")
            f.write(f"<!-- {label} p{first}-{last} -->\n\n")
            if gap:
                f.write(f"> ⚠️ 缺 {len(gap)} 页:{gap[:20]}\n\n")
            for p in pages:
                f.write(f"<!-- page {p} -->\n\n")
                f.write(open(have[p], encoding="utf-8").read().strip() + "\n\n")
        index.append({"file": name, "chapter": num, "title": title,
                      "page_from": first, "page_to": last,
                      "pages_present": len(pages), "pages_missing": gap})
        flag = f"  ⚠️ 缺 {len(gap)} 页" if gap else ""
        print(f"  ch{num:02d} {title[:42]:<44} p{first}-{last} "
              f"({len(pages)} 页){flag}")

    for sub in ("imgs", "images"):
        src = os.path.join(md_dir, sub)
        if os.path.isdir(src):
            dst = os.path.join(out_dir, sub)
            if os.path.exists(dst):
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
            print(f"\n图片 {len(os.listdir(dst))} 个 -> {dst}")

    json.dump(index, open(os.path.join(out_dir, "_index.json"), "w"),
              ensure_ascii=False, indent=1)
    print(f"\n{len(index)} 章 -> {out_dir}")


if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    if len(a) < 3:
        sys.exit(__doc__)
    pref = sys.argv[sys.argv.index("--prefix") + 1] if "--prefix" in sys.argv else None
    lvl = sys.argv[sys.argv.index("--level") + 1] if "--level" in sys.argv else None
    tbl = sys.argv[sys.argv.index("--table") + 1] if "--table" in sys.argv else None
    syl = sys.argv[sys.argv.index("--syllabus") + 1] if "--syllabus" in sys.argv else None
    main(a[0], a[1], a[2], pref, lvl, tbl, syl)
