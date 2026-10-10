#!/usr/bin/env python3
"""One review page per 9618 textbook chapter, written by subagents from the concept lists of
concepts.py: a sentence to remember per section, a diagram, the concepts with their English
mark scheme wording, the calculations and comparisons the papers ask for, and the processes
behind them in sections that open on a click.

    python3 pipeline/explain/concept_pages.py plan --chapters 2-8     raw/concepts_9618/page_NN.md
    (a subagent per chapter writes raw/concepts_9618/page/ch_NN.html, the <main> of the page)
    python3 pipeline/explain/concept_pages.py count KEYWORD [KEYWORD* ...] [--chapter N]
    python3 pipeline/explain/concept_pages.py ms N KEYWORD                mark scheme lines of chapter N
    python3 pipeline/explain/concept_pages.py check [--chapters 2-8] [--render]
    python3 pipeline/explain/concept_pages.py build                       data/concepts/9618/*.html
    python3 pipeline/explain/concept_pages.py zip                         exports/9618复习页.zip

raw/concepts_9618/page/ch_01.html is the model the subagents follow. The page shell (styles,
the pop-up English definitions) is assets/concepts/head.html and tail.html; build wraps each
chapter in it and writes an index. The pages load nothing from outside: styles, scripts and SVG
are inline, and Noto Sans SC and JetBrains Mono are embedded, cut down to the characters each
page uses (the full fonts are downloaded once into raw/fonts/; fonttools and brotli needed).
"""
import argparse, base64, glob, html, io, json, os, re, sqlite3, subprocess, sys, tempfile, urllib.request, zipfile
from html.parser import HTMLParser

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from lib import paths  # noqa: E402

WORK = os.path.join(paths.RAW, "concepts_9618")
PAGES = os.path.join(WORK, "page")
OUT = os.path.join(WORK, "out")
SHELL = os.path.join(paths.ASSETS, "concepts")
RESULT = os.path.join(paths.DATA, "concepts", "9618")
DOC = ('<!doctype html>\n<html lang="zh-CN">\n<meta charset="utf-8">\n'
       '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n')
PAPER = {n: (1 if n <= 8 else 2 if n <= 12 else 3 if n <= 18 else 4) for n in range(1, 21)}
LEVEL = {1: "AS", 2: "AS", 3: "A2", 4: "A2"}
TIERS = {"must", "often", "know"}
# Paper 2 (chapters 9-12) is mostly pseudocode: what the model page does not show.
CODE = """
## 伪代码与程序(本章适用)

- 伪代码写在 `<pre class="code">` 里,关键字(DECLARE、IF、THEN、ENDIF、FOR、NEXT、WHILE、ENDWHILE、REPEAT、UNTIL、
  CASE OF、OTHERWISE、ENDCASE、PROCEDURE、FUNCTION、RETURNS、RETURN、CALL、BYVAL、BYREF、OPENFILE、READFILE、
  WRITEFILE、CLOSEFILE、INPUT、OUTPUT 等)用 `<b>` 包起来,注释(`//` 起)用 `<i>`,要强调的一行用 `<mark>`。
  `<pre>` 里的 `<`、`>`、`&` 写成 `&lt;`、`&gt;`、`&amp;`,赋值箭头写 `←`。
- 写法以教材本章与评分细则为准(剑桥 9618 伪代码指南):缩进 4 格,THEN、ELSE 与 CASE 的分支缩进 2 格;
  数组 `ARRAY[1:10] OF INTEGER`,字符串拼接用 `&`,整除与取余用 `DIV`、`MOD`。每段代码都要能照着手工执行出正确结果。
- 追踪表用 `.cmp` 表格,逐行写出变量的变化;算法过程用 `.flow`,流程图可以画 SVG(按标准符号:圆角框开始结束、
  平行四边形输入输出、矩形处理、菱形判断)。
- 每节的 `.how` 优先放真题常考的写法:完整的模板代码(如线性查找、冒泡排序、读写文件、栈和队列的操作),
  以及评分细则的给分点。代码只写最典型的一种写法,其他可接受的写法用一句话说明。
"""
FONTS = os.path.join(paths.RAW, "fonts")
FONT_SRC = "https://raw.githubusercontent.com/google/fonts/main/ofl/"
FONT_FILES = {"Noto Sans SC": "notosanssc/NotoSansSC%5Bwght%5D.ttf",
              "JetBrains Mono": "jetbrainsmono/JetBrainsMono%5Bwght%5D.ttf"}

TASK = """# 9618 第 {n} 章:复习页

为第 {n} 章写一页复习材料,结构、组件、语气、详略完全照第 1 章的成品。读者把它当作背诵用的材料:
要一眼看出先背什么,读得顺,图能直接看懂。不写成讲义,也不写成一条一条的列表。

## 材料

1. 第 1 章成品(范本):`raw/concepts_9618/page/ch_01.html`。先完整读一遍,所有写法都以它为准。
2. 本章必须收进去的概念(英文名、中文名、评分细则式英文定义):`raw/concepts_9618/out/ch_{n:02d}.json`。
3. 本章候选术语与评分细则原文:`raw/concepts_9618/ch_{n:02d}.md`。
4. 教材本章:`{book}`。文件长,用 offset/limit 分段读;先用 Grep 找 `^#` 看小节结构。
5. 查真题:
   - `python3 pipeline/explain/concept_pages.py count 关键词 [同义词 ...]` 输出含这些词的 9618 试卷份数(共 130 份)。
     按整词匹配(可带复数),词尾加 * 匹配词的开头(如 `compress*`);加 `--chapter {n}` 只数本章的题。
     这个概念也在别的章出现时(如 AI、switch),以本章的份数为准。
   - `python3 pipeline/explain/concept_pages.py ms {n} 关键词` 列出本章题目评分细则中含该词的行。

## 页面结构(照范本)

- `<main>` 开头:`<header>` 中 `<h1>第 {n} 章 中文章名</h1>` 和 `<p class="sub">9618 Computer Science · {level} 卷 {paper}</p>`。
- 总览 `.overview`:「本章先背哪些」列出全部概念,「本章要会做哪些题」列出计算、比较、过程类题型;
  都按三档分行(必考 / 常考 / 了解),每个 chip 链接到所在小节的 id。最后一句 `.legend` 与范本相同。
- 每个小节一个 `<section id="...">`:
  1. `<h2><span class="num">大纲小节号</span>中文小标题</h2>`;
  2. `<p class="core">`:一句话核心,读完就知道这一节讲什么;
  3. 至少一张图(`<figure>`),把这一节最关键的结构、过程或对比画出来;
  4. `<p class="detail">`:概念的中文解释,关键说法后面用 `<span class="kw">(English wording)</span>` 附评分细则的英文原话,
     英文要多,方便背英文;
  5. 真题常考的计算、比较、过程放 `<div class="how">`(带三档标签的小标题);
  6. 教材里有、能帮助理解但不必一眼看到的过程和细节,放 `<details class="more">`,summary 里带三档标签。
- 小节按教材顺序;内容多的小节拆开,每节不要太长。

## 概念与分档

- json 里的每个概念都要出现,第一次出现写成
  `<span class="t 档" data-en="English term" data-def="评分细则式英文定义">中文名<span class="en">English term</span></span>`,
  档是 `must`、`often`、`know` 之一。只是英文缩写的概念(如 ASCII)不写 `.en`。
- 分档:用 count 数这个概念出现的试卷份数(用最能代表它的英文词,必要时加同义词)。15 份以上 must(必考),
  8 至 14 份 often(常考),8 份以下 know(了解)。题型(计算、比较等)的分档同样按 count 的结果。
- 教材与真题中重要、json 里没有的概念可以补,同样写成 `.t`。

## 图

- 优先用范本里的组件:`.bits`(位与位权)、`.boxes`、`.flow`(过程)、`.chain`、`.cmp` 表格(放在 `.tbl` 里)、
  `.strip`、`.dl`、`.add`(竖式)、`.pref`、`.formula`。
- 需要画图时写内联 SVG:viewBox 宽不超过 340,文字不小于 11;颜色只用范本里的类(`fg`、`fgs`、`ln`、`p1`–`p4`)
  或 `fill="var(--fig)"` 这类变量,不写任何具体颜色值。
- 图里的每个数字、例子都要算对、与教材一致。

## 规定

- 只写 `<main>…</main>` 片段,不写 `<html>`、`<head>`、`<style>`、`<script>`;不用 `<ul>`、`<ol>`、`<li>`。
- 用中文写,英文只出现在 `.en`、`.kw`、`data-en`、`data-def`、图中标注和公式里。
- 内容以教材和评分细则为准,不确定的不写。
- 写到 `raw/concepts_9618/page/ch_{n:02d}.html`,然后运行
  `python3 pipeline/explain/concept_pages.py check --chapters {n} --render`,有报错就改,直到通过。
- 不改其他文件。最后回复一行:小节数和概念数。
"""


def chapters():
    out = {}
    for p in sorted(glob.glob(os.path.join(paths.BOOKS, "9618", "9618_ch*.md"))):
        m = re.match(r"9618_ch(\d+)_", os.path.basename(p))
        out[int(m.group(1))] = p
    return out


def span(text):
    a, _, b = text.partition("-")
    return list(range(int(a), int(b or a) + 1))


def con():
    return sqlite3.connect(os.path.join(paths.DATA, "caie.db"))


def plan(a):
    books = chapters()
    for n in span(a.chapters):
        with open(os.path.join(WORK, f"page_{n:02d}.md"), "w", encoding="utf-8") as f:
            task = TASK.format(n=n, book=os.path.relpath(books[n], paths.ROOT), level=LEVEL[PAPER[n]], paper=PAPER[n])
            if PAPER[n] in (2, 4):
                task = task.replace("\n## 规定\n", CODE + "\n## 规定\n", 1)
            f.write(task)
        print(f"page_{n:02d}.md")


def count(a):
    """Papers whose question or mark scheme contains a keyword as a whole word (plural allowed);
    a keyword ending in * matches the start of a word (compress* finds compression)."""
    where, args = "syllabus='9618'", []
    if a.chapter:
        where, args = where + " AND topic=?", [str(a.chapter)]
    pat = re.compile("|".join(r"(?<![A-Za-z0-9])" + (re.escape(k[:-1]) if k.endswith("*") else
                                                     re.escape(k) + r"(?:s|es)?(?![A-Za-z0-9])")
                              for k in a.keywords), re.I)
    papers, hit = set(), set()
    for pdf, text in con().execute(f"SELECT qp_pdf, COALESCE(question_text,'') || ' ' || COALESCE(ms_text,'') "
                                   f"FROM questions WHERE {where}", args):
        papers.add(pdf)
        if pat.search(text):
            hit.add(pdf)
    print(f"{len(hit)} / {len(papers)} 份试卷")


def ms(a):
    seen = set()
    for qid, text in con().execute("SELECT id, ms_text FROM questions WHERE syllabus='9618' AND topic=? "
                                   "AND ms_text LIKE ? ORDER BY id", (str(a.chapter), f"%{a.keyword}%")):
        for line in text.splitlines():
            line = line.strip(" •-\t")
            if a.keyword.lower() in line.lower() and line not in seen:
                seen.add(line)
                print(f"{qid}  {line[:220]}")


class Page(HTMLParser):
    VOID = {"br", "img", "input", "meta", "link", "hr", "wbr", "source", "col", "area", "base", "embed", "param", "track"}
    SVG_VOID = {"rect", "circle", "line", "path", "polyline", "polygon", "ellipse", "use", "stop"}

    def __init__(self):
        super().__init__()
        self.stack, self.errs, self.terms, self.cores, self.sections = [], [], [], 0, 0
        self.summary_tag = []

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        cls = (d.get("class") or "").split()
        if tag in ("ul", "ol", "li", "script", "style", "html", "head", "body"):
            self.errs.append(f"不能用 <{tag}>")
        if "t" in cls and tag == "span":
            tier = TIERS & set(cls)
            if len(tier) != 1:
                self.errs.append(f"概念 {d.get('data-en')} 要有且只有一个档:must / often / know")
            if not d.get("data-en") or not d.get("data-def"):
                self.errs.append(f"概念 span 缺 data-en 或 data-def:{d}")
            self.terms.append(d.get("data-en") or "")
        if "core" in cls:
            self.cores += 1
        if tag == "section":
            self.sections += 1
        if tag == "summary":
            self.summary_tag.append(False)
        if "tag" in cls and self.summary_tag:
            self.summary_tag[-1] = True
        for k, v in d.items():
            if k in ("fill", "stroke", "style", "color") and v and re.search(r"#[0-9a-fA-F]{3,8}\b|rgb\(|hsl\(", v):
                self.errs.append(f"<{tag}> 的 {k} 用了具体颜色值 {v[:40]},只能用 var(--…) 或范本里的类")
        if tag not in self.VOID and not (tag in self.SVG_VOID and self.get_starttag_text().rstrip().endswith("/>")):
            self.stack.append(tag)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if self.stack and self.stack[-1] == tag:
            self.stack.pop()

    def handle_endtag(self, tag):
        if tag in self.VOID:
            return
        if not self.stack or self.stack[-1] != tag:
            self.errs.append(f"标签不配对:</{tag}>,当前未闭合的是 <{self.stack[-1] if self.stack else '无'}>")
            if tag in self.stack:
                while self.stack and self.stack.pop() != tag:
                    pass
            return
        self.stack.pop()
        if tag == "summary" and not self.summary_tag.pop():
            self.errs.append("<summary> 里要有三档标签(<span class=\"tag …\">)")


def problems(n):
    path = os.path.join(PAGES, f"ch_{n:02d}.html")
    if not os.path.exists(path):
        return ["还没有结果"]
    text = open(path, encoding="utf-8").read()
    p = Page()
    p.feed(text)
    errs = list(dict.fromkeys(p.errs))
    if p.stack:
        errs.append(f"未闭合的标签:{p.stack[-5:]}")
    if not text.lstrip().startswith("<main>") or not text.rstrip().endswith("</main>"):
        errs.append("文件应只有 <main>…</main>")
    if 'class="overview"' not in text:
        errs.append("缺总览 .overview")
    if p.sections < 2 or p.cores < p.sections:
        errs.append(f"{p.sections} 个 section,{p.cores} 句 .core:每节都要有一句 .core")
    if text.count("<figure") < p.sections:
        errs.append(f"{p.sections} 个 section 只有 {text.count('<figure')} 张图,每节至少一张")
    if f"<h1>第 {n} 章" not in text:
        errs.append(f"<h1> 应以「第 {n} 章」开头")
    have = " | ".join(t.lower() for t in p.terms)
    jpath = os.path.join(OUT, f"ch_{n:02d}.json")
    for x in json.load(open(jpath, encoding="utf-8")) if os.path.exists(jpath) else []:
        core = re.sub(r"\s*\(.*?\)", "", x["term"]).strip().lower()
        if core not in have and core.rstrip("s") not in have:
            errs.append(f"缺概念 {x['term']}(data-en 里要有这个英文名)")
    return errs


def chrome():
    hits = sorted(glob.glob("/opt/pw-browsers/chromium*/chrome-linux/chrome"))
    return os.environ.get("CHROME") or (hits[-1] if hits else None)


def font_path(family):
    url = FONT_SRC + FONT_FILES[family]
    path = os.path.join(FONTS, os.path.basename(url).replace("%5B", "[").replace("%5D", "]"))
    if not os.path.exists(path):
        os.makedirs(FONTS, exist_ok=True)
        print(f"下载 {url}")
        urllib.request.urlretrieve(url, path + ".part")
        os.replace(path + ".part", path)
        lic = os.path.join(FONTS, f"OFL-{family.replace(' ', '')}.txt")
        urllib.request.urlretrieve(FONT_SRC + os.path.dirname(FONT_FILES[family]) + "/OFL.txt", lic)
    return path


def embedded_fonts(text):
    """@font-face rules for the two families, each cut down to the characters in text."""
    from fontTools import subset
    from fontTools.ttLib import TTFont
    chars = "".join(sorted(set(text) | {chr(c) for c in range(32, 127)}))
    rules = []
    for family in FONT_FILES:
        opt = subset.Options()
        opt.flavor, opt.layout_features, opt.name_IDs, opt.notdef_outline = "woff2", ["*"], ["*"], True
        font = TTFont(font_path(family))
        sub = subset.Subsetter(opt)
        sub.populate(text=chars)
        sub.subset(font)
        buf = io.BytesIO()
        font.flavor = "woff2"
        font.save(buf)
        data = base64.b64encode(buf.getvalue()).decode()
        rules.append(f"@font-face{{font-family:\"{family}\";font-weight:100 900;font-display:block;"
                     f"src:url(data:font/woff2;base64,{data}) format(\"woff2\")}}")
    return "<style>" + "\n".join(rules) + "</style>\n"


def with_fonts(page):
    i = page.index("<style>")
    return page[:i] + embedded_fonts(page) + page[i:]


def page_html(n, body):
    title = re.search(r"<h1>(.*?)</h1>", body, re.S)
    title = re.sub(r"<[^>]+>", "", title.group(1)).strip() if title else f"第 {n} 章"
    head = open(os.path.join(SHELL, "head.html"), encoding="utf-8").read()
    tail = open(os.path.join(SHELL, "tail.html"), encoding="utf-8").read()
    return DOC + head.replace("{{TITLE}}", html.escape(f"9618 {title}")) + body + "\n" + tail


PROBE = """<!doctype html><meta charset=utf-8><body style="margin:0"><iframe id=f src="page.html" style="width:375px;height:900px;border:0"></iframe>
<script>f.onload=()=>setTimeout(()=>{const d=f.contentDocument,W=f.contentWindow.innerWidth;
const o=[...d.querySelectorAll('main *')].filter(e=>!e.closest('.tbl,figure')&&e.getBoundingClientRect().right>W+1)
.filter(e=>![...e.children].some(c=>c.getBoundingClientRect().right>W+1)).slice(0,5)
.map(e=>'<'+e.tagName.toLowerCase()+' class='+e.className+'> '+e.textContent.trim().slice(0,30));
const fig=[...d.querySelectorAll('figure,.tbl')].filter(e=>e.scrollWidth>e.clientWidth+1).map(e=>e.textContent.replace(/\\s+/g,' ').trim().slice(0,30));
document.title=JSON.stringify({page:d.documentElement.scrollWidth>W,over:o,scroll:fig})},1500)</script>"""


def render(n):
    exe = chrome()
    if not exe:
        return ["找不到 Chromium,跳过 --render"]
    body = open(os.path.join(PAGES, f"ch_{n:02d}.html"), encoding="utf-8").read()
    with tempfile.TemporaryDirectory() as tmp:
        open(os.path.join(tmp, "page.html"), "w", encoding="utf-8").write(page_html(n, body))
        open(os.path.join(tmp, "probe.html"), "w", encoding="utf-8").write(PROBE)
        dom = subprocess.run([exe, "--headless", "--no-sandbox", "--disable-gpu", "--allow-file-access-from-files",
                              "--window-size=500,900", "--virtual-time-budget=4000", "--dump-dom",
                              "file://" + os.path.join(tmp, "probe.html")], capture_output=True, text=True, timeout=60).stdout
    m = re.findall(r"<title>(.*?)</title>", dom)
    if not m:
        return ["渲染失败,没有拿到结果"]
    r = json.loads(html.unescape(m[-1]))
    errs = [f"手机宽度(375px)下超出屏幕:{x}" for x in r["over"]]
    if r["page"] and not errs:
        errs.append("手机宽度(375px)下页面横向超宽")
    for x in r["scroll"]:
        errs.append(f"这张图或表在手机宽度(375px)下要横向滚动,改窄一些:{x}")
    return errs


def check(a):
    bad = 0
    for n in span(a.chapters):
        errs = problems(n)
        if a.render and not errs:
            errs = render(n)
        for e in errs:
            print(f"ch_{n:02d}: {e}")
        bad += bool(errs)
    print("全部通过" if not bad else f"{bad} 章有问题")


def build(a):
    os.makedirs(RESULT, exist_ok=True)
    done = []
    for n in sorted(chapters()):
        path = os.path.join(PAGES, f"ch_{n:02d}.html")
        if not os.path.exists(path):
            continue
        if problems(n):
            sys.exit(f"ch_{n:02d} 未通过 check")
        body = open(path, encoding="utf-8").read()
        h1 = re.sub(r"<[^>]+>", "", re.search(r"<h1>(.*?)</h1>", body, re.S).group(1)).strip()
        done.append((n, h1, body))
    for i, (n, h1, body) in enumerate(done):
        links = ['<a href="index.html">目录</a>']
        if i:
            links.append(f'<a href="ch_{done[i - 1][0]:02d}.html">← 第 {done[i - 1][0]} 章</a>')
        if i + 1 < len(done):
            links.append(f'<a href="ch_{done[i + 1][0]:02d}.html">第 {done[i + 1][0]} 章 →</a>')
        nav = f'<nav class="pager">{"".join(links)}</nav>'
        body = body.replace("<main>", "<main>\n" + nav, 1).replace("</main>", nav + "\n</main>", 1)
        with open(os.path.join(RESULT, f"ch_{n:02d}.html"), "w", encoding="utf-8") as f:
            f.write(with_fonts(page_html(n, body)))
    rows = []
    for paper in (1, 2, 3, 4):
        links = "".join(f'<a class="chip often" href="ch_{n:02d}.html">{html.escape(t)}</a>'
                        for n, t, _ in done if PAPER[n] == paper)
        if links:
            rows.append(f'<div class="row"><span class="tag know lab">卷 {paper}</span>{links}</div>')
    if os.path.exists(os.path.join(RESULT, "glossary.html")):
        rows.insert(0, '<div class="row"><span class="tag must lab">术语</span>'
                       '<a class="chip must" href="glossary.html">卷 2 定义题:真题要求说出名称或含义的术语</a></div>')
    index = ('<main><header><h1>9618 Computer Science 复习页</h1><p class="sub">每章一页:先背什么、图、英文原话、常考题型</p></header>'
             f'<div class="overview">{"".join(rows)}</div></main>')
    head = open(os.path.join(SHELL, "head.html"), encoding="utf-8").read().replace("{{TITLE}}", "9618 复习页")
    with open(os.path.join(RESULT, "index.html"), "w", encoding="utf-8") as f:
        f.write(with_fonts(DOC + head + index + "\n"))
    print(f"{len(done)} 章 -> {os.path.relpath(RESULT, paths.ROOT)}/")


EXTERNAL = re.compile(r'<link\b|<script[^>]+src=|<img[^>]+src="(?!data:)|@import|url\((?!#|data:)', re.I)



def zip_pages(a):
    files = sorted(glob.glob(os.path.join(RESULT, "*.html")))
    if not files:
        sys.exit("先运行 build")
    for f in files:
        m = EXTERNAL.search(open(f, encoding="utf-8").read())
        if m:
            sys.exit(f"{os.path.basename(f)} 引用了外部资源:{m.group(0)}")
    os.makedirs(paths.EXPORTS, exist_ok=True)
    out = os.path.join(paths.EXPORTS, "9618复习页.zip")
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for f in files:
            z.write(f, os.path.join("9618复习页", os.path.basename(f)))
        for f in sorted(glob.glob(os.path.join(FONTS, "OFL-*.txt"))):
            z.write(f, os.path.join("9618复习页", "字体许可", os.path.basename(f)))
    print(f"{len(files)} 个页面 -> {out}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("plan"); p.add_argument("--chapters", default="1-20"); p.set_defaults(fn=plan)
    p = sub.add_parser("count"); p.add_argument("keywords", nargs="+"); p.add_argument("--chapter", type=int)
    p.set_defaults(fn=count)
    p = sub.add_parser("ms"); p.add_argument("chapter", type=int); p.add_argument("keyword"); p.set_defaults(fn=ms)
    p = sub.add_parser("check"); p.add_argument("--chapters", default="1-20"); p.add_argument("--render", action="store_true")
    p.set_defaults(fn=check)
    p = sub.add_parser("build"); p.set_defaults(fn=build)
    p = sub.add_parser("zip"); p.set_defaults(fn=zip_pages)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
