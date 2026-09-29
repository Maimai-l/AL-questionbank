#!/usr/bin/env python3
"""Merge the admissions bank (TMUA / TSA / BMAT) into qb/caie.db.

    python3 merge_admissions.py

Re-runnable: existing TMUA/TSA/BMAT rows are deleted and re-inserted, then
the FTS index rows for them are rebuilt. CAIE rows are never touched.

The re-inserted rows carry the keyword tags of questions_adm.json; the model
tags in pipeline/tags/retag_model.json (topic, topic_parts, topic_source =
'model', ...) are applied again straight after, through tag_batches.write().

Schema: two new columns are added if missing —
    answer  TEXT   the key's letter (or free text for early BMAT)
    qtype   TEXT   'mcq' | 'short'  (NULL for CAIE rows)
    options TEXT   JSON list of the offered letters, e.g. ["A",..,"E"]

Hand corrections checked against the papers (text_fixes.json: a question whose
text went to its neighbour, option fragments of the previous question) replace
the split's text and options before anything else.

Text is converted from Paddle's HTML to what practice.html already renders:
HTML tables become pipe tables, <img> tags become ![](img_tara/...) lines
with the referenced crops copied next to the page, decorative divs die.

Images: every question gets both.
    qb/img_adm/    一题一张原页图(render_adm_imgs.py 裁的),文件名就是题号 ID
    qb/img_tara/   题干里引用的插图裁片
"""
import argparse, html
import json, os, re, shutil, sqlite3, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))          # qb/
from lib import paths
from pipeline.tags import tag_batches
from pipeline.text.answer_lines import strip as strip_answer_lines

QB = paths.DATA                            # 题图写进 data/;CAIE_DATA 可覆盖
DB = paths.DB
ROOT = paths.BANK_OCR
FIXES = os.path.join(paths.ADM, "text_fixes.json")   # 对照原卷的题干修正

COMPONENT_NAMES = {
    ("TMUA", "1"): "Paper 1 (Applications of Mathematical Knowledge)",
    ("TMUA", "2"): "Paper 2 (Mathematical Reasoning)",
    ("TSA", "1"): "Section 1 (Thinking Skills: TARA 前代)",
    ("BMAT", "1"): "Section 1 (Aptitude and Skills: TARA 前代)",
}

ROWRE = re.compile(r"<tr[^>]*>(.*?)</tr>", re.S)
CELLRE = re.compile(r"<td[^>]*>(.*?)</td>", re.S)
TABLERE = re.compile(r"<table\b.*?</table>", re.S)
IMGRE = re.compile(r'<img[^>]+src=["\']([^"\']+)["\'][^>]*/?>')
DIVRE = re.compile(r"</?div[^>]*>")
MARKRE = re.compile(r"<!--[^>]*-->")


def img_dir_for(q):
    if q["exam"] == "TMUA":
        return f"{ROOT}/TMUA/papers/TMUA-{q['year']}-paper-{q['paper']}"
    sub = "TSA_section1" if q["exam"] == "TSA" else "BMAT_section1"
    return f"{ROOT}/TARA/{sub}/papers/{q['exam']}-{q['year']}-S1"


def clean_text(q, copied):
    """Paddle HTML -> practice.html dialect; copy referenced figures."""
    t = q["text"]

    def table(m):
        rows = []
        for row in ROWRE.findall(m.group(0)):
            cells = []
            for c in CELLRE.findall(row):
                c = IMGRE.sub(lambda i: img(i), c)
                cells.append(" ".join(re.sub(r"<[^>]+>", " ", c).split()))
            rows.append(cells)
        if not rows:
            return ""
        w = max(len(r) for r in rows)
        rows = [r + [""] * (w - len(r)) for r in rows]
        out = ["| " + " | ".join(rows[0]) + " |",
               "|" + "---|" * w]
        out += ["| " + " | ".join(r) + " |" for r in rows[1:]]
        return "\n" + "\n".join(out) + "\n"

    def img(m):
        src = m.group(1)
        base = os.path.basename(src)
        srcdir = img_dir_for(q)
        frm = os.path.join(srcdir, src)
        sub = f"{q['exam']}-{q['year']}" + (f"-P{q['paper']}" if q["exam"] == "TMUA" else "")
        dst_rel = f"img_tara/{sub}/{base}"
        dst = os.path.join(QB, dst_rel)
        # the figure may already be in data/ from an earlier run, and raw/bank_ocr
        # (a local OCR cache) need not be there at all
        if os.path.exists(frm) and not os.path.exists(dst):
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy(frm, dst)
        if os.path.exists(dst):
            copied.add(dst_rel)
            return f"\n![]({dst_rel})\n"
        return ""

    t = TABLERE.sub(table, t)
    t = IMGRE.sub(img, t)
    t = DIVRE.sub("", t)
    t = MARKRE.sub("", t)
    t = html.unescape(t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return strip_answer_lines(t)


def qid_of(q):
    if q["exam"] == "TMUA":
        return f"TMUA-{q['year']}-P{q['paper']}-q{q['q']}"
    return f"{q['exam']}-{q['year']}-S1-q{q['q']}"


def apply_fix(q, fixes):
    """The hand correction from text_fixes.json, if there is one."""
    f = fixes.get(qid_of(q))
    if f:
        q = dict(q, text=f["text"], options=f["options"])
    return q


def fix_number(text, n):
    """A printed number that lost its leading digit ("2 Which ..." for 12)."""
    m = re.match(r"(\d{1,2}) ", text)
    if m and int(m.group(1)) != n and str(n).endswith(m.group(1)):
        return f"{n} " + text[m.end():]
    return text


def main():
    qs = json.load(open(os.path.join(paths.ADM, "questions_adm.json")))
    ms_tmua = json.load(open(os.path.join(paths.ADM, "ms_tmua.json")))
    fixes = {k: v for k, v in json.load(open(FIXES)).items() if not k.startswith("_")}

    con = sqlite3.connect(DB)
    cols = [r[1] for r in con.execute("PRAGMA table_info(questions)")]
    for col in ("answer", "qtype", "options"):
        if col not in cols:
            con.execute(f"ALTER TABLE questions ADD COLUMN {col} TEXT")

    con.execute("DELETE FROM questions WHERE syllabus IN ('TMUA','TSA','BMAT')")

    copied = set()
    rows = []
    for q in qs:
        exam, year, paper = q["exam"], q["year"], q["paper"]
        q = apply_fix(q, fixes)
        text = fix_number(clean_text(q, copied), q["q"])
        ans = q.get("answer") or ""
        if exam == "TMUA":
            qid = f"TMUA-{year}-P{paper}-q{q['q']}"
            wa = ms_tmua.get(f"{year}-{paper}", {}).get(str(q["q"]), "")
            ms = f"**答案:{ans}**\n\n" + wa
            image = f"img_adm/{qid}.png"
            nyear = 2017 if year == "specimen" else int(year)
            session = "Specimen" if year == "specimen" else f"October {year}"
            series = "spec" if year == "specimen" else f"t{str(year)[2:]}"
            paper_label = f"TMUA/{paper}"
            pdf = f"bank/TMUA/papers/TMUA-{year}-paper-{paper}.pdf"
        else:
            qid = f"{exam}-{year}-S1-q{q['q']}"
            ms = f"**答案:{ans}**"
            image = f"img_adm/{qid}.png"
            nyear = int(year)
            session = f"November {year}"
            series = f"{exam.lower()[0]}{str(year)[2:]}"
            paper_label = f"{exam}/S1"
            sub = "TSA_section1" if exam == "TSA" else "BMAT_section1"
            pdf = f"bank/TARA/{sub}/papers/{exam}-{year}-S1.pdf"
        qtype = "mcq" if re.fullmatch(r"[A-H]", ans) else "short"
        opts = q.get("options") or []
        if qtype == "mcq" and not opts:
            # options live in the text (line-start letters or \textbf math
            # blocks) but the splitter didn't list them; derive the range
            letters = set(re.findall(r"^(?:\*\*)?([A-H])(?:\*\*)?[\s.):]",
                                     text, re.M))
            letters |= set(re.findall(
                r"\\(?:textbf|mathbf|bf)\s*\{\s*([A-H])\s*\}", text))
            letters.add(ans)
            opts = [chr(c) for c in range(ord("A"), ord(max(letters)) + 1)]
        q = dict(q, options=opts)
        rows.append({
            "id": qid, "syllabus": exam, "component": paper,
            "component_name": COMPONENT_NAMES[(exam, paper)],
            "paper": paper_label, "variant": "", "year": nyear, "month": 11,
            "session": session, "series": series, "q": q["q"],
            "parts": "[]", "marks": 1, "marks_parts": "[]",
            "topic": q.get("topic"), "topic_name": q.get("topic_name"),
            "topic_all": json.dumps(q.get("topic_all") or []),
            "topic_confident": q.get("topic_confident", 1),
            "topic_margin": None, "topic_source": q.get("topic_source", "keyword"),
            "topic_note": None,
            "question_text": text, "question_latex": text,
            "ms_text": ms, "ms_latex": ms, "mark_codes": "[]",
            "ms_total": 1, "totals_agree": 1,
            "image": image, "qp_pdf": pdf, "ms_pdf": None,
            "qp_pages": json.dumps([p - 1 for p in q["pages"]]),
            "has_diagram": int("![](" in text),
            "q_quality": "ok", "ms_quality": "ok",
            "subtopic": q.get("subtopic"), "subtopic_name": q.get("subtopic_name"),
            "answer": ans, "qtype": qtype,
            "options": json.dumps(q.get("options") or []),
        })

    keys = list(rows[0])
    con.executemany(
        f"INSERT INTO questions ({','.join(keys)}) VALUES ({','.join(':'+k for k in keys)})",
        rows)

    # FTS: drop stale admissions rows, insert fresh
    con.execute("DELETE FROM q_fts WHERE id IN "
                "(SELECT id FROM questions WHERE syllabus IN ('TMUA','TSA','BMAT'))")
    con.execute("""INSERT INTO q_fts (id, question_text, ms_text, topic_name)
                   SELECT id, question_text, ms_text, topic_name FROM questions
                   WHERE syllabus IN ('TMUA','TSA','BMAT')""")
    con.commit()

    # the model tags went with the deleted rows; put them back
    tag_batches.write(argparse.Namespace(retag=tag_batches.RETAG_DEFAULT, dry_run=False),
                      syllabi=("TMUA", "TSA", "BMAT"))

    # ---- verification --------------------------------------------------
    errs = []
    for syl, n in con.execute("SELECT syllabus, COUNT(*) FROM questions "
                              "WHERE syllabus IN ('TMUA','TSA','BMAT') "
                              "GROUP BY syllabus"):
        print(f"  {syl}: {n} 题")
    n_noans = con.execute("SELECT COUNT(*) FROM questions WHERE syllabus IN "
                          "('TMUA','TSA','BMAT') AND (answer IS NULL OR answer='')"
                          ).fetchone()[0]
    if n_noans:
        errs.append(f"{n_noans} 题无答案")
    for (img,) in con.execute("SELECT image FROM questions WHERE image LIKE 'img_adm/%'"):
        if not os.path.exists(os.path.join(QB, img)):
            errs.append(f"缺图 {img}")
            break
    missing_fig = [f for f in copied if not os.path.exists(os.path.join(QB, f))]
    if missing_fig:
        errs.append(f"缺内嵌图 {missing_fig[:3]}")
    model = {k for k, v in json.load(open(tag_batches.RETAG_DEFAULT)).items()
             if k != "_" and k.split("-")[0] in ("TMUA", "TSA", "BMAT")}
    got = {r[0] for r in con.execute("SELECT id FROM questions WHERE syllabus IN "
                                     "('TMUA','TSA','BMAT') AND topic_source='model'")}
    if model - got:
        errs.append(f"retag_model.json 中 {len(model - got)} 题未写上模型标签")
    nf = con.execute("SELECT COUNT(*) FROM q_fts WHERE id LIKE 'TMUA%' OR id LIKE "
                     "'TSA%' OR id LIKE 'BMAT%'").fetchone()[0]
    if nf != len(rows):
        errs.append(f"FTS {nf} 行,应为 {len(rows)}")
    total = con.execute("SELECT COUNT(*) FROM questions").fetchone()[0]
    print(f"  内嵌图 {len(copied)} 张;库总量 {total} 题")
    print("⚠️  " + "; ".join(errs) if errs else "合库校验全部通过")
    con.close()


if __name__ == "__main__":
    main()
