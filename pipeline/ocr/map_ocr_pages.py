#!/usr/bin/env python3
"""Work out which PDF page each OCR'd markdown file actually is.

Counting files is not enough to tell whether an OCR run is complete. A run can
produce a file for every fourth page and still look continuous — the surviving
pages march through the whole book, so the last one really is about complex
numbers, and nothing about the output says three quarters is missing.

So match on content instead. Pure Maths 2&3 and most of these books keep a
usable text layer for prose (only the formulas are lost), which is enough to
line each markdown file up against the PDF page it came from. The mapping then
says plainly whether it is 1,2,3,4... or 4,8,12,16...

    python3 map_ocr_pages.py <book.pdf> <page_md_dir>

Prints the recovered mapping and, if there is a constant stride, names it.
"""
import os, re, sys
from collections import Counter

try:
    import fitz
except ImportError:
    sys.exit("需要 PyMuPDF:  pip install pymupdf")

WORD = re.compile(r"[a-z]{4,}")
NOISE = re.compile(r"<!--.*?-->|!\[.*?\]\(.*?\)|\$\$?.*?\$\$?|\\[a-zA-Z]+", re.S)


def words(t):
    return Counter(WORD.findall(NOISE.sub(" ", t or "").lower()))


def overlap(a, b):
    if not a or not b:
        return 0.0
    common = sum(min(a[w], b[w]) for w in a.keys() & b.keys())
    return common / max(1, min(sum(a.values()), sum(b.values())))


def main(pdf, md_dir, window=40):
    doc = fitz.open(pdf)
    pdf_words = [words(doc[i].get_text()) for i in range(doc.page_count)]
    usable = sum(1 for w in pdf_words if sum(w.values()) >= 30)
    print(f"{os.path.basename(pdf)}: {doc.page_count} 页,"
          f"其中 {usable} 页文本层可用于比对")
    if usable < doc.page_count * 0.3:
        print("⚠️  这本文本层太差,比对结果不可信(扫描件用不了这个办法)")

    files = sorted(f for f in os.listdir(md_dir) if re.match(r"page_\d+\.md$", f))
    if not files:
        sys.exit(f"{md_dir} 里没有 page_NNNN.md")
    print(f"{md_dir}: {len(files)} 个 markdown\n")

    # A page's own text is the only reliable anchor, so search the whole book
    # rather than a window around the last hit: once a window stops advancing
    # every later file piles onto the same page and the stride looks random.
    # Ordering is restored afterwards instead.
    STRONG = 0.5
    hits = []
    for f in files:
        w = words(open(os.path.join(md_dir, f), encoding="utf-8").read())
        if sum(w.values()) < 30:
            hits.append((f, None, 0.0)); continue
        best, bestp = 0.0, None
        for p in range(doc.page_count):
            s = overlap(w, pdf_words[p])
            if s > best:
                best, bestp = s, p
        hits.append((f, (bestp + 1) if bestp is not None else None, best))

    # only confident, forward-moving matches are evidence about the stride
    matched, last = [], 0
    for f, p, s in hits:
        if p and s >= STRONG and p >= last:
            matched.append((f, p)); last = p
    print(f"{'markdown':<16}{'对应 PDF 页':>12}{'匹配度':>9}")
    for f, p, s in hits[:12]:
        print(f"{f:<16}{(p if p else '?'):>12}{s:>9.2f}")
    if len(hits) > 12:
        print(f"   ... 共 {len(hits)} 个")

    weak = sum(1 for _f, p, s in hits if p and s < STRONG)
    print(f"\n高置信匹配 {len(matched)}/{len(files)} 个"
          + (f",另有 {weak} 个匹配度偏低(多半是公式页,文本层本来就残)" if weak else ""))
    if len(matched) < 3:
        print("匹配太少,没法判断。")
        return

    strides = Counter(matched[i + 1][1] - matched[i][1]
                      for i in range(len(matched) - 1))
    top, n = strides.most_common(1)[0]
    print(f"相邻文件的页码间隔:{dict(strides.most_common(5))}")
    covered = {p for _f, p in matched}
    lo, hi = min(covered), max(covered)
    print(f"高置信匹配落在 p{lo}–p{hi}")

    if top == 1 and n > len(matched) * 0.7:
        print("\n✅ 1:1 连续 —— OCR 是完整的,之前判断错了。")
    elif top > 1:
        print(f"\n❌ 每 {top} 页只留下 1 页 —— 丢了约 "
              f"{(1 - 1/top)*100:.0f}% 的正文。")
        print("   原因几乎可以肯定是:PaddleOCR 一行 JSONL 里返回多页,")
        print("   而写文件时几页共用同一个文件名,只有最后一页留下来了。")
        print("   (ocr_book.py 里的 collect() 是逐个 result 展开的,没有这个问题)")
    else:
        print("\n⚠️  间隔不规则,得人工看一眼。")


if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    if len(a) < 2:
        sys.exit(__doc__)
    main(a[0], a[1])
