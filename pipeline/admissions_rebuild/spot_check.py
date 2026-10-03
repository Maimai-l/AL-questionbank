#!/usr/bin/env python3
"""Spot check of the admissions questions (TMUA / TSA / BMAT) against their page images,
through sub-agents, to decide which papers need their transcription redone.

    python3 pipeline/admissions_rebuild/spot_check.py plan [--exam TMUA TSA] [--per-paper 5] [--size 10] [--seed 2026] [--run NAME]
    python3 pipeline/admissions_rebuild/spot_check.py verify raw/adm_check/out/batch_01.json
    python3 pipeline/admissions_rebuild/spot_check.py report [--run NAME]

--run puts a sample in raw/adm_check/NAME/ instead of raw/adm_check/, so a second sample
does not overwrite the first.

plan    draws the same --per-paper questions from every paper (fixed seed) and writes one
        prompt per batch, raw/adm_check/batch_NN.md. A sub-agent writes
        raw/adm_check/out/batch_NN.json:
        [{"id", "ok": bool, "issues": [{"kind", "now", "should"}], "text": str | null,
          "options": {letter: text} | null}]
verify  checks one result file: every question of the batch answered once, kinds known,
        ok agrees with issues, corrected text and options given whenever ok is false.
report  counts the questions with errors per paper and per exam, by kind.
"""
import argparse
import collections
import glob
import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from lib import db, paths  # noqa: E402

BASE = os.path.join(paths.RAW, "adm_check")
WORK = OUT = None


def use(run):
    global WORK, OUT
    WORK = os.path.join(BASE, run) if run else BASE
    OUT = os.path.join(WORK, "out")
KINDS = {
    "missing": "漏掉句子、段落、表格或图中的文字",
    "extra": "混入了其他题的内容、页眉页脚或乱码",
    "wrong": "字词、数字、公式与原图不符",
    "options": "选项缺失、多出、顺序错误,或选项文字与原图不符",
    "diagram": "题图有作答需要的信息,文本里没有写出,也没有说明见图",
    "answer": "答案字母不在选项中",
}

TASK = """# 入学考抽查 批次 {n}

题库中 TMUA、TSA、BMAT 的题干与选项来自 OCR。本批从各份试卷随机抽出若干题,请对照题图逐题核对,
用来判断哪些试卷需要整份重新转录。

## 每题的材料

- 题图:这道题在原卷上的图像,是核对的依据。用 Read 打开;看不清时用 pdftoppm 从给出的 PDF 与页码渲染原页放大看。
- 当前题干:库中的文本,页面与导出都显示它。选项通常写在题干末尾。
- 当前选项:按字母拆出的选项文字(option_texts),图形选项可能为空。
- 答案:官方答案字母。

## 核对内容

1. 题干:与题图逐句比对,有没有漏掉或多出句子、段落、表格行;数字、单位、公式、专有名词是否正确。
   公式写成 LaTeX 是对的,只看数学内容是否一致。
2. 选项:字母与数量是否齐全;每个选项的文字是否与原图一致。图形选项(选项画在图里)文字为空不算错。
3. 题图里作答需要的信息(图表数值、坐标、标注)若题干没有写出,记为 diagram。照片和装饰图不算。
4. 答案字母必须在选项中。
5. 只记实质错误。空格、换行、斜体、标点全角半角、LaTeX 写法不同但内容相同,都不算错。

## 输出

把 JSON 数组写到 `{out}`,每题一项:

```json
{{"id": "TMUA-2016-P1-q1", "ok": false,
  "issues": [{{"kind": "wrong", "now": "A $-\\\\angle12\\\\sqrt{{3}}$", "should": "A $-12\\\\sqrt{{3}}$"}}],
  "text": "改正后的完整题干(含选项),或 null",
  "options": {{"A": "...", "B": "..."}}}}
```

- `kind` 只能是:{kinds}。
- `ok` 为 true 时 `issues` 为空,`text` 与 `options` 写 null。
- `ok` 为 false 时,`text` 写出改正后的**完整**题干(格式与当前题干相同),`options` 写出改正后的全部选项;
  选项没有错时 `options` 写 null。
- 写完后运行 `python3 pipeline/admissions_rebuild/spot_check.py verify {out}`,直到输出「全部通过」。
- 只写这一个 JSON 文件,不改数据库与其他文件。最后的回复只报告题数、有错的题数,以及每道有错的题一句话说明。

## 题目
"""


def rel(p):
    return os.path.relpath(p, paths.ROOT)


def text_of(r):
    return r["question_latex"] or r["question_text"] or ""


def sample(con, per, seed, exams):
    papers = collections.defaultdict(list)
    marks = ", ".join("?" * len(exams))
    for r in con.execute(f"SELECT * FROM questions WHERE syllabus IN ({marks}) ORDER BY id", exams):
        papers[r["qp_pdf"]].append(r)
    rng = random.Random(seed)
    rows = []
    for pdf in sorted(papers):
        qs = papers[pdf]
        rows += sorted(rng.sample(qs, min(per, len(qs))), key=lambda r: r["id"])
    return rows


def plan(a):
    os.makedirs(OUT, exist_ok=True)
    con = db.connect()
    rows = sample(con, a.per_paper, a.seed, a.exam)
    kinds = "、".join(f"`{k}`({v})" for k, v in KINDS.items())
    for n, b in enumerate(range(0, len(rows), a.size), 1):
        out = rel(os.path.join(OUT, f"batch_{n:02d}.json"))
        text = [TASK.format(n=n, out=out, kinds=kinds)]
        for r in rows[b:b + a.size]:
            img = paths.resolve(r["image"]) if r["image"] else None
            pdf = os.path.join(paths.DATA, "papers", r["qp_pdf"]) if r["qp_pdf"] else None
            text.append(
                f"\n### {r['id']}\n\n"
                f"题图:{rel(img) if img else '无'}\n"
                f"原卷:{rel(pdf) if pdf else '无'},第 {', '.join(map(str, json.loads(r['qp_pages'] or '[]')))} 页\n"
                f"答案:{r['answer'] or '无'};选项字母:{', '.join(json.loads(r['options'] or '[]'))}\n"
                f"\n当前题干:\n\n````\n{text_of(r)}\n````\n"
                f"\n当前选项:\n\n````json\n{r['option_texts'] or '{}'}\n````\n")
        with open(os.path.join(WORK, f"batch_{n:02d}.md"), "w", encoding="utf-8") as f:
            f.write("".join(text))
        print(f"{rel(WORK)}/batch_{n:02d}.md  {len(rows[b:b + a.size])} 题")
    print(f"共 {len(rows)} 题")


def batch_ids(path):
    md = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(path))),
                      os.path.basename(path).replace(".json", ".md"))
    return [line[4:].strip() for line in open(md, encoding="utf-8") if line.startswith("### ")]


def check(path):
    """Problems found in one result file."""
    try:
        items = json.load(open(path, encoding="utf-8"))
    except (OSError, ValueError) as e:
        return [f"读不出 JSON:{e}"]
    want = batch_ids(path)
    got = [x.get("id") for x in items]
    probs = [f"缺少 {i}" for i in want if i not in got]
    probs += [f"多出或重复 {i}" for i, c in collections.Counter(got).items() if i not in want or c > 1]
    for x in items:
        i, issues = x.get("id"), x.get("issues") or []
        if x.get("ok") not in (True, False):
            probs.append(f"{i}: ok 必须是 true 或 false")
            continue
        if x["ok"] and (issues or x.get("text") or x.get("options")):
            probs.append(f"{i}: ok 为 true 时 issues 应为空,text、options 应为 null")
        if not x["ok"]:
            if not issues:
                probs.append(f"{i}: ok 为 false 时要列出 issues")
            if not x.get("text"):
                probs.append(f"{i}: ok 为 false 时要写出改正后的完整题干")
        for s in issues:
            if s.get("kind") not in KINDS:
                probs.append(f"{i}: kind 只能是 {', '.join(KINDS)},不能是 {s.get('kind')!r}")
        if x.get("options") is not None and not isinstance(x["options"], dict):
            probs.append(f"{i}: options 要写成 {{字母: 文字}}")
    return probs


def verify(a):
    probs = check(a.file)
    print("\n".join(probs) if probs else "全部通过")


def report(a):
    con = db.connect()
    paper = {r["id"]: r["qp_pdf"] for r in con.execute(
        "SELECT id, qp_pdf FROM questions WHERE syllabus IN ('TMUA', 'TSA', 'BMAT')")}
    per_paper = collections.defaultdict(lambda: [0, 0])
    per_exam = collections.defaultdict(lambda: [0, 0])
    kinds = collections.Counter()
    for path in sorted(glob.glob(os.path.join(OUT, "batch_*.json"))):
        if check(path):
            print(f"{rel(path)} 未通过 verify,不计入")
            continue
        for x in json.load(open(path, encoding="utf-8")):
            p = paper[x["id"]]
            exam = x["id"].split("-")[0]
            for d in (per_paper[p], per_exam[exam]):
                d[0] += 1
                d[1] += not x["ok"]
            kinds.update({s["kind"] for s in x["issues"]})
    for e, (n, bad) in sorted(per_exam.items()):
        print(f"{e}: {bad}/{n} 题有错")
    print("错误类型(按题计):" + ",".join(f"{k} {v}" for k, v in kinds.most_common()))
    print("\n有错的试卷:")
    for p, (n, bad) in sorted(per_paper.items()):
        if bad:
            print(f"  {p}: {bad}/{n}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("plan")
    p.add_argument("--per-paper", type=int, default=5)
    p.add_argument("--size", type=int, default=10)
    p.add_argument("--seed", type=int, default=2026)
    p.add_argument("--exam", nargs="+", default=["TMUA", "TSA", "BMAT"], choices=["TMUA", "TSA", "BMAT"])
    p.add_argument("--run")
    p.set_defaults(fn=plan)
    p = sub.add_parser("verify")
    p.add_argument("file")
    p.set_defaults(fn=verify)
    p = sub.add_parser("report")
    p.add_argument("--run")
    p.set_defaults(fn=report)
    a = ap.parse_args()
    use(getattr(a, "run", None))
    a.fn(a)


if __name__ == "__main__":
    main()
