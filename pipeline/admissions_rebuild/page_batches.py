#!/usr/bin/env python3
"""Hand the OCR pages the split cannot use to the transcriber, then keep its fixes.

    python3 pipeline/admissions_rebuild/page_batches.py plan  --out raw/page_batches/run1
    python3 pipeline/admissions_rebuild/page_batches.py apply --out raw/page_batches/run1

plan   splits the bank as it stands (page_fixes.json applied) into a scratch
       file, not over questions_adm.json, and compares it with the tracked
       split: a question missing, whose answer letter is not among its options,
       whose text is less than half as long, or which shares under half its
       words with the tracked question (a shift), marks its pages (as the tracked
       split records them). TMUA worked answers missing a "Question N" heading
       mark the page of the PDF where it is printed (not the contents page);
       a missing question also marks its neighbours' pages, where its option
       run most often went. Each page is rendered
       from its PDF, its current text copied beside it, and the pages batched
       for the transcriber agent (.claude/agents/transcriber.md), which reads
       an image and a text and returns the corrected text as JSON.
apply  reads agent_NN.result.json, keeps a page only if every <img> of the
       OCR text survives and the text did not shrink by more than a third, and
       writes the pages to page_fixes.json. Rerun split_admissions.py and
       attach_ms.py afterwards; plan again for what is still wrong.
"""
import argparse, datetime, json, os, re, sys, tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))
from lib import paths  # noqa: E402
from pipeline.admissions_rebuild import page_fixes, split_admissions  # noqa: E402
from pipeline.admissions_rebuild.reocr_pages import needs_fix, pdf_for  # noqa: E402

IMG = re.compile(r"<img[^>]+>")
PROMPT = """修正入学考试卷一页的识别文本。依次处理下列页面,每页先用 Read 打开图片,再打开识别文本。

对照图片,只做这几类改动:
1. 每道题以题号开头,题号与图片一致,写在该题第一行行首,如 "17 The table below ..."。
2. 每个选项单独一行,以字母加空格开头,如 "C 3 and 4 only"。选项是图形时写 "C (图形选项)";
   选项在表格里时,把表格改写成这样的行,不再保留该表格。
3. 补上识别漏掉的句子、数字、陈述编号("1 ...", "2 ...");改正明显的识别错字。
其余内容一律原样保留:<img> 标签、<table> 表格、$...$ 公式、段落顺序都不要改写,也不要删除。
题号以外的页眉页脚、"BLANK PAGE" 不要补。
页面后若注明"重点核对",先解决所列问题;选项只在图中以字母标出时,写 "A (图中的点 A)" 这样的行。

页面:
{pages}

整个回复只输出一个 JSON 对象,键为上面每页方括号里的键,值为修正后的整页文本:
{{"键1": "...", "键2": "..."}}
"""


def drop_option_tables(text):
    """The transcriber writes a table's options out as lines and keeps the
    table too; split_admissions turns both into option runs and makes a
    phantom question of the second. A lettered table followed by the same
    letters as lines is dropped."""
    def conv(m):
        rows = [[re.sub(r"<[^>]+>", " ", c).strip() for c in split_admissions.CELLRE.findall(r)]
                for r in split_admissions.ROWRE.findall(m.group(0))]
        letters = [r[0] for r in rows if r and re.fullmatch(r"[A-H]", r[0])]
        if len(letters) < 2 or len(letters) < len(rows) - 1:
            return m.group(0)
        after = re.findall(r"(?m)^([A-H])\s", text[m.end():m.end() + 40 * len(rows) + 400])
        return "" if after[:len(letters)] == letters else m.group(0)
    return split_admissions.TABLERE.sub(conv, text)


WA_PROMPT = """修正 TMUA 答案解析(worked answers)一页的识别文本。依次处理下列页面,每页先用 Read 打开图片,再打开识别文本。

对照图片,只做这几类改动:
1. 图片中每道题解析开头印有 "Question N" 的,文本中也要有单独一行 "## Question N",放在该题解析之前,N 与图片一致。
2. 补上识别漏掉的句子、数字;改正明显的识别错字。
其余内容一律原样保留:<img> 标签、<table> 表格、$...$ 公式、段落顺序都不要改写,也不要删除。
页眉页脚不要补。

页面:
{pages}

整个回复只输出一个 JSON 对象,键为上面每页方括号里的键,值为修正后的整页文本:
{{"键1": "...", "键2": "..."}}
"""


def key_of(path):
    return os.path.relpath(path, paths.BANK_OCR).replace(os.sep, "/")


def words(t):
    t = re.sub(r"<[^>]+>|\$[^$]*\$|!\[[^]]*\]\([^)]*\)", " ", t or "")
    return re.findall(r"[a-z]{3,}", t.lower())


def same_question(a, b):
    """The two texts share most of their words (order ignored): the split put
    the tracked question under this number, not a neighbour."""
    wa, wb = set(words(a)), set(words(b))
    if len(wa) < 5 or len(wb) < 5:
        return True
    return len(wa & wb) >= 0.5 * min(len(wa), len(wb))


def split_now():
    """Split into a scratch file; the tracked questions_adm.json is not touched."""
    tmp = tempfile.mktemp(suffix=".json")
    out, split_admissions.OUT = split_admissions.OUT, tmp
    try:
        import contextlib, io
        with contextlib.redirect_stdout(io.StringIO()):
            split_admissions.main()
        return json.load(open(tmp))
    finally:
        split_admissions.OUT = out
        os.path.exists(tmp) and os.remove(tmp)


def worked_answer_pages():
    """Pages of worked-answer PDFs printing a Question N that attach_ms misses."""
    import pymupdf
    from pipeline.admissions_rebuild import attach_ms
    root = attach_ms.ROOT
    want = {}
    for d in sorted(os.listdir(root)):
        m = re.match(r"TMUA-(\w+)-paper-(\d)-worked-answers", d)
        if not m:
            continue
        text = "".join(page_fixes.read_page(os.path.join(root, d, f)) + "\n"
                       for f in sorted(os.listdir(os.path.join(root, d)))
                       if re.match(r"page_\d+\.md$", f))
        have = {int(h.group(1)) for h in attach_ms.HEAD.finditer(text)}
        lost = [n for n in range(1, 21) if n not in have]
        if not lost:
            continue
        doc = pymupdf.open(os.path.join(paths.BANK, "TMUA", "worked_answers", d + ".pdf"))
        for n in lost:
            for p in range(len(doc)):
                heads = re.findall(r"(?m)^\s*Question\s+(\d+)\s*$", doc[p].get_text())
                if heads == [str(n)]:              # not the contents page, which lists them all
                    want.setdefault(("wa", d), set()).add(p + 1)
                    break
    return want


def plan(a):
    ref = json.load(open(os.path.join(paths.ADM, "questions_adm.json")))
    new = {(q["exam"], str(q["year"]), str(q.get("paper")), q["q"]): q for q in split_now()}
    pages, hints, shifted = {}, {}, set()
    by = {(q["exam"], str(q["year"]), str(q.get("paper")), q["q"]): q for q in ref}
    for k, q in by.items():
        n = new.get(k)
        why = ("整题没有切出来(题号或选项行缺失)" if n is None else
               f"没有找到选项行(答案为 {n.get('answer')})" if needs_fix(n) else
               "文本比旧版短一半以上(可能缺句子或题号)"
               if len(n.get("text", "")) < 0.5 * len(q.get("text", "")) else
               "切出的内容与该题不符(前面可能缺一个题号,后面的题依次错位)"
               if not same_question(n["text"], q["text"]) else None)
        if why and why.startswith("切出的内容"):
            if k[:3] in shifted:                    # only the first of a run of shifted questions
                continue
            shifted.add(k[:3])
        if why:
            pdf, out = pdf_for(q)
            pages.setdefault((pdf, out), set()).update(q["pages"])
            for p in q["pages"]:
                hints.setdefault((out, p), []).append(f"第 {q['q']} 题{why}")
            if n is None or k[:3] in shifted:       # its run was lost, most often a page earlier
                for j in (q["q"] - 1, q["q"] + 1):
                    pages[(pdf, out)].update(by.get(k[:3] + (j,), {}).get("pages", []))
    for (_, d), ps in worked_answer_pages().items():
        pdf = os.path.join(paths.BANK, "TMUA", "worked_answers", d + ".pdf")
        pages.setdefault((pdf, os.path.join(paths.BANK_OCR, "TMUA", "worked_answers", d)), set()).update(ps)

    import pymupdf
    os.makedirs(os.path.join(a.out, "img"), exist_ok=True)
    os.makedirs(os.path.join(a.out, "txt"), exist_ok=True)
    items = []
    for (pdf, out), ps in sorted(pages.items()):
        doc = pymupdf.open(pdf)
        for p in sorted(ps):
            md = os.path.join(out, f"page_{p:04d}.md")
            if not os.path.exists(md) or p > len(doc):
                continue
            key = key_of(md)
            slug = key.replace("/", "__")[:-3]
            img = os.path.join(a.out, "img", slug + ".png")
            doc[p - 1].get_pixmap(dpi=a.dpi, colorspace=pymupdf.csGRAY).save(img)
            txt = os.path.join(a.out, "txt", slug + ".md")
            open(txt, "w", encoding="utf-8").write(page_fixes.read_page(md))
            items.append({"key": key, "image": os.path.abspath(img), "text": os.path.abspath(txt),
                          "hint": ";".join(hints.get((out, p), []))})
    batches = []
    for kind in (False, True):                      # question pages, then worked answers
        its = [it for it in items if ("/worked_answers/" in it["key"]) == kind]
        batches += [its[i:i + a.size] for i in range(0, len(its), a.size)]
    for b, batch in enumerate(batches, 1):
        lines = "\n".join(f"- [{it['key']}] 图片 {it['image']} ;识别文本 {it['text']}"
                          + (f" ;重点核对:{it['hint']}" if it.get("hint") else "") for it in batch)
        prompt = WA_PROMPT if "/worked_answers/" in batch[0]["key"] else PROMPT
        open(os.path.join(a.out, f"batch_{b:02d}.prompt.txt"), "w", encoding="utf-8").write(
            prompt.format(pages=lines))
    per = a.per_agent
    for g in range(0, len(batches), per):
        names = [f"batch_{b:02d}" for b in range(g + 1, min(g + per, len(batches)) + 1)]
        task = ("依次处理以下批次文件,每个都用 Read 打开并按其中的要求执行:\n"
                + "\n".join(f"{i}. {os.path.abspath(os.path.join(a.out, n + '.prompt.txt'))}"
                            for i, n in enumerate(names, 1))
                + "\n\n整个回复只输出一个 JSON 对象,合并所有批次的结果:{\"页面键\": \"修正后的整页文本\", ...}\n")
        open(os.path.join(a.out, f"agent_{g // per + 1:02d}.task.txt"), "w", encoding="utf-8").write(task)
    json.dump(items, open(os.path.join(a.out, "plan.json"), "w"), ensure_ascii=False, indent=1)
    print(f"{len(pages)} 份文件,{len(items)} 页 → {len(batches)} 批(每批 ≤{a.size})"
          f" → {(len(batches) + per - 1) // per} 个转录员 -> {a.out}")


def apply(a):
    items = {it["key"]: it for it in json.load(open(os.path.join(a.out, "plan.json")))}
    got = {}
    for f in sorted(os.listdir(a.out)):
        if re.match(r"agent_\d+\.result\.json$", f):
            got.update(json.load(open(os.path.join(a.out, f), encoding="utf-8")))
    data = {}
    if os.path.exists(page_fixes.FILE):
        data = json.load(open(page_fixes.FILE, encoding="utf-8"))
    data.setdefault("_说明", "入学考逐页识别文本的人工修正(对照页面图像),键为 raw/bank_ocr 下的页面路径。"
                    "由 page_batches.py apply 写入,split_admissions.py 与 attach_ms.py 读页时优先使用。")
    kept, dropped = 0, []
    today = datetime.date.today().isoformat()
    for key, text in got.items():
        text = drop_option_tables(text or "")
        if key not in items:
            dropped.append(f"{key}: 不在计划中"); continue
        old = open(items[key]["text"], encoding="utf-8").read()
        n0, n1 = (len(split_admissions.tables_to_lines(x)) for x in (old, text))
        if not text or n1 < 0.67 * n0:              # option tables count as their lines
            dropped.append(f"{key}: 变短 {n0} -> {n1}"); continue
        lost = [i for i in IMG.findall(old) if i not in text]
        if lost:
            dropped.append(f"{key}: 丢了 {len(lost)} 个 <img>"); continue
        data[key] = {"text": text, "note": f"转录员对照页面图像修正 {today}"}
        kept += 1
    json.dump(data, open(page_fixes.FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"收到 {len(got)} 页,写入 {kept},退回 {len(dropped)};计划 {len(items)} 页,"
          f"未交回 {len(set(items) - set(got))}")
    for d in dropped:
        print("  " + d)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mode", choices=["plan", "apply"])
    ap.add_argument("--out", required=True)
    ap.add_argument("--size", type=int, default=8, help="每批页数")
    ap.add_argument("--per-agent", type=int, default=3, help="每个转录员的批数")
    ap.add_argument("--dpi", type=int, default=110)
    a = ap.parse_args()
    {"plan": plan, "apply": apply}[a.mode](a)


if __name__ == "__main__":
    main()
