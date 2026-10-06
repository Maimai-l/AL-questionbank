#!/usr/bin/env python3
"""A short list of concepts to memorise for each 9618 textbook chapter, chosen by subagents.

    python3 pipeline/explain/concepts.py plan      raw/concepts_9618/ch_NN.md, one per chapter
    (a subagent per chapter writes raw/concepts_9618/out/ch_NN.json)
    python3 pipeline/explain/concepts.py check     every result present and well formed
    python3 pipeline/explain/concepts.py build     data/concepts/9618.md

Each chapter's prompt gives the textbook chapter (its Key terms boxes) and the candidate terms
of that syllabus section from term_tree.py's terms.json (exports/9618_terms/), ranked by the
number of papers that examine them, with the mark scheme rows quoting them. The subagent picks
the concepts and writes one sentence for each in the scheme's wording:
    [{"term": "pixel", "zh": "像素", "def": "The smallest addressable element of an image."}]
"""
import argparse, glob, json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from lib import paths  # noqa: E402

WORK = os.path.join(paths.RAW, "concepts_9618")
OUT = os.path.join(WORK, "out")
TERMS = next((p for p in (os.path.join(d, "9618_terms", "terms.json")
                          for d in (paths.EXPORTS, os.path.join(paths.ROOT, "exports")))
              if os.path.exists(p)), os.path.join(paths.EXPORTS, "9618_terms", "terms.json"))
RESULT = os.path.join(paths.DATA, "concepts", "9618.md")
MAX_WORDS = 30

TASK = """# 9618 第 {n} 章 {title}:极简概念

为学生挑出本章必须背下来的概念,每个只写一句话。不写讲义、不举例、不解释。

## 材料

1. 教材本章:`{book}`。用 Read 打开,重点看各个 Key terms 框和小节标题;文件长,用 offset/limit 分段读。
2. 下面的候选术语:真题评分细则中出现过的术语,按考到它的试卷数排序,附评分细则原文行。

## 要求

- 选 8 至 20 个概念。真题考过定义、描述或比较的优先;教材 Key terms 中重要而候选里没有的可以补上;
  编程中的普通词汇(variable、loop 之类在本章不是概念的)和日常用词不要。
- 每个概念写三项:
  - `term`:英文名称,用教材或大纲的写法;
  - `zh`:中文名称,2 至 8 个字;
  - `def`:英文一句话,不超过 25 个词,用评分细则能拿分的措辞,只写定义,不举例、不解释。
- 按重要程度排序,最常考的在前。
- 只把 JSON 数组写到 `{out}`:`[{{"term": "...", "zh": "...", "def": "..."}}]`。
- 写完后运行 `python3 pipeline/explain/concepts.py check`,本章报错就改,直到本章没有报错(其他章没写完的报错不用管)。
- 不改其他文件。最后回复一行:写入的概念个数。

## 候选术语
"""


def chapters():
    out = []
    for p in sorted(glob.glob(os.path.join(paths.BOOKS, "9618", "9618_ch*.md"))):
        m = re.match(r"9618_ch(\d+)_\d+_(.+)\.md$", os.path.basename(p))
        out.append((int(m.group(1)), re.sub(r" ai$", " (AI)", m.group(2).replace("_", " ").capitalize()), p))
    return out


def plan(a):
    terms = json.load(open(TERMS, encoding="utf-8"))
    os.makedirs(OUT, exist_ok=True)
    for n, title, book in chapters():
        mine = [t for t in terms if t["subsection"].split(".")[0] == str(n)]
        mine.sort(key=lambda t: (-t["level"], -t["papers"]))
        text = [TASK.format(n=n, title=title, book=os.path.relpath(book, paths.ROOT),
                            out=os.path.relpath(os.path.join(OUT, f"ch_{n:02d}.json"), paths.ROOT))]
        for t in mine:
            rows = ([t["definition"]] if t.get("definition") else []) + t.get("evidence", [])[:3]
            text.append(f"\n- **{t['term']}**(考到的试卷 {t['papers']} 份)\n"
                        + "".join(f"  - {r}\n" for r in rows[:4]))
        if not mine:
            text.append("\n(没有候选,完全依据教材 Key terms 与小节标题挑选)\n")
        with open(os.path.join(WORK, f"ch_{n:02d}.md"), "w", encoding="utf-8") as f:
            f.write("".join(text))
        print(f"ch_{n:02d}  {title}  候选 {len(mine)}")


def problems(path):
    try:
        items = json.load(open(path, encoding="utf-8"))
    except (OSError, ValueError) as e:
        return [f"读不出 JSON:{e}"]
    if not isinstance(items, list) or not 8 <= len(items) <= 20:
        return ["应是 8 至 20 项的数组"]
    errs, seen = [], set()
    for i, x in enumerate(items, 1):
        if not isinstance(x, dict) or set(x) != {"term", "zh", "def"}:
            errs.append(f"第 {i} 项只能有 term、zh、def 三个键")
            continue
        if not all(isinstance(x[k], str) and x[k].strip() for k in x):
            errs.append(f"第 {i} 项有空值")
        if len(x["def"].split()) > MAX_WORDS:
            errs.append(f"{x['term']}:def 超过 {MAX_WORDS} 个词")
        if x["term"].lower() in seen:
            errs.append(f"{x['term']} 重复")
        seen.add(x["term"].lower())
    return errs


def check(a):
    bad = 0
    for n, title, _ in chapters():
        path = os.path.join(OUT, f"ch_{n:02d}.json")
        errs = problems(path) if os.path.exists(path) else ["还没有结果"]
        for e in errs:
            print(f"ch_{n:02d}: {e}")
        bad += bool(errs)
    print("全部通过" if not bad else f"{bad} 章有问题")


def build(a):
    lines = ["# 9618 Computer Science 极简概念", ""]
    total = 0
    for n, title, _ in chapters():
        path = os.path.join(OUT, f"ch_{n:02d}.json")
        if problems(path):
            sys.exit(f"ch_{n:02d} 未通过 check")
        lines += [f"## {n} {title}", ""]
        for i, x in enumerate(json.load(open(path, encoding="utf-8")), 1):
            d = x["def"].strip()
            lines.append(f"{i}. **{x['term'].strip()}**({x['zh'].strip()}):{d if d.endswith('.') else d + '.'}")
            total += 1
        lines.append("")
    os.makedirs(os.path.dirname(RESULT), exist_ok=True)
    with open(RESULT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"{total} 个概念 -> {os.path.relpath(RESULT, paths.ROOT)}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["plan", "check", "build"])
    a = ap.parse_args()
    {"plan": plan, "check": check, "build": build}[a.cmd](a)


if __name__ == "__main__":
    main()
