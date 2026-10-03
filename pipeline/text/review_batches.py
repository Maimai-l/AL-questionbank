#!/usr/bin/env python3
"""Review CAIE question text and mark schemes against the original images, through
sub-agents, to measure (and later find) what the automated checks miss.

    python3 pipeline/text/review_batches.py plan --sample 9618:40,9709:10,9231:10 [--seed 1] [--size 15]
    python3 pipeline/text/review_batches.py report

plan    picks questions (a sample spread evenly over each syllabus's components, or
        every question when no count is given, e.g. --sample 9618), renders the
        mark scheme pages to raw/review/pages/, and writes one prompt file per batch,
        raw/review/batch_NN.md. A general-purpose sub-agent reads it, compares each
        question's text (question_latex, else question_text) with its crop and its
        mark scheme (ms_latex, else ms_text) with the scheme pages, and writes
        raw/review/out/batch_NN.json. It reports; it does not correct.
report  sums the results per syllabus and component: questions with major or minor
        problems, by kind, and writes raw/review/report.md with every major problem.

The text reviewed is what the exports use (pipeline/export/question_md.py).
"""
import argparse
import collections
import glob
import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import pymupdf  # noqa: E402

from lib import db, paths  # noqa: E402
from pipeline.ocr.latex_fix_batches import _pdf, scheme_pages  # noqa: E402

WORK = os.path.join(paths.RAW, "review")
OUT = os.path.join(WORK, "out")
PAGES = os.path.join(WORK, "pages")
KINDS = {
    "missing": "原图有、文本没有:句子、小问、选项、表格行、代码行、评分点",
    "extra": "文本有、原图没有:串入相邻题、页眉页脚、答题线、重复的句子",
    "wrong": "写错:数字、符号、公式、变量名、代码、评分代码",
    "garbled": "乱码或无法读懂的片段",
    "structure": "结构损坏:表格错行错列、代码缩进或换行、小问编号、评分细则的行与列错位",
    "marks": "分值缺失或与原图不符",
}

TASK = """# 题目文本审查批次 {n}

题库中的题干与评分细则由 OCR 得到,导出时(尤其是不带图片的导出)读者只看这些文本。
请对照原图逐题检查,**只报告,不改写**。

## 每题的步骤

1. 用 Read 打开题图(整道题的裁图),再读「题干文本」,逐句对照。
2. 用 Read 打开评分细则原页(列出的页可能包含相邻题,按左列题号找到本题),再读「评分细则文本」,逐行对照。
   评分细则文本每行是 `答案  |  评分代码  |  说明`,单元格内的 `<br>` 是换行,这是正常格式。
3. 公式写成 LaTeX(`$...$`)是正常的;只要数学含义与原图一致就不算错。空格、标点、大小写、
   换行位置的差别不算错。题干末尾的答题横线、`[Total: n]` 之类的有无不算错。
4. 只看文本是否忠实于原图,不评判题目本身。

## 问题类型(type)

{kinds}

## 严重程度(severity)

- `major`:只读文本的人会因此读不懂题、做出不同的答案,或按评分细则判出不同的分数。
- `minor`:能看出原意,不影响作答和判分。

## 输出

把 JSON 数组写到 `{out}`,每题一项:

```json
{{"id": "9618_s23_12_q03",
  "question": {{"verdict": "ok | minor | major", "issues": [{{"type": "missing", "severity": "major", "detail": "(b)(ii) 的第二句缺失:原图为 …"}}]}},
  "scheme": {{"verdict": "ok | minor | major", "issues": []}}}}
```

- `verdict` 取该部分最严重的一条;没有问题时为 `ok`,`issues` 为空数组。
- `detail` 用中文写清在哪里、原图是什么、文本是什么,便于之后更正。
- 原图看不清或页面里找不到本题时,把 `verdict` 写成 `unchecked` 并在 `issues` 里说明原因。
- 只写这一个 JSON 文件,不改数据库,不改其他文件。最后的回复只报告题数与 major、minor 的题数。

## 题目
"""


def pick(spec, seed):
    con = db.connect()
    rng = random.Random(seed)
    ids = []
    for part in spec.split(","):
        syl, _, n = part.partition(":")
        rows = [r for r in con.execute("SELECT id, component FROM questions WHERE syllabus = ? ORDER BY id", (syl,))]
        if not n:
            ids += [r["id"] for r in rows]
            continue
        by = collections.defaultdict(list)
        for r in rows:
            by[r["component"]].append(r["id"])
        comps = sorted(by)
        for k, c in enumerate(comps):        # spread evenly over the components
            share = int(n) // len(comps) + (k < int(n) % len(comps))
            ids += rng.sample(by[c], min(share, len(by[c])))
    return ids


def render(path, pages, stem):
    out = []
    with pymupdf.open(path) as doc:
        for n in pages:
            f = os.path.join(PAGES, f"{stem}_p{n + 1}.png")
            if not os.path.exists(f) or not os.path.getsize(f):   # an interrupted render leaves an empty file
                doc[n].get_pixmap(dpi=110, colorspace=pymupdf.csGRAY).save(f)
            out.append(f)
    return out


def rel(p):
    return os.path.relpath(p, paths.ROOT)


def plan(a):
    os.makedirs(PAGES, exist_ok=True)
    os.makedirs(OUT, exist_ok=True)
    con = db.connect()
    ids = pick(a.sample, a.seed)
    rows = [con.execute("SELECT * FROM questions WHERE id = ?", (q,)).fetchone() for q in ids]
    with open(os.path.join(WORK, "sample.json"), "w") as f:
        json.dump(ids, f, indent=1)
    kinds = "\n".join(f"- `{k}`:{v}" for k, v in KINDS.items())
    n = 0
    for b in range(0, len(rows), a.size):
        n += 1
        out = rel(os.path.join(OUT, f"batch_{n:02d}.json"))
        text = [TASK.format(n=n, out=out, kinds=kinds)]
        for r in rows[b:b + a.size]:
            crop = paths.resolve(r["image"])
            ms = _pdf(r["ms_pdf"], "ms")
            pages = []
            if ms:
                with pymupdf.open(ms) as d:
                    pages = render(ms, scheme_pages(d, r["q"]), os.path.splitext(os.path.basename(r["ms_pdf"]))[0])
            qt = r["question_latex"] or r["question_text"] or ""
            st = r["ms_latex"] or r["ms_text"] or ""
            text.append(f"\n### {r['id']}\n\n题图:{rel(crop) if crop else '无'}\n"
                        f"评分细则原页:{', '.join(rel(p) for p in pages) or '无'}\n"
                        f"\n题干文本({'question_latex' if r['question_latex'] else 'question_text'}):\n\n"
                        f"````\n{qt}\n````\n"
                        f"\n评分细则文本({'ms_latex' if r['ms_latex'] else 'ms_text'}):\n\n````\n{st}\n````\n")
        with open(os.path.join(WORK, f"batch_{n:02d}.md"), "w", encoding="utf-8") as f:
            f.write("".join(text))
        print(f"batch_{n:02d}.md  {len(rows[b:b + a.size])} 题")


def report(a):
    con = db.connect()
    res = []
    for f in sorted(glob.glob(os.path.join(OUT, "batch_*.json"))):
        res += json.load(open(f, encoding="utf-8"))
    groups = collections.defaultdict(lambda: collections.Counter())
    kinds = collections.defaultdict(lambda: collections.Counter())
    majors = []
    for x in res:
        r = con.execute("SELECT syllabus, component FROM questions WHERE id = ?", (x["id"],)).fetchone()
        g = f"{r['syllabus']} 卷 {r['component']}"
        for side, label in (("question", "题干"), ("scheme", "评分细则")):
            v = (x.get(side) or {}).get("verdict", "unchecked")
            groups[(g, label)][v] += 1
            groups[(r["syllabus"] + " 合计", label)][v] += 1
            for i in (x.get(side) or {}).get("issues", []):
                kinds[(r["syllabus"], label)][f"{i.get('type')}/{i.get('severity')}"] += 1
                if i.get("severity") == "major":
                    majors.append((x["id"], label, i.get("type"), i.get("detail", "")))
    lines = ["# 题目文本抽查结果", "", f"共 {len(res)} 题。", "",
             "| 范围 | 部分 | 抽查 | 无问题 | minor | major | 未能核对 |", "|---|---|---|---|---|---|---|"]
    for (g, label), c in sorted(groups.items()):
        lines.append(f"| {g} | {label} | {sum(c.values())} | {c['ok']} | {c['minor']} | {c['major']} | {c['unchecked']} |")
    lines += ["", "## 问题类型", "", "| 科目 | 部分 | 类型/严重程度 | 条数 |", "|---|---|---|---|"]
    for (s, label), c in sorted(kinds.items()):
        for k, n in c.most_common():
            lines.append(f"| {s} | {label} | {k} | {n} |")
    lines += ["", "## major 问题", "", "| 题目 | 部分 | 类型 | 说明 |", "|---|---|---|---|"]
    lines += [f"| {i} | {label} | {t} | {d.replace('|', '/').replace(chr(10), ' ')} |" for i, label, t, d in majors]
    with open(os.path.join(WORK, "report.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines[:4 + len(groups) + 2]))
    print(f"major 问题 {len(majors)} 条,详见 {rel(os.path.join(WORK, 'report.md'))}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("plan")
    p.add_argument("--sample", required=True)
    p.add_argument("--seed", type=int, default=1)
    p.add_argument("--size", type=int, default=15)
    p.set_defaults(fn=plan)
    sub.add_parser("report").set_defaults(fn=report)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
