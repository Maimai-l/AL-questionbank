#!/usr/bin/env python3
"""Split the TMUA worked-answer documents into per-question explanations.

    python3 attach_ms.py

Output ms_tmua.json: {"2021-1": {"1": "...markdown...", ...}, ...}

Anchors are `Question N` headings (with or without ## / bold). Contents pages
list "Question 6 ..... 8" style lines — the anchor regex requires the line to
end after the number, so those don't split. Invariant: every paper yields
exactly questions 1..20.
"""
import json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))          # 项目根目录;在任意目录下运行都能找到 lib
from lib import paths  # noqa: E402

ROOT = os.path.join(paths.BANK_OCR, "TMUA", "worked_answers")
OUT = os.path.join(paths.ADM, "ms_tmua.json")
HEAD = re.compile(r"^(?:#+\s*)?\**\s*Question\s+(\d{1,2})\s*\**\s*$", re.M)


def main():
    out, problems = {}, []
    for d in sorted(os.listdir(ROOT)):
        m = re.match(r"TMUA-(\w+)-paper-(\d)-worked-answers", d)
        if not m:
            continue
        year, paper = m.group(1), m.group(2)
        text = ""
        for f in sorted(os.listdir(os.path.join(ROOT, d))):
            if re.match(r"page_\d+\.md$", f):
                text += open(os.path.join(ROOT, d, f), encoding="utf-8").read() + "\n"
        marks = [(int(h.group(1)), h.start(), h.end()) for h in HEAD.finditer(text)]
        qs = {}
        for i, (n, s, e) in enumerate(marks):
            end = marks[i + 1][1] if i + 1 < len(marks) else len(text)
            body = text[e:end].strip()
            if n in qs:
                problems.append(f"{year} P{paper}: Question {n} 出现两次")
            qs[n] = body
        if sorted(qs) != list(range(1, 21)):
            problems.append(f"{year} P{paper}: 题号 {sorted(qs)}")
        short = [n for n, b in qs.items() if len(b) < 100]
        if short:
            problems.append(f"{year} P{paper}: 过短详解 {short}")
        out[f"{year}-{paper}"] = {str(n): b for n, b in sorted(qs.items())}

    json.dump(out, open(OUT, "w"), ensure_ascii=False, indent=1)
    total = sum(len(v) for v in out.values())
    print(f"{len(out)} 份详解,共 {total} 题 -> ms_tmua.json")
    if problems:
        print(f"⚠️  {len(problems)} 处:")
        for p in problems:
            print("  ", p)
    else:
        print("全部 1..20 覆盖,无过短详解")


if __name__ == "__main__":
    main()
