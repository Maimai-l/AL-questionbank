#!/usr/bin/env python3
"""Export CAIE 9618 questions that explicitly require code production.

The selection deliberately excludes questions that only ask students to trace,
explain, or identify code. It includes direct requests to write/complete
pseudocode, write SQL/assembly, and every Paper 4 practical code task. Besides
the rules on the whole text, a part whose task (part_data, from its command
words) is write_code, complete_code, sql or assembly counts; those parts are
named in the listing and the manifest.
"""
from __future__ import annotations

import csv
import argparse
import re
import shutil
import sqlite3
import tempfile
import zipfile
from collections import Counter
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from lib import paths  # noqa: E402
from pipeline.export import question_md  # noqa: E402

DATA = Path(paths.DATA)
ASSETS = DATA  # images and books/ live in data/
DB = Path(paths.DB)
OUT = Path(paths.EXPORTS) / "caie_9618_code_questions.zip"
OUT_SLIM = Path(paths.EXPORTS) / "caie_9618_code_questions_slim.zip"
PACKAGE = "caie_9618_code_questions"

RULES = (
    ("Pseudocode: write", re.compile(r"\bwrite\s+(?:efficient\s+)?pseudocode\b", re.I)),
    ("Pseudocode: complete", re.compile(r"\bcomplete\s+(?:the\s+)?pseudocode\b", re.I)),
    ("SQL", re.compile(r"\bwrite\s+(?:the\s+)?(?:structured query language\s+)?sql\b|\bwrite\s+the\s+structured query language\b", re.I)),
    ("Assembly / machine code", re.compile(r"\bwrite\s+(?:an?\s+)?(?:assembly language|machine code|assembly code)\b", re.I)),
)


# part tasks (part_data, pipeline/text/split_parts.py) that produce code
PART_TASKS = {"write_code": "Pseudocode: write", "complete_code": "Pseudocode: complete",
              "sql": "SQL", "assembly": "Assembly / machine code"}


def code_parts(row: sqlite3.Row) -> list[str]:
    """Labels of the parts whose command words ask for code."""
    parts = (question_md.parts_of(row) or {}).get("parts", [])
    return [p["label"] for p in parts if p.get("task") in PART_TASKS and p["label"]]


def categories(row: sqlite3.Row) -> list[str]:
    text = row["question_text"] or ""
    found = [label for label, pattern in RULES if pattern.search(text)]
    for p in (question_md.parts_of(row) or {}).get("parts", []):
        label = PART_TASKS.get(p.get("task"))
        if label and label not in found:
            found.append(label)
    if row["component"] == "4":
        found.append("Paper 4: practical program code")
    return found


def format_guide() -> str:
    return """# CAIE 9618：代码作答格式

## 这份包如何分类

只收录题干**直接要求产出代码**的题：写/补全伪代码、写 SQL、写汇编/机器代码，
以及所有 Paper 4 实际编程题。阅读、追踪、解释已有程序的题不计入。

## Paper 2 / Paper 3：伪代码

这些试卷要求的是清晰的 Cambridge 风格伪代码，而不是可运行的 Python、Java 或
Visual Basic。题目给出的模块头、变量名、参数、数据结构和可用函数必须沿用；题目
若说 *must use* 某模块或函数，也必须实际调用它。

常用写法（以题库中已有题干的记法为准）：

```text
DECLARE Count : INTEGER
DECLARE Names : ARRAY[1:10] OF STRING

PROCEDURE Process(Value : INTEGER)
    IF Value > 0 THEN
        OUTPUT Value
    ELSE
        OUTPUT "Invalid"
    ENDIF
ENDPROCEDURE

FUNCTION IsValid(Text : STRING) RETURNS BOOLEAN
    ...
    RETURN TRUE
ENDFUNCTION
```

- 赋值用 `←`（OCR 有时显示成空格）；相等比较用 `=`，不等用 `<>`。
- 声明应给出标识符和类型；记录用 `TYPE ... ENDTYPE`，数组用 `ARRAY[...] OF ...`。
- 选择结构：`IF ... THEN / ELSE / ENDIF`；多分支：`CASE OF / OTHERWISE / ENDCASE`。
- 循环：`FOR ... TO ... NEXT`、`WHILE ... ENDWHILE`、`REPEAT ... UNTIL`。
- 子程序：`PROCEDURE ... ENDPROCEDURE` 或 `FUNCTION ... RETURNS <type> ... ENDFUNCTION`；
  调用用 `CALL`，函数必须 `RETURN`。
- 字符串、数组和文件题须使用题目给定的函数/文件操作名称（如 `LENGTH`、`MID`、
  `OPENFILE`、`READFILE`、`WRITEFILE`、`EOF`、`CLOSEFILE`），不要自行换成另一门语言的 API。
- 要求“complete pseudocode”时，只补题目留下的部分，并保持原有模块签名、缩进和命名。

## Paper 4：实际程序代码 + 证据

Paper 4 要求写**可运行的实际程序代码**，不是伪代码。遵从每套题指定的语言、起始
文件、模块签名、输入/输出文件名和保存名。题干通常明确要求：

1. 按题号指定的文件名保存程序；
2. 在 evidence document 的对应小问中复制粘贴程序代码；
3. 在要求处运行测试，并把输出截图粘贴进 evidence document；
4. 只实现该小问要求的模块，但保持前面已给模块可调用。

因此，Paper 4 不能把答案写成上述伪代码格式；应使用所选实际语言的有效语法、
缩进/代码块和文件 I/O。每道题的精确提交/保存说明已保留在 `code_questions.md`。

## SQL 与汇编

- SQL 题：写出题目指定的 `SELECT` / `INSERT` / `UPDATE` 等 SQL 语句，沿用给定表、字段和条件名。
- 汇编/机器代码题：沿用该题附表中的指令集、寻址模式、标签和操作数格式；不同年份附表不同，
  不应套用另一题的指令名称。
"""


def select_slim(rows: list[sqlite3.Row]) -> list[sqlite3.Row]:
    """Choose a compact, balanced set of direct code-production tasks."""
    quotas = (
        ("2", "Programming", 4),
        ("2", "Data Types and Structures", 4),
        ("2", "Algorithm Design and Problem-solving", 2),
        ("3", "Computational thinking and Problem-solving", 2),
        ("3", "Data Representation", 2),
        ("3", "Further Programming", 2),
        ("4", "Computational thinking and Problem-solving", 4),
        ("4", "Further Programming", 4),
        ("1", "Databases", 2),
    )
    selected = []
    for component, topic, limit in quotas:
        candidates = [row for row in rows if row["component"] == component and row["topic_name"] == topic]
        candidates.sort(key=lambda row: (row["year"], row["month"], row["paper"], row["q"]), reverse=True)
        selected.extend(candidates[:limit])
    return sorted(selected, key=lambda row: (row["component"], row["year"], row["month"], row["paper"], row["q"]))


def main(slim: bool = False) -> None:
    out = OUT_SLIM if slim else OUT
    package = PACKAGE + "_slim" if slim else PACKAGE
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix="caie-9618-code-"))
    try:
        with sqlite3.connect(DB) as con:
            con.row_factory = sqlite3.Row
            rows = [row for row in con.execute("""
                SELECT id, component, component_name, paper, session, year, month, q, marks,
                       topic_name, question_text, question_latex, ms_text, ms_latex, image,
                       q_quality, part_data
                FROM questions
                WHERE syllabus = '9618'
                ORDER BY component, year, month, paper, q, id
            """) if categories(row)]
        if slim:
            rows = select_slim(rows)

        by_category = Counter(category for row in rows for category in categories(row))
        by_topic = Counter(row["topic_name"] for row in rows)
        question_lines = ["# CAIE 9618 代码题", "",
                          f"共 **{len(rows)}** 题{'（题型代表性精选，不含图片）' if slim else ''}。筛选规则见 `code_format.md`。", "",
                          "## 分类统计", ""]
        for category, count in by_category.most_common():
            question_lines.append(f"- {category}: {count}")
        question_lines += ["", "## 主题分布", ""]
        for topic, count in by_topic.most_common():
            question_lines.append(f"- {topic}: {count}")

        manifest_rows = []
        with zipfile.ZipFile(out, "w", allowZip64=True) as zf:
            added_images: set[str] = set()
            for row in rows:
                cats = categories(row)
                question_lines += ["", "---", "",
                    f"## {row['paper']} {row['session']} Q{row['q']}", "",
                    f"- ID: `{row['id']}`", f"- Component: {row['component']} — {row['component_name']}",
                    f"- Topic: {row['topic_name']}", f"- Type: {', '.join(cats)}",
                    f"- Marks: {row['marks'] if row['marks'] is not None else '—'}"]
                parts = code_parts(row)
                if parts:
                    question_lines.append(f"- Code parts: {', '.join(parts)}")
                question_lines.append("")
                if not slim and row["image"]:
                    source = ASSETS / row["image"]
                    arc = f"{package}/images/{row['image']}"
                    if source.is_file() and arc not in added_images:
                        zf.write(source, arc, compress_type=zipfile.ZIP_STORED)
                        added_images.add(arc)
                    if source.is_file():
                        question_lines += [f"![Question image](images/{row['image']})", ""]
                question = question_md.question_text(row)
                markscheme = question_md.scheme_text(row)
                question_lines += ["### Question", "", question.strip(), "", "### Mark scheme", "", markscheme.strip(), ""]
                manifest_rows.append({
                    "id": row["id"], "paper": row["paper"], "session": row["session"],
                    "question": row["q"], "component": row["component"], "topic": row["topic_name"],
                    "categories": "; ".join(cats), "code_parts": "; ".join(code_parts(row)),
                    "marks": row["marks"], "q_quality": row["q_quality"] or "", "image": row["image"] or "",
                })

            questions_md = tmp / "code_questions.md"
            questions_md.write_text("\n".join(question_lines).rstrip() + "\n", encoding="utf-8")
            format_md = tmp / "code_format.md"
            format_md.write_text(format_guide(), encoding="utf-8")
            manifest = tmp / "manifest.csv"
            with manifest.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(manifest_rows[0]))
                writer.writeheader()
                writer.writerows(manifest_rows)
            zf.write(questions_md, f"{package}/code_questions.md", compress_type=zipfile.ZIP_DEFLATED)
            zf.write(format_md, f"{package}/code_format.md", compress_type=zipfile.ZIP_DEFLATED)
            zf.write(manifest, f"{package}/manifest.csv", compress_type=zipfile.ZIP_DEFLATED)
        print(f"Created: {out}")
        print(f"Questions: {len(rows)}; images: {len(added_images)}")
        print("Categories: " + "; ".join(f"{name}={count}" for name, count in by_category.most_common()))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--slim", action="store_true", help="export a 26-question, text-only representative pack")
    main(slim=parser.parse_args().slim)
