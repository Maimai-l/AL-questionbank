#!/usr/bin/env python3
"""A glossary of the terms that appear in 9618 paper 2, to find the ones a student has never met.

    python3 pipeline/explain/glossary.py            data/concepts/9618/glossary.html

Terms come from the chapter pages (raw/concepts_9618/page/ch_NN.html: the .t spans, with their
Chinese names and mark scheme definitions) and from term_tree.py's terms.json, whose terms
without a page got a Chinese name and a checked definition from subagents
(raw/glossary_9618/out/batch_N.json; keep = false drops a word that is not a term). Each term is
counted in the papers of each component (question and scheme text, whole words, plural allowed;
all-capital terms such as AND or RAM case-sensitive) and shown with one recent question it
appears in. The page lets the reader mark the terms they know and hide them; the marks stay in
the browser. Run concept_pages.py build afterwards so the index links the glossary.
"""
import glob, html, json, os, re, sqlite3, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from lib import paths  # noqa: E402
from pipeline.explain import concept_pages, concepts  # noqa: E402

WORK = os.path.join(paths.RAW, "glossary_9618")
PAPERS = ("2",)
CHAPTERS = range(9, 13)          # the paper 2 syllabus
# terms of other chapters that paper 2 uses in the same sense (a plain word match also finds
# "switch the heaters on", "a music track", a data item called Host ID ...)
OTHER = {"library routine", "integrated development environment (ide)", "breakpoint", "single stepping",
         "report window", "dynamic syntax checking", "prettyprinting", "auto-complete", "context-sensitive prompt",
         "expand/collapse code blocks", "validation", "check digit", "ascii", "character set", "encryption",
         "cipher text", "compiler", "interpreter", "logic expression"}
# terms.json entries that repeat a page concept under another name: counted with it, not listed
SAME = {"bitmap": "bitmap image", "cache": "cache memory", "defragmentation": "defragmentation software",
        "back-up": "backup", "open source": "open source software", "record type": "record",
        "array index": "index (array)", "privacy of data": "data privacy", "integrity of data": "data integrity",
        "non-volatile": "non-volatile storage", "design stage": "design", "peer-to-peer": "peer-to-peer network",
        "client-server": "client-server model", "property": "attribute / property", "sample rate": "sampling rate",
        "passed by reference": "by reference", "normal data": "normal test data", "boundary data": "boundary test data",
        "lan (local area network)": "local area network (lan)", "wan (wide area network)": "wide area network (wan)",
        "utility program": "utility software", "ide (integrated development environment)": "integrated development environment (ide)",
        "data verification": "verification", "data validation": "validation", "dbms": "database management system (dbms)",
        "data manipulation language": "dml (data manipulation language)"}
ZH = {"kernel": "操作系统内核"}
# other ways the papers write a term
ALT = {"two-dimensional array": ["2D array", "2-D array"], "abnormal test data": ["abnormal data", "erroneous data"],
       "extreme test data": ["extreme data"], "normal test data": ["normal data"], "boundary test data": ["boundary data"],
       "state-transition table": ["state transition table"], "state-transition diagram": ["state transition diagram"],
       "finite state machine": ["FSM"], "pre-condition loop": ["pre-condition"], "post-condition loop": ["post-condition"],
       "count-controlled loop": ["count controlled"], "perfective maintenance": ["perfective"],
       "adaptive maintenance": ["adaptive"], "corrective maintenance": ["corrective"],
       "iterative model": ["iterative development"]}
EN = {"fifo": "FIFO", "lcase": "LCASE", "mod": "MOD", "ethernet": "Ethernet", "classes": "class"}

STYLE = """<style>
.gl-bar{display:flex;flex-wrap:wrap;gap:10px;align-items:center}
.gl-bar input[type=search]{flex:1 1 12rem;min-width:0;font:inherit;padding:6px 10px;border:1px solid var(--line);border-radius:8px;background:var(--paper);color:var(--ink)}
.gl-count{font-size:.85rem;color:var(--ink2)}
.gl-ch{display:grid;gap:0;background:var(--paper);border:1px solid var(--line);border-radius:10px;padding:6px 18px 10px}
.gl-ch h2{font-size:1.1rem;font-weight:900;margin:10px 0 4px}
.gl-term{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:2px 12px;padding:10px 0;border-top:1px solid var(--line)}
.gl-term:first-of-type{border-top:0}
.gl-name{font-weight:700;font-size:1.02rem}
.gl-name .zh{font-weight:500;color:var(--ink2);margin-left:8px;font-size:.92rem}
.gl-def{grid-column:1 / -1;font-family:var(--mono);font-size:.84rem;line-height:1.65;color:var(--ink)}
.gl-meta{grid-column:1 / -1;font-size:.8rem;color:var(--ink2)}
.gl-side{display:flex;gap:8px;align-items:center;justify-content:flex-end}
.gl-n{font-size:.78rem;font-weight:700;padding:2px 8px;border-radius:999px;white-space:nowrap}
.gl-n.must{background:var(--must-bg);color:var(--must)}.gl-n.often{background:var(--often-bg);color:var(--often)}.gl-n.know{background:var(--know-bg);color:var(--know)}
.gl-known{font:inherit;font-size:.8rem;border:1px solid var(--line);background:var(--paper);color:var(--ink2);border-radius:6px;padding:2px 8px;cursor:pointer}
.gl-term.is-known .gl-name,.gl-term.is-known .gl-def{opacity:.4}
.gl-term.is-known .gl-known{background:var(--fig-soft);color:var(--fig);border-color:var(--fig)}
</style>
"""

BODY = """<main>
<header>
  <h1>9618 卷 2 术语表</h1>
  <p class="sub">卷 2 大纲(第 9 至 12 章)的全部术语,加上其他章节里卷 2 真题也用到的术语(如 library routine、IDE、断点)。认识的点「认识」,再勾「隐藏认识的」,剩下的就是没见过的。</p>
</header>
<div class="overview">
  <div class="gl-bar">
    <input type="search" id="gl-q" placeholder="搜索英文或中文" aria-label="搜索">
    <label><input type="checkbox" id="gl-hide"> 隐藏认识的</label>
  </div>
  <p class="legend" id="gl-count"></p>
  <p class="legend">份数是这个术语出现在多少份卷 2 真题里(题目或评分细则,共 33 份),红色 15 份以上,橙色 8 至 14 份,灰色 8 份以下。
  「认识」的标记只存在这台设备的浏览器里。</p>
</div>
<div id="gl-list" style="display:grid;gap:18px"></div>
</main>
<script>
(function(){
var DATA=__DATA__, CH=__CHAPTERS__;
var KEY='gl9618-known', known={}, paper='2';
try{known=JSON.parse(localStorage.getItem(KEY)||'{}')}catch(e){}
function save(){try{localStorage.setItem(KEY,JSON.stringify(known))}catch(e){}}
function tier(n){return n>=15?'must':n>=8?'often':'know'}
function esc(s){return String(s).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]})}
var list=document.getElementById('gl-list'),q=document.getElementById('gl-q'),hide=document.getElementById('gl-hide'),cnt=document.getElementById('gl-count');
function render(){
  var s=q.value.trim().toLowerCase(),groups={},shown=0,total=0,unk=0;
  DATA.forEach(function(t){
    var n=t.n[paper]; if(!n) return; total++;
    if(!known[t.en]) unk++;
    if(s&&(t.en+' '+t.zh+' '+t.def).toLowerCase().indexOf(s)<0) return;
    if(hide.checked&&known[t.en]) return;
    (groups[t.ch]=groups[t.ch]||[]).push(t); shown++;
  });
  var out=[];
  Object.keys(groups).sort(function(a,b){return a-b}).forEach(function(ch){
    var items=groups[ch].sort(function(a,b){return b.n[paper]-a.n[paper]||a.en.localeCompare(b.en)});
    out.push('<section class="gl-ch"><h2>第 '+ch+' 章 '+esc(CH[ch]||'')+'</h2>'+items.map(function(t){
      var n=t.n[paper];
      return '<div class="gl-term'+(known[t.en]?' is-known':'')+'" data-en="'+esc(t.en)+'">'+
        '<div class="gl-name">'+esc(t.en)+'<span class="zh">'+esc(t.zh)+'</span></div>'+
        '<div class="gl-side"><span class="gl-n '+tier(n)+'">'+n+' 份</span><button type="button" class="gl-known">认识</button></div>'+
        '<div class="gl-def">'+esc(t.def)+'</div>'+
        '<div class="gl-meta">例:'+esc(t.ex[paper])+'</div></div>';
    }).join('')+'</section>');
  });
  list.innerHTML=out.join('')||'<p class="legend">没有符合的术语。</p>';
  cnt.textContent='共 '+total+' 个术语,其中 '+unk+' 个还没标记为认识;当前显示 '+shown+' 个。';
}
q.addEventListener('input',render);hide.addEventListener('change',render);
list.addEventListener('click',function(e){var b=e.target.closest('.gl-known');if(!b)return;
  var en=b.closest('.gl-term').dataset.en;if(known[en])delete known[en];else known[en]=1;save();render();});
render();
})();
</script>
"""


def page_terms():
    """{lower en: term} from the chapter pages; chapters 9-12 first, then the others."""
    out = {}
    files = sorted(glob.glob(os.path.join(concept_pages.PAGES, "ch_*.html")),
                   key=lambda f: (int(re.search(r"ch_(\d+)", f).group(1)) not in CHAPTERS, f))
    for f in files:                      # the paper's own chapters first: their sense of a term wins
        ch = int(re.search(r"ch_(\d+)", f).group(1))
        for en, d, zh in re.findall(r'<span class="t [a-z ]+" data-en="([^"]+)" data-def="([^"]+)">([^<]*)',
                                    open(f, encoding="utf-8").read()):
            en = html.unescape(en)
            out.setdefault(en.lower(), {"en": en, "zh": zh.strip() or en, "def": html.unescape(d), "ch": ch})
    return out


def bank_terms():
    """Terms from terms.json that the subagents kept, with their Chinese names and definitions."""
    fixed = {}
    for f in sorted(glob.glob(os.path.join(WORK, "out", "batch_*.json"))):
        for x in json.load(open(f, encoding="utf-8")):
            fixed[x["en"].lower()] = x
    out = {}
    for a in json.load(open(concepts.TERMS, encoding="utf-8")):
        x = fixed.get(a["term"].lower())
        if x and x.get("keep", True):
            out[a["term"].lower()] = {"en": a["term"], "zh": x["zh"], "def": x["def"],
                                      "ch": int(a["subsection"].split(".")[0])}
    return out


def norm(en):
    s = re.sub(r"[^a-z0-9]", "", re.sub(r"\s*\(.*?\)", "", en).lower())
    return re.sub(r"(ing|s)$", "", s)


def merged():
    """Page concepts, then bank terms not already there; a bank term spelt differently from a
    page concept (pretty printing / prettyprinting, bios / BIOS (...)) only adds a spelling."""
    terms = page_terms()
    by_norm = {norm(t["en"]): t for t in terms.values()}
    for k, t in bank_terms().items():
        same = terms.get(SAME.get(k, "")) or by_norm.get(norm(t["en"]))
        if same:
            same.setdefault("alt", []).append(t["en"])
        elif k not in terms:
            terms[k] = t
    for t in terms.values():
        t["zh"] = ZH.get(t["en"].lower(), t["zh"])
        t.setdefault("alt", []).extend(ALT.get(t["en"].lower(), []))
        t["en"] = EN.get(t["en"].lower(), t["en"])
    return terms


def pattern(en, alt=()):
    names = []
    for e in (en, *alt):
        core = re.sub(r"\s*\(.*?\)", "", e).strip()
        names += [n.strip() for part in [core] + re.findall(r"\((.*?)\)", e) for n in part.split(" / ") if len(n.strip()) > 1]
    alts = []
    for n in names:
        body = r"(?<![A-Za-z0-9])" + re.escape(n) + r"(?:s|es)?(?![A-Za-z0-9])"
        alts.append(body if re.fullmatch(r"[A-Z0-9/\-]+", n) else "(?i:" + body + ")")
    return re.compile("|".join(alts))


def main():
    terms = merged()
    con = sqlite3.connect(os.path.join(paths.DATA, "caie.db"))
    rows = con.execute("SELECT id, qp_pdf, component, COALESCE(question_latex, question_text, '') || ' ' || "
                       "COALESCE(ms_latex, ms_text, '') FROM questions WHERE syllabus = '9618' "
                       "ORDER BY year DESC, id").fetchall()
    data = []
    for key, t in terms.items():
        if t["ch"] not in CHAPTERS and key not in OTHER:
            continue
        pat, seen, n, ex = pattern(t["en"], t.get("alt", ())), set(), {p: 0 for p in PAPERS}, {}
        for qid, pdf, comp, text in rows:
            if comp in n and pdf not in seen and pat.search(text):
                seen.add(pdf)
                n[comp] += 1
                ex.setdefault(comp, qid)
        if any(n.values()) or t["ch"] in CHAPTERS:
            data.append({k: v for k, v in {**t, "n": n, "ex": ex}.items() if k != "alt"})
    titles = {}
    for f in glob.glob(os.path.join(concept_pages.PAGES, "ch_*.html")):
        m = re.search(r"<h1>第 (\d+) 章 (.*?)</h1>", open(f, encoding="utf-8").read())
        if m:
            titles[m.group(1)] = re.sub(r"<[^>]+>", "", m.group(2))
    data.sort(key=lambda t: (t["ch"], t["en"].lower()))
    head = open(os.path.join(concept_pages.SHELL, "head.html"), encoding="utf-8").read().replace("{{TITLE}}", "9618 卷 2 术语表")
    body = BODY.replace("__DATA__", json.dumps(data, ensure_ascii=False)).replace(
        "__CHAPTERS__", json.dumps(titles, ensure_ascii=False))
    nav = '<nav class="pager"><a href="index.html">目录</a></nav>'
    body = body.replace("<main>", "<main>\n" + nav, 1)
    out = os.path.join(concept_pages.RESULT, "glossary.html")
    os.makedirs(concept_pages.RESULT, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write(concept_pages.with_fonts(concept_pages.DOC + head + STYLE + body))
    for p in PAPERS:
        print(f"卷 {p}: {sum(1 for t in data if t['n'][p])} 个术语")
    print(f"-> {os.path.relpath(out, paths.ROOT)}")


if __name__ == "__main__":
    main()
