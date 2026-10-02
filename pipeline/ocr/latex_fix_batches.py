#!/usr/bin/env python3
"""Correct the formulas KaTeX cannot render (check_latex.py) against the original
pages, through sub-agents; the corrections go to ms_fixes.jsonl.

    python3 pipeline/ocr/latex_fix_batches.py plan [--batches 9] [EXTRA_ID ...]
    python3 pipeline/ocr/latex_fix_batches.py verify raw/latex_fix/out/batch_01.json
    python3 pipeline/ocr/latex_fix_batches.py apply

plan    renders the pages each question sits on (mark scheme pages for ms_latex,
        question paper pages for question_latex) to raw/latex_fix/pages/ and writes
        one prompt file per batch, raw/latex_fix/batch_NN.md. A general-purpose
        sub-agent reads it and writes raw/latex_fix/out/batch_NN.json:
        [{"id", "column", "find", "replace", "why"}].
verify  applies one result file to a copy of the texts and re-runs the check: every
        `find` must occur once, and the question's formulas must all render.
apply   checks every result file the same way and appends the corrections that pass
        to pipeline/ocr/ms_fixes.jsonl. Then run apply_ms_fixes.py --write and
        split_parts.py.
"""
import argparse
import glob
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import pymupdf  # noqa: E402

from lib import db, paths  # noqa: E402
from pipeline.text import check_latex  # noqa: E402

WORK = os.path.join(paths.RAW, "latex_fix")
OUT = os.path.join(WORK, "out")
PAGES = os.path.join(WORK, "pages")
FIXES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ms_fixes.jsonl")
COLUMNS = ("ms_latex", "question_latex")

TASK = """# 公式更正批次 {n}

题库中下列题目的公式无法被 KaTeX 渲染,原因多是识别错误:`$` 插在公式中间、括号不配对、
`{{{{ }}}}` 双括号、`\\left` 缺少配对、公式被拆成两段等。请对照原页图像逐题更正。

## 要求

1. 每题先用 Read 打开列出的原页图像,找到这道题(评分细则页按左列题号找),再读下面给出的当前文本。
2. 只改有错的地方,使公式与原页一致并能被 KaTeX 渲染。同一题里其他与原页不符之处也一并更正:
   公式中的数字、符号、分式写错,题干中的乱码、截断或重复的句子。与原页一致的措辞、评分代码和行序不动。
3. 评分细则每行的格式是 `答案  |  评分代码  |  说明`,列之间是「两个空格 + | + 两个空格」,
   必须保持;单元格内换行写 `<br>`,不要写真换行。公式中的竖线(绝对值、条件概率)照常写 `|`,
   两侧不要同时留两个空格。
4. 公式一律放在 `$ ... $` 中,每个 `$` 都要配对。美元金额写成 `\\$`。不要用 `\\boldmath`、`\\sech`
   这类 KaTeX 不支持的命令(`\\sech` 写成 `\\operatorname{{sech}}`,粗体用 `\\mathbf`)。
5. 每处更正写成一条 `{{"id", "column", "find", "replace", "why"}}`:
   - `find` 是当前文本中**只出现一次**的连续片段,尽量短但足以唯一定位;
   - `replace` 是更正后的片段;
   - `why` 用一句中文说明改了什么,例如「按原页把 10/3 改为 20/3」。
6. 全部题目写完后,把 JSON 数组写到 `{out}`,然后运行
   `python3 pipeline/ocr/latex_fix_batches.py verify {out}`。
   它会报告找不到或不唯一的 `find`,以及仍无法渲染的公式;按报告修改,直到它输出「全部通过」。
   确实无法从原页判断的题,在 `why` 里写明原因,不要猜。
7. 只写这一个 JSON 文件,不改数据库,不改其他文件。最后的回复只报告题数与更正条数。

## 题目
"""


def _pdf(name, sub):
    for d in (paths.PAPERS, os.path.join(paths.RAW, sub), paths.RAW):
        p = os.path.join(d, name or "")
        if name and os.path.isfile(p):
            return p
    return None


def scheme_pages(doc, q, col=0.13):
    """Pages of a mark scheme holding question q: from the first page whose left
    column carries its label to the page where question q+1 starts. Pages before
    the table (headed "Question") are skipped."""
    first = last = nxt = None
    lab = re.compile(rf"^{q}(?:\(|$)")
    nlab = re.compile(rf"^{q + 1}(?:\(|$)")
    table = False                        # the cover, notes and abbreviations come first
    for page in doc:
        m = page.rotation_matrix          # word boxes are unrotated; the column is on the page as shown
        left = [w[4] for w in page.get_text("words") if (pymupdf.Rect(w[:4]) * m).x0 < page.rect.width * col]
        table = table or "Question" in left
        if not table:
            continue
        if any(lab.match(t) for t in left):
            first = page.number if first is None else first
            last = page.number
        if first is not None and nxt is None and any(nlab.match(t) for t in left):
            nxt = page.number
    if first is None:                    # some schemes set the question column further in
        return scheme_pages(doc, q, 0.25) if col < 0.25 else []
    end = max(last, nxt if nxt is not None else last)
    return list(range(first, min(end, first + 7) + 1))


def render(path, pages, stem):
    out = []
    with pymupdf.open(path) as doc:
        for n in pages:
            f = os.path.join(PAGES, f"{stem}_p{n + 1}.png")
            if not os.path.exists(f):
                doc[n].get_pixmap(dpi=110, colorspace=pymupdf.csGRAY).save(f)
            out.append(f)
    return out


def plan(a):
    bad = check_latex.check()
    for x in a.ids:                       # named questions are added even if they render
        bad.setdefault(x, [])
    os.makedirs(PAGES, exist_ok=True)
    os.makedirs(OUT, exist_ok=True)
    con = db.connect()
    items = []
    for qid in sorted(bad):
        r = con.execute("SELECT * FROM questions WHERE id = ?", (qid,)).fetchone()
        cols = sorted({e["column"] for e in bad[qid]}) or ["ms_latex"]
        images = []
        for col in cols:
            if col == "ms_latex":
                p = _pdf(r["ms_pdf"], "ms")
                if p:
                    with pymupdf.open(p) as d:
                        pages = scheme_pages(d, r["q"])
                    images += render(p, pages, os.path.splitext(os.path.basename(r["ms_pdf"]))[0])
            else:
                p = _pdf(r["qp_pdf"], "pdf")
                pages = [n - 1 for n in json.loads(r["qp_pages"] or "[]")]
                if p and pages:
                    images += render(p, pages, os.path.splitext(os.path.basename(r["qp_pdf"]))[0])
        items.append((qid, cols, images, bad[qid], r))
    size = -(-len(items) // a.batches)
    for b in range(0, len(items), size):
        n = b // size + 1
        out = os.path.relpath(os.path.join(OUT, f"batch_{n:02d}.json"), paths.ROOT)
        text = [TASK.format(n=n, out=out)]
        for qid, cols, images, errs, r in items[b:b + size]:
            text.append(f"\n### {qid}\n")
            text.append("原页图像:" + (", ".join(os.path.relpath(i, paths.ROOT) for i in images)
                                    if images else "无(按 LaTeX 语法更正)") + "\n")
            for e in errs:
                text.append(f"- {e['column']} 报错:{e['error']}\n  公式:`{e['tex'][:300]}`\n")
            for col in cols:
                text.append(f"\n当前 {col}:\n\n```\n{r[col]}\n```\n")
        with open(os.path.join(WORK, f"batch_{n:02d}.md"), "w", encoding="utf-8") as f:
            f.write("".join(text))
        print(f"batch_{n:02d}.md  {len(items[b:b + size])} 题")


def verify_file(path):
    """(passing fixes, report lines) for one result file."""
    fixes = json.load(open(path, encoding="utf-8"))
    con = db.connect()
    texts, report, ok = {}, [], []
    for f in fixes:
        if f.get("column") not in COLUMNS:
            report.append(f"{f.get('id')}: column 只能是 {COLUMNS}")
            continue
        key = (f["id"], f["column"])
        if key not in texts:
            row = con.execute(f"SELECT {f['column']} FROM questions WHERE id = ?", (f["id"],)).fetchone()
            if not row:
                report.append(f"{f['id']}: 没有这道题")
                continue
            texts[key] = row[0] or ""
        n = texts[key].count(f["find"])
        if n != 1:
            report.append(f"{f['id']} {f['column']}: find 出现 {n} 次:{f['find'][:80]!r}")
            continue
        texts[key] = texts[key].replace(f["find"], f["replace"])
        ok.append(f)
    left = check_latex.check({i for i, _ in texts}, texts)
    for i, errs in left.items():
        for e in errs:
            report.append(f"{i} {e['column']}: 仍无法渲染({e['error'][:80]}):{e['tex'][:120]!r}")
    failed = set(left)
    return [f for f in ok if f["id"] not in failed], report


def verify(a):
    ok, report = verify_file(a.file)
    print("\n".join(report) if report else "全部通过")
    print(f"{len(ok)} 条可用")


def apply(a):
    have = set()
    if os.path.exists(FIXES):
        for line in open(FIXES, encoding="utf-8"):
            f = json.loads(line)
            have.add((f["id"], f["column"], f["find"]))
    added = 0
    with open(FIXES, "a", encoding="utf-8") as out:
        for path in sorted(glob.glob(os.path.join(OUT, "batch_*.json"))):
            ok, report = verify_file(path)
            for line in report:
                print(f"{os.path.basename(path)}: {line}")
            for f in ok:
                if (f["id"], f["column"], f["find"]) in have:
                    continue
                out.write(json.dumps({k: f[k] for k in ("id", "column", "find", "replace", "why")},
                                     ensure_ascii=False) + "\n")
                added += 1
    print(f"追加 {added} 条到 {os.path.relpath(FIXES, paths.ROOT)};"
          "接着运行 apply_ms_fixes.py --write 与 split_parts.py")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("plan")
    p.add_argument("ids", nargs="*")
    p.add_argument("--batches", type=int, default=9)
    p.set_defaults(fn=plan)
    p = sub.add_parser("verify")
    p.add_argument("file")
    p.set_defaults(fn=verify)
    sub.add_parser("apply").set_defaults(fn=apply)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
