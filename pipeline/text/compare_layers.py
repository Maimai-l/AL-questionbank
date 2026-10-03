#!/usr/bin/env python3
"""Measure the PDF text layer against the OCR reading, page by page.

The question this settles: for a page that *has* a text layer, is that layer
good enough, or does OCR read it materially better? Guessing has already been
expensive — the maths mark schemes looked fine until it turned out `pdftotext`
had dropped every equals sign, while for Computer Science the same OCR flattened
clean tables and made things worse. Neither result was predictable from the
outside.

So both readings are on disk and this compares them on things that can be
counted:

  equations      '=' and friends, plus LaTeX fraction/root/integral commands.
                 A maths page with none of these has lost its mathematics.
  orphans        share of one-character tokens. A stripped formula is almost
                 nothing else; real prose has very few.
  structure      markdown tables and figures — content the text layer cannot
                 express at all.
  degenerate     the OCR failure mode: repetition loops, hallucinated scripts.
                 OCR is not automatically the better reading.

Output is a verdict per book plus a side-by-side sample to actually read,
because a metric that disagrees with your eyes is a metric to distrust.

    python3 compare_layers.py <pages_dir> [--samples 6] [--out compare.md]
"""
import os, re, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))          # 项目根目录
from pipeline.text.audit_text import orphan_ratio, degenerate

EQ = re.compile(r"[=≡≈≤≥<>]|\\(?:frac|sqrt|int|sum|lim|cdot|times|le|ge|ne)\b")
LATEX = re.compile(r"\\[a-zA-Z]+|\$")
TABLE = re.compile(r"^\s*\|.*\|\s*$", re.M)
IMG = re.compile(r"!\[[^\]]*\]\([^)]+\)")
WORD = re.compile(r"[A-Za-z][A-Za-z\-']*")
HEAD = re.compile(r"^#{1,4}\s+\S", re.M)
COMMENT = re.compile(r"^<!--.*?-->\s*", re.S)


def stats(t):
    t = COMMENT.sub("", t or "")
    w = WORD.findall(t)
    return {"chars": len(t.strip()), "words": len(w),
            "eq": len(EQ.findall(t)), "latex": len(LATEX.findall(t)),
            "tables": len(TABLE.findall(t)), "imgs": len(IMG.findall(t)),
            "heads": len(HEAD.findall(t)),
            "orphan": round(orphan_ratio(t), 3) if len(w) >= 20 else 0.0,
            "degenerate": degenerate(t)}


def verdict(a, b):
    """(winner, why) for one page: 'text', 'ocr' or 'tie'."""
    if b["degenerate"] and not a["degenerate"]:
        return "text", "OCR 退化"
    if a["chars"] < 100 <= b["chars"]:
        return "ocr", "文本层是空的"
    if b["chars"] < 100 <= a["chars"]:
        return "text", "OCR 是空的"
    if a["chars"] < 100 and b["chars"] < 100:
        return "tie", "两边都几乎没内容"
    # the failure that actually matters: mathematics silently gone
    if a["eq"] == 0 and b["eq"] >= 2:
        return "ocr", "文本层没有等号"
    if a["orphan"] > 0.35 and b["orphan"] < a["orphan"] - 0.1:
        return "ocr", "文本层被打散成单字符"
    if b["tables"] + b["imgs"] > 0 and a["tables"] + a["imgs"] == 0:
        return "ocr", "表格/图只有 OCR 读出来了"
    if b["eq"] > a["eq"] * 1.5 and b["eq"] - a["eq"] >= 3:
        return "ocr", "公式明显更全"
    if a["words"] > b["words"] * 1.3 and a["words"] - b["words"] > 40:
        return "text", "OCR 漏了大段文字"
    return "tie", ""


def read(p):
    try:
        return open(p, encoding="utf-8").read()
    except Exception:
        return ""


def compare_book(d, samples=6):
    td, od = os.path.join(d, "text"), os.path.join(d, "ocr")
    if not (os.path.isdir(td) and os.path.isdir(od)):
        return None
    both = sorted(set(os.listdir(td)) & set(os.listdir(od)))
    both = [f for f in both if re.match(r"page_\d+\.md$", f)]
    if not both:
        return None

    rows, tally, reasons = [], {"text": 0, "ocr": 0, "tie": 0}, {}
    for f in both:
        a, b = stats(read(os.path.join(td, f))), stats(read(os.path.join(od, f)))
        w, why = verdict(a, b)
        tally[w] += 1
        if why:
            reasons[why] = reasons.get(why, 0) + 1
        rows.append((f, a, b, w, why))

    # pages where OCR wins for a substantive reason make the best samples
    interesting = [r for r in rows if r[3] == "ocr" and r[4]]
    step = max(1, len(interesting) // max(1, samples))
    picked = interesting[::step][:samples] or rows[::max(1, len(rows)//samples)][:samples]
    return {"dir": d, "pages": len(both), "tally": tally,
            "reasons": reasons, "rows": rows, "samples": picked}


def main(root, samples=6, out="compare.md"):
    books = [os.path.join(root, x) for x in sorted(os.listdir(root))
             if os.path.isdir(os.path.join(root, x))]
    results = [r for r in (compare_book(b, samples) for b in books) if r]
    if not results:
        sys.exit(f"{root} 下没有同时含 text/ 和 ocr/ 的书目录 —— "
                 f"先跑 build_pages.py")

    print(f"{'书':<44}{'比对页':>7}{'OCR 更好':>10}{'文本层更好':>12}{'打平':>7}")
    for r in results:
        t = r["tally"]
        print(f"{os.path.basename(r['dir'])[:42]:<44}{r['pages']:>7}"
              f"{t['ocr']:>10}{t['text']:>12}{t['tie']:>7}")
    print()
    for r in results:
        if not r["reasons"]:
            continue
        print(f"{os.path.basename(r['dir'])[:50]}")
        for why, n in sorted(r["reasons"].items(), key=lambda x: -x[1]):
            print(f"    {n:>5} 页  {why}")

    with open(out, "w", encoding="utf-8") as f:
        f.write("# 文本层 vs OCR 逐页比对\n\n")
        for r in results:
            t = r["tally"]
            f.write(f"## {os.path.basename(r['dir'])}\n\n")
            f.write(f"- 比对 {r['pages']} 页:OCR 更好 **{t['ocr']}**,"
                    f"文本层更好 **{t['text']}**,打平 {t['tie']}\n")
            for why, n in sorted(r["reasons"].items(), key=lambda x: -x[1]):
                f.write(f"  - {why}:{n} 页\n")
            f.write("\n")
            for fn, a, b, w, why in r["samples"]:
                f.write(f"### {fn} — 判 {w}({why})\n\n")
                f.write("| | 字符 | 词 | 等号/公式 | LaTeX | 表 | 图 | 孤立单字 |\n"
                        "|---|---|---|---|---|---|---|---|\n")
                for nm, s in (("文本层", a), ("OCR", b)):
                    f.write(f"| {nm} | {s['chars']} | {s['words']} | {s['eq']} | "
                            f"{s['latex']} | {s['tables']} | {s['imgs']} | "
                            f"{s['orphan']} |\n")
                f.write("\n<details><summary>文本层</summary>\n\n```\n")
                f.write(read(os.path.join(r["dir"], "text", fn))[:1400])
                f.write("\n```\n</details>\n\n<details><summary>OCR</summary>\n\n```\n")
                f.write(read(os.path.join(r["dir"], "ocr", fn))[:1400])
                f.write("\n```\n</details>\n\n")
    print(f"\n带正文样本的详细报告 -> {out}")


if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    if not a:
        sys.exit(__doc__)
    g = lambda k: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else None
    main(a[0], int(g("--samples") or 6), g("--out") or "compare.md")
