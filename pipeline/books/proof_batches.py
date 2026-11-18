#!/usr/bin/env python3
"""Proof-read OCR'd textbook pages against the original pages, through sub-agents,
and keep the corrections as replayable find/replace lines.

    python3 pipeline/books/proof_batches.py plan edx_ial_phy1 edx_ial_phy2 [--size 20] [--out run1] [--all-pages]
    python3 pipeline/books/proof_batches.py verify raw/book_proof/run1/out/batch_01.json
    python3 pipeline/books/proof_batches.py apply [--write]

plan    takes the pages of the books' chapters (data/books/<book>/*.md, one
        `<!-- page N -->` segment per PDF page) that hold a formula (--all-pages:
        every page), renders each from raw/textbooks/<book>.pdf to
        raw/book_proof/pages/, and writes one prompt file per batch,
        raw/book_proof/<run>/batch_NN.md. A sub-agent writes
        raw/book_proof/<run>/out/batch_NN.json:
        [{"book", "page", "old", "new", "why"}], one line per correction.
verify  checks one result file: `old` occurs exactly once in that page's segment,
        figures (<img ...>) are left as they are, and the page's formulas all
        render in KaTeX after the change (or at least no fewer than before).
apply   appends what passes to pipeline/books/book_fixes.jsonl and, with --write,
        replays that file into the chapter files. A line whose `old` is no longer
        in its page (already applied, or the chapter was rebuilt differently) is
        skipped. After a rebuild of the chapters (split_chapters.py) run apply
        --write again.

Why only pages with formulas by default: the OCR reads prose well; what it gets
wrong is symbols (v read as V, a as α), sub- and superscripts, and LaTeX that does
not render (docs/pipeline.md, "Edexcel 物理教材").
"""
import argparse
import glob
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import pymupdf  # noqa: E402

from lib import paths  # noqa: E402
from pipeline.text import check_latex  # noqa: E402

WORK = os.path.join(paths.RAW, "book_proof")
PAGES = os.path.join(WORK, "pages")
FIXES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "book_fixes.jsonl")
MARK = re.compile(r"<!-- page (\d+) -->\n")
FORMULA = re.compile(r"(?<!\\)\$")
IMG = re.compile(r"<img [^>]*>|!\[[^\]]*\]\([^)]*\)")


def rel(p):
    return os.path.relpath(p, paths.ROOT)


def chapter_files(book):
    return sorted(glob.glob(os.path.join(paths.BOOKS, book, f"{book}_ch*.md")))


def segments(text):
    """[(page, start, end)] of each `<!-- page N -->` segment, end exclusive."""
    marks = list(MARK.finditer(text))
    return [(int(m.group(1)), m.end(), marks[k + 1].start() if k + 1 < len(marks) else len(text))
            for k, m in enumerate(marks)]


def page_index(book):
    """{page: (chapter file, start, end)} for one book."""
    out = {}
    for f in chapter_files(book):
        text = open(f, encoding="utf-8").read()
        for page, a, b in segments(text):
            out[page] = (f, a, b)
    return out


def page_text(book, page):
    f, a, b = page_index(book)[page]
    return open(f, encoding="utf-8").read()[a:b]


def katex_errors(text):
    katex = os.path.join(paths.ASSETS, "vendor", "katex", "katex.min.js")
    out = subprocess.run(["node", "-e", check_latex.JS, katex], input=json.dumps([["p", "text", text]]),
                         capture_output=True, text=True, check=True).stdout
    return [(err, tex) for _i, _c, err, tex in json.loads(out)]


PROMPT = """# 教材页校对批次 {n}

下面每一页都是教材 PDF 的一页经 OCR 得到的 Markdown。请打开每页的原页图(用 Read),逐行对照，只改 OCR 读错的地方。

## 要改的
- 公式与正文里读错的字母和符号(大小写 v/V、s/S;a 读成 α;ρ、λ、μ、Ω、θ 等希腊字母;× 与 x;− 与 -)。
- 丢失或多出的上下标、指数、单位前缀(如 10^{{-3}}、m s^{{-2}}、m², μF)。
- 读错的数字、小数点、正负号。
- KaTeX 无法渲染的 LaTeX(括号不配对、多余的 `}}`、`\\text` 写错等)。
- 被读成下标或公式的普通词(如 `{{}}_{{strain}}` 实为粗体关键词 **strain**,改回正文)。
- 漏掉的词句：原页有、Markdown 里没有的正文句子，补在对应位置。

## 不要改的
- 措辞、标点风格、段落顺序、标题层级、表格样式：与原页意思一致就不动。
- `<img ...>` 标签与插图：原样保留。图里的文字不需要写出。
- 页眉、页脚、页码：已经去掉，不要加回。
- 侧栏(Exam hint、Learning tip 等)的位置：顺序与原页不同也不动。
- 没有错的页：不写任何条目。

## 输出
把结果写成 JSON 数组到 `{out}`,每处改动一项:
```json
[{{"book": "edx_ial_phy1", "page": 23, "old": "原文中要替换的一段", "new": "替换后的文字", "why": "一句话说明"}}]
```
- `old` 必须从下面给出的该页 Markdown 中**逐字复制**,并且在该页中只出现一次(太短就多带几个字)。
- 一处错误一项；同一行有几处错误可以合成一项。
- 写完运行 `python3 pipeline/books/proof_batches.py verify {out}`,按报告修正直到「全部通过」。

只写这一个 JSON 文件，不改其他任何文件。

"""


def plan(a):
    out_dir = os.path.join(WORK, a.out)
    os.makedirs(os.path.join(out_dir, "out"), exist_ok=True)
    os.makedirs(PAGES, exist_ok=True)
    todo = []
    for book in a.books:
        pdf = os.path.join(paths.TEXTBOOKS, f"{book}.pdf")
        if not os.path.exists(pdf):
            sys.exit(f"没有 {rel(pdf)}")
        doc = pymupdf.open(pdf)
        for page, (f, s, e) in sorted(page_index(book).items()):
            text = open(f, encoding="utf-8").read()[s:e]
            if not a.all_pages and not FORMULA.search(text):
                continue
            png = os.path.join(PAGES, f"{book}_p{page:04d}.png")
            if not os.path.exists(png) or not os.path.getsize(png):
                doc[page - 1].get_pixmap(dpi=110).save(png)
            todo.append((book, page, f, text))
    for n, b in enumerate(range(0, len(todo), a.size), 1):
        out = os.path.join(out_dir, "out", f"batch_{n:02d}.json")
        parts = [PROMPT.format(n=n, out=rel(out))]
        for book, page, f, text in todo[b:b + a.size]:
            parts.append(f"## {book} 第 {page} 页(PDF 页码)\n\n原页图:{rel(os.path.join(PAGES, f'{book}_p{page:04d}.png'))}"
                         f"\n章节文件:{rel(f)}\n\n````markdown\n{text.strip()}\n````\n")
        path = os.path.join(out_dir, f"batch_{n:02d}.md")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("\n".join(parts))
        print(f"{rel(path)}  {len(todo[b:b + a.size])} 页")
    print(f"共 {len(todo)} 页")


def check(items):
    """(lines that pass, report)."""
    ok, report, pages = [], [], {}
    for x in items:
        key = (x.get("book"), x.get("page"))
        if key not in pages:
            try:
                pages[key] = page_text(*key)
            except (KeyError, TypeError):
                report.append(f"{key}: 没有这一页")
                pages[key] = None
        if pages[key] is None:
            continue
        old, new = x.get("old") or "", x.get("new")
        n = pages[key].count(old)
        if not old or new is None or old == new:
            report.append(f"{key}: old/new 为空或相同:{old[:40]!r}")
        elif n != 1:
            report.append(f"{key}: old 在该页出现 {n} 次(应为 1):{old[:60]!r}")
        elif IMG.findall(old) != IMG.findall(new):
            report.append(f"{key}: 改动了插图标签:{old[:60]!r}")
        else:
            pages[key] = pages[key].replace(old, new)
            ok.append({"book": key[0], "page": key[1], "old": old, "new": new, "why": x.get("why", "")})
    for key, text in pages.items():
        if text is None:
            continue
        before = {tex for _e, tex in katex_errors(page_text(*key))}
        for err, tex in katex_errors(text):
            if tex not in before:                # broken by the change; one that was broken already may stay
                report.append(f"{key}: 公式无法渲染({err[:60]}):{tex[:80]!r}")
    bad = {r.split(":")[0] for r in report}
    return [o for o in ok if str((o["book"], o["page"])) not in bad], report


def verify(a):
    ok, report = check(json.load(open(a.file, encoding="utf-8")))
    for r in report:
        print(r)
    print("全部通过" if not report else f"{len(report)} 个问题")
    print(f"{len(ok)} 条可用")


def replay(write):
    done = skipped = 0
    texts, where = {}, {}
    for line in open(FIXES, encoding="utf-8") if os.path.exists(FIXES) else []:
        f = json.loads(line)
        if f["book"] not in where:
            where[f["book"]] = {page: path for page, (path, _s, _e) in page_index(f["book"]).items()}
        path = where[f["book"]].get(f["page"])
        if not path:
            skipped += 1
            continue
        text = texts.get(path) or open(path, encoding="utf-8").read()
        seg = [(s, e) for page, s, e in segments(text) if page == f["page"]]
        s, e = seg[0]
        seg, old, new = text[s:e], f["old"], f["new"]
        n = seg.count(old)
        if old in new and n and n == seg.count(new):
            continue                        # applied: "inding" -> "Finding" leaves "inding" inside "Finding"
        if n != 1:
            skipped += new not in seg       # gone and its replacement there: applied
            continue
        texts[path] = text[:s] + text[s:e].replace(f["old"], f["new"]) + text[e:]
        done += 1
    if write:
        for path, text in texts.items():
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(text)
    print(f"{'写入' if write else '待写入'} {done} 处;找不到原文、跳过 {skipped} 处")


def apply(a):
    have = set()
    if os.path.exists(FIXES):
        for line in open(FIXES, encoding="utf-8"):
            f = json.loads(line)
            have.add((f["book"], f["page"], f["old"]))
    added = 0
    with open(FIXES, "a", encoding="utf-8") as out:
        for path in sorted(glob.glob(os.path.join(WORK, "*", "out", "batch_*.json"))):
            items = [x for x in json.load(open(path, encoding="utf-8"))
                     if (x.get("book"), x.get("page"), x.get("old")) not in have]   # recorded: checked then
            if not items:
                continue
            ok, report = check(items)
            for r in report:
                print(f"{rel(path)}: {r}")
            for f in ok:
                if (f["book"], f["page"], f["old"]) in have:
                    continue
                out.write(json.dumps(f, ensure_ascii=False) + "\n")
                have.add((f["book"], f["page"], f["old"]))
                added += 1
    print(f"追加 {added} 条到 {rel(FIXES)}")
    replay(a.write)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("plan")
    p.add_argument("books", nargs="+")
    p.add_argument("--size", type=int, default=20)
    p.add_argument("--out", default="run1")
    p.add_argument("--all-pages", action="store_true")
    p = sub.add_parser("verify")
    p.add_argument("file")
    p = sub.add_parser("apply")
    p.add_argument("--write", action="store_true")
    a = ap.parse_args()
    {"plan": plan, "verify": verify, "apply": apply}[a.cmd](a)


if __name__ == "__main__":
    main()
