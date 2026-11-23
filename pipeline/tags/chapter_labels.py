#!/usr/bin/env python3
"""Label questions with the chapters of a workbook, through sub-agents.

    python3 pipeline/tags/chapter_labels.py examples LABELS.json BOOK
    python3 pipeline/tags/chapter_labels.py plan LABELS.json --set test|bank [--size 35] [--out run1]
    python3 pipeline/tags/chapter_labels.py score LABELS.json --out run1
    python3 pipeline/tags/chapter_labels.py apply LABELS.json --out run1 [--write]

A label table (pipeline/tags/labels_mech.json) names the workbook's chapters and
what each covers. The workbook's own questions are the labelled data: each sits
in a known chapter and names its source paper.

examples  cuts the workbook's OCR'd pages (raw/book_ocr/BOOK/pages, made by
          pipeline/books/ocr_book_pages.py) into questions at each "(9709_s17_qp_41)"
          source mark and assigns each the chapter its page falls in, into
          raw/labels/<table>/examples.json. Questions with no paper as source
          (textbook exercises) only serve as worked examples.
plan      writes prompt files raw/labels/<table>/<run>/batch_NN.md. The prompt shows
          the label table and, as worked examples, the workbook questions from
          2016-2017; --set test asks for labels on the workbook questions from
          2018-2020 (their chapter is known: a test of the method), --set bank on
          the bank's questions of the table's syllabus and component. A
          general-purpose sub-agent writes out/batch_NN.json:
          [{"id", "labels": ["5", "4"]}], the main chapter first.
score     compares a --set test run with the workbook's chapters.
apply     checks a --set bank run and, with --write, puts the labels into the
          questions' tags as "<prefix> <n> <name>" (prefix and names from the
          table), main chapter first, replacing earlier tags with that prefix.
"""
import argparse
import glob
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from lib import db, paths  # noqa: E402

REF = re.compile(r"\((\d{4}_[msw]\d\d_qp_\d\d)\)")
NUM = re.compile(r"(?m)^\s*(\d{1,3})\s*[.．]\s*$")


def work(table):
    return os.path.join(paths.RAW, "labels", os.path.splitext(os.path.basename(table))[0])


def load(table):
    return json.load(open(table, encoding="utf-8"))


def chapter_of(page, labels):
    best = None
    for code, lab in sorted(labels.items(), key=lambda kv: kv[1]["pdf_from"]):
        if page >= lab["pdf_from"]:
            best = code
    return best


QNUM = re.compile(r"(?m)^#{0,4}\s*(\d{1,3})\s*[.．]\s*$")
CHAP = re.compile(r"(?mi)^#{0,4}\s*Chapter\s+(\d+)\b")
SOURCE = re.compile(r"\(([^()\n]*(?:\d{4}_[msw]\d\d_qp_\d\d|第\s*\d+\s*题)[^()\n]*)\)")


def examples(a):
    """Each question runs from its "### N." heading to the next heading (question or
    chapter); its source, "(9709_s17_qp_41)" or "(... Chapter Review Exercise 2-第 8 题)",
    closes it. Numbering restarts at 1 in each chapter, which gives the chapter (the
    "Chapter N" headings are not always read); the contents page numbers check it."""
    spec = load(a.table)
    pages = sorted(glob.glob(os.path.join(paths.RAW, "book_ocr", a.book, "pages", "page_*.md")))
    if not pages:
        sys.exit(f"没有 raw/book_ocr/{a.book}/pages,先运行 ocr_book_pages.py")
    text, starts = "", []
    for p in pages:
        starts.append((len(text), int(re.search(r"page_(\d+)", p).group(1))))
        text += re.sub(r"<[^>]+>", " ", open(p, encoding="utf-8").read()) + "\n"
    page_at = lambda pos: max(n for s, n in starts if s <= pos)
    marks = sorted([(m.start(), "q", m) for m in QNUM.finditer(text)] +
                   [(m.start(), "c", m) for m in CHAP.finditer(text)], key=lambda t: t[0])
    order = sorted(spec["labels"], key=lambda c: spec["labels"][c]["pdf_from"])
    out, chap, last = [], None, 0
    for k, (pos, kind, m) in enumerate(marks):
        if kind == "c":
            continue
        n = int(m.group(1))
        if chap is None or (n == 1 and last != 0):     # numbering restarts in each chapter
            chap = order[0] if chap is None else order[order.index(chap) + 1]
        last = n
        end = marks[k + 1][0] if k + 1 < len(marks) else len(text)
        body = text[m.end():end]
        src = SOURCE.findall(body)
        ref = re.search(r"\d{4}_[msw]\d\d_qp_\d\d", src[-1]) if src else None
        body = SOURCE.sub("", body)
        if chapter_of(page_at(pos), spec["labels"]) not in (chap, order[max(order.index(chap) - 1, 0)]):
            print(f"注意：第 {page_at(pos)} 页第 {n} 题按题号属第 {chap} 章，按目录页码不是")
        out.append({"id": f"wb{len(out) + 1:03d}", "n": n, "chapter": chap,
                    "page": page_at(pos), "source": src[-1].strip() if src else None,
                    "ref": ref.group(0) if ref else None,
                    "year": 2000 + int(ref.group(0)[6:8]) if ref else None,
                    "text": re.sub(r"\n{3,}", "\n\n", body).strip()})
    os.makedirs(work(a.table), exist_ok=True)
    path = os.path.join(work(a.table), "examples.json")
    json.dump(out, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    by = {}
    for x in out:
        by[x["chapter"]] = by.get(x["chapter"], 0) + 1
    print(f"{len(out)} 题 -> {os.path.relpath(path, paths.ROOT)};各章 {dict(sorted(by.items(), key=lambda kv: int(kv[0])))};"
          f"无出处 {sum(1 for x in out if not x['source'])} 题，非真题 {sum(1 for x in out if x['source'] and not x['ref'])} 题")


PROMPT = """# 力学题按练习册章节分类：批次 {n}

把每道题归入下面练习册的章节。章节号只能从表中选。

## 章节表
{table}

## 规则
- `labels` 的第一项是这道题主要考查的章节：多数分值用到的方法属于哪一章就选哪一章。
- 其余小问若用到另一章的方法且该部分不少于 2 分，把那一章加在后面；最多 3 项，不要为了凑数而加。
- 按方法判断，不按情境：斜面上有摩擦是 4,用滑轮连着两个物体是 5(即使也有摩擦),用功率求速度是 9,
  只用 suvat 是 1,速度是时间的函数要求导或积分是 6。
- 用功、动能、势能求解的题归 8,即使物体在粗糙面上、要算摩擦力做的功;题目涉及功率或「功能原理」(阻力做功)归 9。
  只有用 F ≤ μR 与牛顿第二定律求加速度、判断是否滑动时才归 4。

## 示例(练习册原题与所在章节)
{examples}

## 输出
把 JSON 数组写到 `{out}`:
```json
[{{"id": "题号", "labels": ["5", "4"]}}]
```
每道题一项，题号照抄。只写这一个文件，不改其他文件，不运行 sync.py 或 git。

## 题目
"""


def plan(a):
    spec = load(a.table)
    ex = json.load(open(os.path.join(work(a.table), "examples.json"), encoding="utf-8"))
    shots = []
    for code in spec["labels"]:
        pool = [x for x in ex if x["chapter"] == code and (x["year"] or 0) <= 2017 and x["text"]][:2]
        shots += [f"- 章节 {code}:\n```\n{x['text'][:700]}\n```" for x in pool]
    table = "\n".join(f"- **{c}** {lab['name']}:{lab['scope']}" for c, lab in spec["labels"].items())
    if a.set == "test":
        items = [(x["id"], x["text"]) for x in ex if (x["year"] or 0) >= 2018]
    else:
        con = db.connect()
        items = [(r["id"], r["text"] or "") for r in con.execute(
            "SELECT id, COALESCE(question_latex, question_text) AS text FROM questions "
            "WHERE syllabus = ? AND component = ? ORDER BY id", (spec["syllabus"], spec["component"]))]
    run = os.path.join(work(a.table), a.out)
    os.makedirs(os.path.join(run, "out"), exist_ok=True)
    json.dump({"set": a.set, "ids": [i for i, _ in items]}, open(os.path.join(run, "plan.json"), "w"))
    for n, b in enumerate(range(0, len(items), a.size), 1):
        out = os.path.relpath(os.path.join(run, "out", f"batch_{n:02d}.json"), paths.ROOT)
        body = [PROMPT.format(n=n, table=table, examples="\n".join(shots), out=out)]
        body += [f"### {i}\n```\n{t[:1800]}\n```\n" for i, t in items[b:b + a.size]]
        path = os.path.join(run, f"batch_{n:02d}.md")
        open(path, "w", encoding="utf-8").write("\n".join(body))
        print(f"{os.path.relpath(path, paths.ROOT)}  {len(items[b:b + a.size])} 题")


def results(a, spec):
    run = os.path.join(work(a.table), a.out)
    want = json.load(open(os.path.join(run, "plan.json")))["ids"]
    got, problems = {}, []
    for f in sorted(glob.glob(os.path.join(run, "out", "batch_*.json"))):
        for x in json.load(open(f, encoding="utf-8")):
            labs = [str(v) for v in x.get("labels") or []]
            if not labs or len(labs) > 3 or any(v not in spec["labels"] for v in labs) or len(set(labs)) < len(labs):
                problems.append(f"{x.get('id')}: labels 不合规 {labs}")
                continue
            got[x["id"]] = labs
    missing = [i for i in want if i not in got]
    if missing:
        problems.append(f"缺 {len(missing)} 题:{' '.join(missing[:10])}")
    return got, problems


def score(a):
    spec = load(a.table)
    got, problems = results(a, spec)
    ex = {x["id"]: x for x in json.load(open(os.path.join(work(a.table), "examples.json"), encoding="utf-8"))}
    main = any_ = n = 0
    wrong = {}
    for i, labs in got.items():
        n += 1
        truth = ex[i]["chapter"]
        main += labs[0] == truth
        any_ += truth in labs
        if labs[0] != truth:
            wrong[(truth, labs[0])] = wrong.get((truth, labs[0]), 0) + 1
    for p in problems:
        print(p)
    print(f"{n} 题：主章节正确 {main}({main / max(n, 1):.0%}),练习册章节在标签中 {any_}({any_ / max(n, 1):.0%})")
    for (t, g), k in sorted(wrong.items(), key=lambda kv: -kv[1]):
        print(f"  练习册 {t} -> 判为 {g}:{k} 题")


def apply(a):
    spec = load(a.table)
    got, problems = results(a, spec)
    for p in problems:
        print(p)
    pre = spec["prefix"] + " "
    con = db.connect()
    db.ensure_tags(con)
    upd = []
    for i, labs in got.items():
        r = con.execute("SELECT tags FROM questions WHERE id = ?", (i,)).fetchone()
        if not r:
            continue
        old = [t for t in json.loads(r["tags"] or "[]") if not t.startswith(pre)]
        new = old + [f"{pre}{c} {spec['labels'][c]['name']}" for c in labs]
        upd.append((json.dumps(new, ensure_ascii=False), i))
    print(f"{len(upd)} 题{'已写入' if a.write else '待写入(加 --write)'}")
    if a.write:
        con.executemany("UPDATE questions SET tags = ? WHERE id = ?", upd)
        con.commit()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("examples"); p.add_argument("table"); p.add_argument("book")
    p = sub.add_parser("plan"); p.add_argument("table"); p.add_argument("--set", choices=["test", "bank"], required=True)
    p.add_argument("--size", type=int, default=35); p.add_argument("--out", default="run1")
    p = sub.add_parser("score"); p.add_argument("table"); p.add_argument("--out", default="run1")
    p = sub.add_parser("apply"); p.add_argument("table"); p.add_argument("--out", default="run1")
    p.add_argument("--write", action="store_true")
    a = ap.parse_args()
    {"examples": examples, "plan": plan, "score": score, "apply": apply}[a.cmd](a)


if __name__ == "__main__":
    main()
