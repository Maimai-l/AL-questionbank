#!/usr/bin/env python3
"""Build a chapter table from the book's own printed contents page.

    python3 contents_table.py <page_md_dir> <out.json> [--syllabus 9231]

For a scanned book with no PDF bookmarks, the obvious source of chapter
boundaries is the one the publisher already wrote: the contents page. It is in
the OCR output like everything else, it lists every chapter with its printed
page number, and it does not depend on whether a chapter heading happened to
survive recognition.

The only thing it does not give is the offset between printed page numbers and
PDF page numbers — the front matter. That is measured rather than assumed: for
each chapter, look for the PDF page where that title appears as a heading, take
the difference, and require the same difference to come out of several chapters
independently. If they disagree the script says so instead of guessing.
"""
import json, os, re, sys
from collections import Counter

# "12 Probability generating functions 279", and also "20 Matrices 2 447" —
# a digit inside the title is normal, so only the trailing number is the page
LINE = re.compile(r"^\s*(\d{1,2})\s+(\S.{1,60}?)\s+(\d{1,3})\s*$", re.M)
LETTERS = re.compile(r"[A-Za-z]")
# "1.2 Cubics 5" — sub-sections, deliberately not chapters
SUB = re.compile(r"^\s*\d{1,2}\.\d", re.M)
HEAD = re.compile(r"^#{1,4}\s*(.+?)\s*$", re.M)
NOISE = re.compile(r"end-of-chapter|cross-topic|review exercise|practice exam|"
                   r"answers|glossary|index|acknowledge", re.I)


def pages(md_dir):
    out = {}
    for f in sorted(os.listdir(md_dir)):
        m = re.match(r"page_(\d+)\.md$", f)
        if m:
            out[int(m.group(1))] = open(os.path.join(md_dir, f),
                                        encoding="utf-8").read()
    return out


def find_contents(pg, limit=40, need=3):
    """Pages that look like a table of contents: several 'Title  NNN' lines.

    A book's contents runs over several pages and each carries only a handful
    of chapter lines — the rest are sub-sections. Requiring many chapter lines
    on one page finds the middle page and misses the rest, so the bar is low
    and neighbours of a hit are pulled in as well.
    """
    hit = set()
    for n in sorted(pg)[:limit]:
        chapters = [m for m in LINE.finditer(pg[n]) if not SUB.match(m.group(0))]
        if len(chapters) >= need:
            hit.add(n)
    for n in sorted(hit):
        for m in (n - 1, n + 1):
            if m in pg and m <= limit:
                chapters = [x for x in LINE.finditer(pg[m]) if not SUB.match(x.group(0))]
                if chapters or SUB.search(pg[m]):
                    hit.add(m)
    return sorted(hit)


def end_matter_page(pg, contents_pages, after):
    """Printed page of the first end-matter entry after the last chapter.

    Without it the final chapter swallows the answers, glossary and index.
    """
    best = None
    for n in contents_pages:
        for ln in pg[n].split("\n"):
            if not NOISE.search(ln):
                continue
            m = re.search(r"(\d{1,3})\s*$", ln.strip())
            if m:
                v = int(m.group(1))
                if v > after and (best is None or v < best):
                    best = v
    return best


def parse_chapters(pg, contents_pages):
    seen, out = set(), []
    for n in contents_pages:
        for m in LINE.finditer(pg[n]):
            if SUB.match(m.group(0)):
                continue
            num, title, page = int(m.group(1)), m.group(2).strip(), int(m.group(3))
            if NOISE.search(title) or num in seen:
                continue
            if len(LETTERS.findall(title)) < 3:
                continue
            seen.add(num)
            out.append({"chapter": num, "title": title, "printed": page})
    out.sort(key=lambda c: c["chapter"])

    # A page number that runs into the title is the commonest OCR damage here:
    # "4 Matrices 1 58" comes back as "4 Matrices 158", and 158 sits between
    # chapter 3's page 45 and chapter 5's page 93 in no sensible way. Chapter
    # pages only ever increase, so peel leading digits until the value fits.
    for i, c in enumerate(out):
        lo = out[i - 1]["printed"] if i else 0
        hi = out[i + 1]["printed"] if i + 1 < len(out) else 10 ** 6
        if lo < c["printed"] < hi:
            continue
        s = str(c["printed"])
        for k in range(1, len(s)):
            v = int(s[k:])
            if lo < v < hi:
                c["printed"], c["title"] = v, (c["title"] + " " + s[:k]).strip()
                c["repaired"] = True
                break
    return out


def measure_offset(pg, chapters, span=None):
    """PDF page minus printed page, taken from chapters we can actually locate."""
    votes, evidence = Counter(), {}
    for c in chapters:
        key = re.sub(r"[^a-z]+", " ", c["title"].lower()).strip()
        if len(key) < 6:
            continue
        for n, text in pg.items():
            head = text[:700]
            for h in HEAD.finditer(head):
                ht = re.sub(r"[^a-z]+", " ", h.group(1).lower()).strip()
                if key and (key in ht or ht in key) and abs(len(ht) - len(key)) < 12:
                    d = n - c["printed"]
                    if 0 <= d <= 60:
                        votes[d] += 1
                        evidence.setdefault(d, []).append((c["chapter"], c["printed"], n))
                    break
    return votes, evidence


def main(md_dir, out="chapters_proposed.json", syllabus=None):
    pg = pages(md_dir)
    if not pg:
        sys.exit(f"{md_dir} 里没有 page_NNNN.md")
    total = max(pg)
    cps = find_contents(pg)
    if not cps:
        sys.exit("前 40 页里找不到目录页 —— 这本要另想办法")
    print(f"{md_dir}: {total} 页,目录在 PDF p{cps}")

    chapters = parse_chapters(pg, cps)
    if not chapters:
        sys.exit("目录页解析不出章节行")
    print(f"目录里读到 {len(chapters)} 章:第 {chapters[0]['chapter']} 到 "
          f"第 {chapters[-1]['chapter']} 章")
    gaps = [c["chapter"] for i, c in enumerate(chapters)
            if c["chapter"] != chapters[0]["chapter"] + i]
    if gaps:
        print(f"⚠️  章号不连续,缺的位置在 {gaps[:6]}")
    fixed = [c["chapter"] for c in chapters if c.get("repaired")]
    if fixed:
        print(f"修正了页码与标题粘连的章:{fixed}")

    votes, evidence = measure_offset(pg, chapters)
    if not votes:
        sys.exit("对不上任何一章的正文开头,没法确定印刷页与 PDF 页的偏移")
    off, n = votes.most_common(1)[0]
    print(f"\n印刷页 -> PDF 页 偏移 = +{off}  ({n} 章独立印证)")
    for ch, pr, pdfp in evidence[off][:6]:
        print(f"    第 {ch:>2} 章  印刷 p{pr:<4} = PDF p{pdfp}")
    others = [(d, c) for d, c in votes.most_common() if d != off]
    if others and others[0][1] >= n * 0.5:
        print(f"⚠️  还有别的偏移得到不少支持:{others[:3]} —— 人工看一眼")

    rows = []
    for i, c in enumerate(chapters):
        start = c["printed"] + off
        if i + 1 < len(chapters):
            end = chapters[i + 1]["printed"] + off - 1
        else:
            tail = end_matter_page(pg, cps, c["printed"])
            end = (tail + off - 1) if tail else total
        if start > total:
            print(f"⚠️  第 {c['chapter']} 章算出来在 p{start},超过全书 {total} 页,丢弃")
            continue
        rows.append({"chapter": c["chapter"], "title": c["title"],
                     "page_from": start, "page_to": min(end, total),
                     "printed_from": c["printed"]})
    json.dump(rows, open(out, "w"), ensure_ascii=False, indent=1)

    print(f"\n{'章':<4}{'PDF 页范围':<16}{'页数':>5}  标题")
    for r in rows:
        print(f"{r['chapter']:<4}p{r['page_from']}-{r['page_to']:<10}"
              f"{r['page_to']-r['page_from']+1:>5}  {r['title'][:46]}")
    print(f"\n-> {out}")
    print("核对无误后:\n  python3 split_chapters.py <toc.json::书名> "
          f"{md_dir} <out_dir> --table {out} --prefix <前缀>")


if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    if not a:
        sys.exit(__doc__)
    g = lambda k: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else None
    main(a[0], a[1] if len(a) > 1 else "chapters_proposed.json", g("--syllabus"))
