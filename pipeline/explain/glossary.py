#!/usr/bin/env python3
"""The terms 9618 paper 2 questions ask a student to name or define, where the meaning is not
what the words suggest: each with the question as printed and the mark scheme answer.

    python3 pipeline/explain/glossary.py            data/concepts/9618/glossary.html

The list is pipeline/explain/glossary_p2.json, chosen by hand from the paper 2 parts that ask
for a technical term or its meaning (Give the technical term …, Identify the type of …,
Explain the term …). Terms whose name already says what they are (start pointer, breakpoint,
run-time error, integration testing) and terms only paper 1 asks to define (library routine)
are left out. Every question quoted is checked against the bank before the page is written.
Run concept_pages.py build afterwards so the index links the page.
"""
import html, json, os, re, sqlite3, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from lib import paths  # noqa: E402
from pipeline.explain import concept_pages  # noqa: E402

LIST = os.path.join(os.path.dirname(os.path.abspath(__file__)), "glossary_p2.json")

STYLE = """<style>
.gl{background:var(--paper);border:1px solid var(--line);border-radius:10px;padding:16px 18px;display:grid;gap:8px;min-width:0}
.gl h2{margin:0;font-size:1.2rem;font-weight:900;display:flex;flex-wrap:wrap;gap:4px 10px;align-items:baseline}
.gl h2 .zh{font-size:.95rem;font-weight:500;color:var(--ink2)}
.gl .lab{font-size:.75rem;font-weight:700;color:var(--ink2);letter-spacing:.04em}
.gl .q{font-family:var(--mono);font-size:.84rem;line-height:1.65;margin:0}
.gl .q span{color:var(--ink2)}
.gl .ms{font-family:var(--mono);font-size:.88rem;line-height:1.65;margin:0;background:var(--must-bg);color:var(--ink);border-radius:6px;padding:6px 10px}
.gl .note{margin:0}
</style>
"""


def check(items):
    con = sqlite3.connect(os.path.join(paths.DATA, "caie.db"))
    norm = lambda s: re.sub(r"[\s`*]+", " ", s).strip()  # noqa: E731
    for t in items:
        for ref, q in t["asks"]:
            text = con.execute("SELECT COALESCE(question_latex, question_text) FROM questions WHERE id = ?",
                               (ref.split()[0],)).fetchone()
            core = re.sub(r"\s*\[\d+\]$", "", q.split(" — ", 1)[-1]).rstrip(".")
            if not text or norm(core) not in norm(text[0]):
                sys.exit(f"{t['en']}:{ref} 的题目原文对不上")


def main():
    items = json.load(open(LIST, encoding="utf-8"))
    check(items)
    e = html.escape
    cards = []
    for t in items:
        asks = "".join(f'<p class="q"><span>{e(ref)}</span><br>{e(q)}</p>' for ref, q in t["asks"])
        cards.append(f'<section class="gl"><h2>{e(t["en"])}<span class="zh">{e(t["zh"])}</span></h2>'
                     f'<div class="lab">题目怎么问</div>{asks}'
                     f'<div class="lab">评分细则答案</div><p class="ms">{e(t["ms"])}</p>'
                     f'<p class="note">{e(t["note"])}</p></section>')
    body = ('<main>\n<nav class="pager"><a href="index.html">目录</a></nav>\n<header><h1>9618 卷 2 定义题</h1>'
            f'<p class="sub">卷 2 真题明确要求写出名称或解释含义、而含义和字面不一样的 {len(items)} 个术语,'
            '附原题问法与评分细则答案。</p></header>\n' + "\n".join(cards) + "\n</main>\n")
    head = open(os.path.join(concept_pages.SHELL, "head.html"), encoding="utf-8").read().replace("{{TITLE}}", "9618 卷 2 定义题")
    out = os.path.join(concept_pages.RESULT, "glossary.html")
    os.makedirs(concept_pages.RESULT, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write(concept_pages.with_fonts(concept_pages.DOC + head + STYLE + body))
    print(f"{len(items)} 个术语 -> {os.path.relpath(out, paths.ROOT)}")


if __name__ == "__main__":
    main()
