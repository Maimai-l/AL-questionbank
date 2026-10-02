"""Reading documents for a set (docs/data-manager.md, F6): the mark schemes and the worked
explanations, each one self-contained HTML page with KaTeX inlined, so a downloaded copy
renders offline."""
import base64
import html
import json
import os
import re

from lib import db, paths
from manager import bank

KATEX = os.path.join(paths.ASSETS, "vendor", "katex")
_katex = None


def _katex_assets():
    """KaTeX css with its woff2 fonts as data URIs, plus the two scripts."""
    global _katex
    if _katex is None:
        css = open(os.path.join(KATEX, "katex.min.css"), encoding="utf-8").read()

        def font(m):
            with open(os.path.join(KATEX, "fonts", m.group(1)), "rb") as f:
                return "url(data:font/woff2;base64," + base64.b64encode(f.read()).decode() + ") format(\"woff2\")"
        css = re.sub(r'url\(fonts/([^)]+\.woff2)\) format\("woff2"\)', font, css)
        css = re.sub(r',\s*url\(fonts/[^)]+\.(woff|ttf)\) format\("(woff|truetype)"\)', "", css)
        js = "".join(open(os.path.join(KATEX, n), encoding="utf-8").read() + "\n"
                     for n in ("katex.min.js", "auto-render.min.js"))
        _katex = (css, js)
    return _katex


STYLE = """
:root { color-scheme: light; --fg: #191919; --muted: #666; --line: #d9d9d9; --bg: #fff; --band: #f2f2f2; }
@media (prefers-color-scheme: dark) { :root { color-scheme: dark; --fg: #ededed; --muted: #a6a6a6; --line: #35373c; --bg: #131315; --band: #1f1f22; } }
body { margin: 0; background: var(--bg); color: var(--fg); font: 15px/1.7 -apple-system, "PingFang SC", "Noto Sans SC", sans-serif; }
main { max-width: 820px; margin: 0 auto; padding: 40px 24px 80px; }
h1 { font-size: 26px; margin: 0 0 4px; }
.sub { color: var(--muted); font-size: 13px; margin-bottom: 32px; }
section { padding: 24px 0; border-top: 1px solid var(--line); }
h2 { font-size: 17px; margin: 0 0 12px; display: flex; gap: 12px; align-items: baseline; }
h2 small { color: var(--muted); font-weight: 400; font-size: 13px; }
table { border-collapse: collapse; width: 100%; font-size: 14px; }
td { padding: 6px 8px; vertical-align: top; border-bottom: 1px solid var(--line); }
td.code { white-space: nowrap; font-family: ui-monospace, Menlo, monospace; font-size: 13px; width: 64px; }
td { white-space: pre-line; }
td.guide { color: var(--muted); font-size: 13px; width: 38%; }
tr.part td { background: var(--band); font-weight: 600; }
h3 { font-size: 15px; margin: 16px 0 6px; }
ul { margin: 6px 0; padding-left: 20px; color: var(--muted); font-size: 14px; }
p { margin: 0 0 8px; }
.katex-display { overflow-x: auto; overflow-y: hidden; }
"""


def _rows(ids):
    con = db.connect()
    by = {}
    for i in range(0, len(ids), 500):
        chunk = ids[i:i + 500]
        for r in con.execute(f"SELECT * FROM questions WHERE id IN ({','.join('?' * len(chunk))})", chunk):
            by[r["id"]] = r
    return [by[q] for q in ids if q in by]


def _e(t):
    return html.escape(t or "", quote=False)


def _md(text):
    """Paragraphs and **bold**, as the admissions solutions are written."""
    out = []
    for p in re.split(r"\n{2,}", text or ""):
        if p.strip():
            out.append("<p>" + re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", _e(p.strip())).replace("&lt;br&gt;", "<br>") + "</p>")
    return "".join(out)


def _page(title, sub, body):
    css, js = _katex_assets()
    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{_e(title)}</title><style>{css}</style><style>{STYLE}</style></head>
<body><main><h1>{_e(title)}</h1><div class="sub">{_e(sub)}</div>{body}</main>
<script>{js}</script>
<script>renderMathInElement(document.body, {{delimiters: [{{left: '$$', right: '$$', display: true}}, {{left: '$', right: '$', display: false}}], throwOnError: false}});</script>
</body></html>"""


def _head(i, r):
    return (f'<h2><span>{i:02d}</span><span>{_e(bank.paper_code(r))} Q{r["q"]}</span>'
            f'<small>{r["marks"]} 分</small></h2>')


def scheme(s):
    rows = _rows(s["items"])
    parts = []
    for i, r in enumerate(rows, 1):
        if r["syllabus"] in bank.CIE:
            trs = []
            for x in bank.scheme_rows(r["ms_latex"] or r["ms_text"]):
                if x["part"]:
                    trs.append(f'<tr class="part"><td colspan="3">{_e(x["part"])}</td></tr>')
                trs.append(f'<tr><td class="code">{_e(x["code"])}</td><td>{_e(x["answer"])}</td>'
                           f'<td class="guide">{_e(x["guide"])}</td></tr>')
            body = f'<table>{"".join(trs)}</table>'
        else:
            body = _md(r["ms_latex"] or r["ms_text"])
        parts.append(f"<section>{_head(i, r)}{body}</section>")
    marks = sum(r["marks"] or 0 for r in rows)
    return _page(f'{s["name"]} 评分细则', f"{len(rows)} 题 {marks} 分", "".join(parts))


def explanation(s):
    rows = _rows(s["items"])
    parts, n = [], 0
    for i, r in enumerate(rows, 1):
        if not r["explanation"]:
            continue
        n += 1
        ex = json.loads(r["explanation"])
        body = []
        for p in ex.get("parts", []):
            body.append(f'<h3>{_e(p.get("label") or "解答")}</h3>')
            if p.get("approach"):
                body.append(f'<p>{_e(p["approach"])}</p>')
            if p.get("points"):
                body.append("<table>" + "".join(
                    f'<tr><td class="code">{_e(str(pt.get("mark", "")))}</td><td>{_e(pt.get("point"))}</td>'
                    f'<td class="guide">{_e(pt.get("why"))}</td></tr>' for pt in p["points"]) + "</table>")
            if p.get("pitfalls"):
                body.append("<ul>" + "".join(f"<li>{_e(x)}</li>" for x in p["pitfalls"]) + "</ul>")
        parts.append(f'<section>{_head(i, r)}{"".join(body)}</section>')
    return _page(f'{s["name"]} 详解', f"{n} / {len(rows)} 题有详解", "".join(parts))


def counts(s):
    rows = _rows(s["items"])
    return {"scheme": len(rows), "explanation": sum(1 for r in rows if r["explanation"])}
