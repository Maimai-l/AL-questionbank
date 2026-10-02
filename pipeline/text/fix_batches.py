#!/usr/bin/env python3
"""Rewrite CAIE question text and mark schemes against the original pages, through
sub-agents, and keep the result as replayable corrections.

    python3 pipeline/text/fix_batches.py plan --syllabus 9618 [--size 10] [--out run1] [ID ...]
    python3 pipeline/text/fix_batches.py verify raw/text_fix/run1/out/batch_01.json
    python3 pipeline/text/fix_batches.py apply [--write]

plan    writes one prompt file per batch, raw/text_fix/<run>/batch_NN.md, with each
        question's crop, the PDF text layer, the current text and mark scheme, and the
        mark scheme pages (rendered to raw/text_fix/pages/). A general-purpose sub-agent
        writes raw/text_fix/<run>/out/batch_NN.json:
        [{"id", "question": text | null, "scheme": text | null, "why"}], null meaning
        the current text is right.
verify  checks one result file: formulas render (check_latex.py), no [DIAGRAM] is left,
        every scheme block ends with its marks and they add up to the question's marks,
        the parts match the paper's tariffs, the text keeps the text layer's words.
apply   appends what passes to pipeline/text/text_fixes.jsonl and, with --write,
        replays that file into the database. A line is {id, column, base, text, why}:
        it replaces the column only while the column still holds the text whose sha1
        starts with `base`, so a line made from an older text is skipped, not forced.
        Run before split_parts.py; then split_parts.py --write.

The text written is what the pages and the exports read: question_latex (else
question_text) and ms_latex (else ms_text).
"""
import argparse
import glob
import hashlib
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import pymupdf  # noqa: E402

from lib import db, paths, scheme  # noqa: E402
from manager import bank  # noqa: E402
from pipeline.ocr.latex_fix_batches import _pdf, scheme_pages  # noqa: E402
from pipeline.text import check_latex  # noqa: E402

WORK = os.path.join(paths.RAW, "text_fix")
PAGES = os.path.join(WORK, "pages")
FIXES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "text_fixes.jsonl")
WORD = re.compile(r"[A-Za-z]{4,}")

TASK = """# 题干与评分细则更正批次 {n}

题库的题干与评分细则来自 OCR,有大段丢失、乱码、串题,图示只剩 `[DIAGRAM]`。不带图片的导出只给读者这些文本,
所以要让**只读文本的人也能完整作答、按评分细则判分**。请逐题对照原图重写。

## 每题的材料

- 题图:整道题的裁图(可能很长),这是题干的依据。用 Read 打开。
- PDF 文本层:从 PDF 直接取出的文字,字词通常准确,但排版、表格、公式被打散;用来核对字词。
- 当前题干、当前评分细则:要更正的文本。
- 评分细则原页:列出的页可能包含相邻题,按左列题号找到本题。

## 题干的写法

1. 从题号开始,按原图顺序写出全部文字,一个字不漏;不要改写、概括或补充原图没有的内容。
2. 小问标签 `(a)`、`(b)`、`(i)`、`(ii)` 放在各自一行的行首,写法与原图相同;分值 `[3]` 留在原图的位置(行末)。
3. 答题横线、空白答题框不写;需要填写的表格写成 Markdown 表格,空格留空;需要补全的代码或伪代码中的空位写成 `………`。
4. 表格写成 Markdown 表格(`| A | B |`)。代码与伪代码放进 ``` 代码块,保留原图的缩进与换行。
5. 公式用 LaTeX,放在 `$...$` 中;编程语言、伪代码、SQL 里的符号照原样写,不要改成 LaTeX。
6. **图示要写成文字**(不要留 `[DIAGRAM]`)。在图的位置写一行 `Diagram:`,接着用以下方式之一写出图中全部信息:
   - 逻辑电路:每个门写成一行表达式,如 `P = A XOR B`,并写出输出 `X = …`;
   - 寄存器、比特位、方框中的数:按顺序写出,如 `ACC: 0 1 1 0 0 1 0 1`;
   - 带权图、网络:每条边一行,如 `Base – Town1: 4`;
   - 连线题:分别列出左列与右列的全部选项(`- …`);
   - 流程图、状态图:按编号写出每个框与每条箭头及其条件;
   - 栈、队列、数组、内存图:写成表格,指针标注写在对应行;
   - 数据库表结构、类图:按原图逐项写出;
   - 照片、装饰性图片:一句话说明内容。
   图中有、作答需要的信息必须全部写出。

## 评分细则的写法

1. 每个小问一块,第一行以小问标签开头(如 `3(a)(ii)  `,与原页左列相同),之后照原页逐行写出该小问的全部内容:
   评分说明、每个评分点(`MP1 …`、`1 …`、`• …`)、示例答案、各语言的示例代码(保留缩进)、注意事项。
2. 每块的最后一行末尾写 `  |  分值`(两个空格、竖线、两个空格、原页 Marks 列的数字)。块内其他地方不要出现两侧都带两个空格的竖线。
3. 答案中的表格(真值表、追踪表、指针表)写成 Markdown 表格行,放在块内;连线题写出每一条正确的连线(`1NF → There are no repeating groups …`);
   流程图答案按步骤写出。负号写成 `−` 或 `-`,不要写成乱码。
4. 原页没有的内容不要写。

## 输出

把 JSON 数组写到 `{out}`,每题一项:

```json
{{"id": "9618_s23_12_q03", "question": "完整的新题干,或 null", "scheme": "完整的新评分细则,或 null", "why": "一句中文:改了什么"}}
```

- `null` 表示当前文本已经完全正确,不需要改。只要有任何与原图不符之处,就写出**完整**的新文本(不是片段)。
- 写完后运行 `python3 pipeline/text/fix_batches.py verify {out}`,按报告修改,直到输出「全部通过」。
  报告分值合计不符、小问数不符时,先回到原图核对;确认原图本身如此(例如原卷印刷的小计)时,在 `why` 里写明。
- 只写这一个 JSON 文件,不改数据库,不改其他文件。最后的回复只报告题数、改了题干的题数、改了评分细则的题数。

## 题目
"""


def sha(text):
    return hashlib.sha1((text or "").encode()).hexdigest()[:16]


def qcol(r):
    return "question_latex" if r["question_latex"] else "question_text"


def mcol(r):
    return "ms_latex" if r["ms_latex"] else "ms_text"


def rel(p):
    return os.path.relpath(p, paths.ROOT)


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
    out_dir = os.path.join(WORK, a.out)
    os.makedirs(os.path.join(out_dir, "out"), exist_ok=True)
    os.makedirs(PAGES, exist_ok=True)
    con = db.connect()
    if a.ids:
        rows = [con.execute("SELECT * FROM questions WHERE id = ?", (q,)).fetchone() for q in a.ids]
    else:
        rows = list(con.execute("SELECT * FROM questions WHERE syllabus = ? ORDER BY id", (a.syllabus,)))
    rows = [r for r in rows if r]
    n = 0
    for b in range(0, len(rows), a.size):
        n += 1
        out = rel(os.path.join(out_dir, "out", f"batch_{n:02d}.json"))
        text = [TASK.format(n=n, out=out)]
        for r in rows[b:b + a.size]:
            crop = paths.resolve(r["image"])
            ms = _pdf(r["ms_pdf"], "ms")
            pages = []
            if ms:
                with pymupdf.open(ms) as d:
                    pages = render(ms, scheme_pages(d, r["q"]), os.path.splitext(os.path.basename(r["ms_pdf"]))[0])
            tariffs = json.loads(r["marks_parts"] or "[]")
            text.append(
                f"\n### {r['id']}({bank.paper_code(r)} 第 {r['q']} 题,共 {r['marks']} 分;各小问分值 {tariffs})\n\n"
                f"题图:{rel(crop) if crop else '无'}\n评分细则原页:{', '.join(rel(p) for p in pages) or '无'}\n"
                f"\nPDF 文本层:\n\n````\n{r['question_text'] or ''}\n````\n"
                f"\n当前题干({qcol(r)}):\n\n````\n{r[qcol(r)] or ''}\n````\n"
                f"\n当前评分细则({mcol(r)}):\n\n````\n{r[mcol(r)] or ''}\n````\n")
        with open(os.path.join(out_dir, f"batch_{n:02d}.md"), "w", encoding="utf-8") as f:
            f.write("".join(text))
        print(f"{rel(out_dir)}/batch_{n:02d}.md  {len(rows[b:b + a.size])} 题")


LABEL = re.compile(r"^\s*\d+\s*(\([a-z]+\))?(\([ivx]+\))?\s")


def check_scheme(text, marks):
    """Problems with a mark scheme in the block format: blocks without marks, a wrong total."""
    problems, total, open_block = [], 0, False
    for line in text.splitlines():
        if not line.strip():
            continue
        if LABEL.match(line) and not scheme.is_row(line):
            if open_block:
                problems.append(f"块没有以分值结束:{line[:40]!r} 之前")
            open_block = True
        if scheme.is_row(line):
            cells = scheme.cells(line)
            m = re.fullmatch(r"\d+", cells[1].strip()) if len(cells) > 1 else None
            if not m:
                problems.append(f"分值不是数字:{line[-40:]!r}")
            else:
                total += int(cells[1])
            open_block = False
    if open_block:
        problems.append("最后一块没有以分值结束")
    if marks and total != marks:
        problems.append(f"各块分值合计 {total},题目共 {marks} 分")
    return problems


def check_question(text, r):
    problems = []
    if "[DIAGRAM]" in text:
        problems.append("还有 [DIAGRAM]")
    tariffs = json.loads(r["marks_parts"] or "[]")
    labels = re.findall(r"(?m)^\s*(?:\d+\s+)?\(([a-h]|i{1,3}|iv|vi{0,3}|ix|x)\)", text)
    if len(tariffs) > 1:
        lowest = 0
        for i, x in enumerate(labels):            # a letter followed by a roman is not lowest-level
            nxt = labels[i + 1] if i + 1 < len(labels) else None
            roman = lambda y: y and re.fullmatch(r"i{1,3}|iv|vi{0,3}|ix|x", y) is not None
            if roman(x) or not roman(nxt):
                lowest += 1
        if lowest != len(tariffs):
            problems.append(f"最低一级小问 {lowest} 个,原卷分值 {len(tariffs)} 个({tariffs})")
    layer = [w.lower() for w in WORD.findall(r["question_text"] or "")]
    if layer:
        have = set(w.lower() for w in WORD.findall(text))
        miss = sum(1 for w in layer if w not in have) / len(layer)
        if miss > 0.08:
            problems.append(f"文本层中 {miss:.0%} 的词不在新题干里")
    return problems


def verify_file(path):
    """(lines that pass, report) for one result file."""
    con = db.connect()
    items = json.load(open(path, encoding="utf-8"))
    report, ok, texts = [], [], {}
    for x in items:
        r = con.execute("SELECT * FROM questions WHERE id = ?", (x.get("id"),)).fetchone()
        if not r:
            report.append(f"{x.get('id')}: 没有这道题")
            continue
        lines = []
        if x.get("question"):
            q = x["question"].strip() + "\n"
            for p in check_question(q, r):
                report.append(f"{r['id']} 题干:{p}")
            lines.append({"id": r["id"], "column": qcol(r), "base": sha(r[qcol(r)]), "text": q, "why": x.get("why", "")})
            if qcol(r) == "question_latex":
                texts[(r["id"], "question_latex")] = q
        if x.get("scheme"):
            s = x["scheme"].strip() + "\n"
            for p in check_scheme(s, r["marks"]):
                report.append(f"{r['id']} 评分细则:{p}")
            lines.append({"id": r["id"], "column": mcol(r), "base": sha(r[mcol(r)]), "text": s, "why": x.get("why", "")})
            if mcol(r) == "ms_latex":
                texts[(r["id"], "ms_latex")] = s
        ok += lines
    for i, errs in check_latex.check({i for i, _ in texts}, texts).items():
        for e in errs:
            report.append(f"{i} {e['column']}: 公式无法渲染({e['error'][:60]}):{e['tex'][:80]!r}")
    return ok, report


def verify(a):
    ok, report = verify_file(a.file)
    print("\n".join(report) if report else "全部通过")
    print(f"{len(ok)} 条可用")


def replay(write):
    con = db.connect()
    done = skipped = 0
    for line in open(FIXES, encoding="utf-8"):
        f = json.loads(line)
        cur = con.execute(f"SELECT {f['column']} FROM questions WHERE id = ?", (f["id"],)).fetchone()
        if cur is None:
            continue
        if cur[0] == f["text"]:
            continue
        if sha(cur[0]) != f["base"]:
            skipped += 1
            continue
        if write:
            con.execute(f"UPDATE questions SET {f['column']} = ? WHERE id = ?", (f["text"], f["id"]))
        done += 1
    if write:
        con.commit()
    print(f"{'写入' if write else '待写入'} {done} 处;原文本已变、跳过 {skipped} 处")


def apply(a):
    have = set()
    if os.path.exists(FIXES):
        for line in open(FIXES, encoding="utf-8"):
            f = json.loads(line)
            have.add((f["id"], f["column"], f["base"]))
    added = 0
    with open(FIXES, "a", encoding="utf-8") as out:
        for path in sorted(glob.glob(os.path.join(WORK, "*", "out", "batch_*.json"))):
            ok, report = verify_file(path)
            bad = {line.split()[0] for line in report}
            for line in report:
                print(f"{rel(path)}: {line}")
            for f in ok:
                if f["id"] in bad or (f["id"], f["column"], f["base"]) in have:
                    continue
                out.write(json.dumps(f, ensure_ascii=False) + "\n")
                have.add((f["id"], f["column"], f["base"]))
                added += 1
    print(f"追加 {added} 条到 {rel(FIXES)}")
    replay(a.write)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("plan")
    p.add_argument("ids", nargs="*")
    p.add_argument("--syllabus", default="9618")
    p.add_argument("--size", type=int, default=10)
    p.add_argument("--out", default="run1")
    p.set_defaults(fn=plan)
    p = sub.add_parser("verify")
    p.add_argument("file")
    p.set_defaults(fn=verify)
    p = sub.add_parser("apply")
    p.add_argument("--write", action="store_true")
    p.set_defaults(fn=apply)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
