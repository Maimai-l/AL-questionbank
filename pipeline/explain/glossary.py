#!/usr/bin/env python3
"""9618 paper 2 vocabulary: the terms paper 2 questions and mark schemes use whose meaning a
student needs to answer and cannot work out from the words themselves (library routine,
stub testing, BYREF, rogue value …). Each term has a Chinese explanation, the English
definition to learn, the number of paper 2 papers it appears in, and one sentence quoted
from the bank.

    python3 pipeline/explain/glossary.py            data/concepts/9618/glossary.html

The list is pipeline/explain/glossary_p2.json. Terms only paper 1 uses are left out, and so
are terms whose name already says what they are (flowchart, trace table, breakpoint,
run-time error, integration testing). Every quoted sentence is checked against the bank
before the page is written. Run concept_pages.py build afterwards so the index links the page.
"""
import html, json, os, re, sqlite3, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from lib import paths  # noqa: E402
from pipeline.explain import concept_pages  # noqa: E402

LIST = os.path.join(os.path.dirname(os.path.abspath(__file__)), "glossary_p2.json")
TIERS = [("must", "必考", "8 份卷以上", 8, 99), ("often", "常考", "4 至 7 份卷", 4, 7), ("know", "了解", "1 至 3 份卷", 1, 3)]

STYLE = """<style>
.tier{display:flex;align-items:center;gap:10px;margin:14px 0 -4px;font-size:1rem;font-weight:700}
.tier span{font-size:.85rem;font-weight:500;color:var(--ink2)}
.gl{gap:8px;padding:16px 18px}
.gl h2{margin:0;font-size:1.2rem;font-weight:900;display:flex;flex-wrap:wrap;gap:4px 10px;align-items:baseline}
.gl h2 .zh{font-size:.95rem;font-weight:500;color:var(--ink2)}
.gl h2 .n{margin-left:auto;font-size:.78rem;font-weight:500;color:var(--ink2);font-variant-numeric:tabular-nums}
.gl .note{margin:0}
.gl .def{margin:0;font-family:var(--mono);font-size:.86rem;line-height:1.65;background:var(--bg);border-radius:6px;padding:6px 10px}
.gl .q{margin:0;font-size:.8rem;line-height:1.6;color:var(--ink2)}
.gl .q i{font-style:normal;font-family:var(--mono)}
</style>
"""


def flat(s):
    s = re.sub(r"\\underline\{\\text\{(.*?)\}\}", r"\1", s or "")
    return re.sub(r"[\s`*|$]+", " ", s).strip()


def check(items):
    con = sqlite3.connect(os.path.join(paths.DATA, "caie.db"))
    for t in items:
        qid, src, text = t["quote"]
        row = con.execute("SELECT COALESCE(question_latex, question_text), COALESCE(ms_latex, ms_text) "
                          "FROM questions WHERE id = ? AND component = '2'", (qid,)).fetchone()
        if not row or flat(text) not in flat(row[0 if src == "题目" else 1]):
            sys.exit(f"{t['en']}:{qid} 的{src}原文对不上")


def main():
    items = sorted(json.load(open(LIST, encoding="utf-8")), key=lambda t: -t["papers"])
    check(items)
    e = html.escape
    parts = []
    for cls, name, span, low, high in TIERS:
        group = [t for t in items if low <= t["papers"] <= high]
        parts.append(f'<div class="tier"><span class="tag {cls}">{name}</span>{len(group)} 个<span>出现在 {span}</span></div>')
        for t in group:
            qid, src, text = t["quote"]
            parts.append(f'<section class="gl"><h2>{e(t["en"])}<span class="zh">{e(t["zh"])}</span>'
                         f'<span class="n">{t["papers"]} 份卷</span></h2>'
                         f'<p class="note">{e(t["note"])}</p>'
                         f'<p class="def">{e(t["def"])}</p>'
                         f'<p class="q"><i>{e(qid)}</i> {src}:{e(text)}</p></section>')
    body = ('<main>\n<nav class="pager"><a href="index.html">目录</a></nav>\n<header><h1>9618 卷 2 词汇</h1>'
            f'<p class="sub">卷 2 真题和评分细则里出现、答题时必须知道含义、但从字面看不出意思的 {len(items)} 个术语。'
            '按出现在多少份卷里排序;灰底是要背的英文定义,最后一行是题库原句。</p></header>\n'
            + "\n".join(parts) + "\n</main>\n")
    head = open(os.path.join(concept_pages.SHELL, "head.html"), encoding="utf-8").read().replace("{{TITLE}}", "9618 卷 2 词汇")
    out = os.path.join(concept_pages.RESULT, "glossary.html")
    os.makedirs(concept_pages.RESULT, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write(concept_pages.with_fonts(concept_pages.DOC + head + STYLE + body))
    print(f"{len(items)} 个术语 -> {os.path.relpath(out, paths.ROOT)}")


if __name__ == "__main__":
    main()
