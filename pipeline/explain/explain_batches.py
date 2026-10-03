#!/usr/bin/env python3
"""Worked explanations for CAIE questions, written by subagents in batches.

    python3 pipeline/explain/explain_batches.py plan  --out DIR [选题参数]
    python3 pipeline/explain/explain_batches.py apply --out DIR
    python3 pipeline/explain/explain_batches.py write --out DIR [--write]

plan 在 DIR 下生成:
    batch_NN.json         本批题号与各题小问标签
    batch_NN.prompt.txt   给 explainer 的批次文件:任务说明 + 主题表 + 题目
    plan.json             选题参数与批次清单
每个 explainer(.claude/agents/explainer.md)读一个批次文件,把结果写到
DIR/batch_NN.result.json,回复只报告写了几题。结果不经过主会话的上下文。

apply 校验每批结果:题号集合与 batch_NN.json 一致;每题的小问标签与库中
part_data 一致;每个小问有 approach、points、pitfalls、answer、terms,
terms 的 topic 属于大纲小节。不合格的批整批拒收(删除结果后重派),
合格的汇总到 DIR/accepted.json。

write 把 accepted.json 写进 questions.explanation(JSON,缺列时新建);
--override DIR 再读重做批次的 accepted.json,同一题以重做结果为准:
    {"parts": [{"label": "a(i)", "approach": "...",
                "points": [{"mark": "1", "point": "...", "why": "..."}],
                "pitfalls": ["..."], "answer": "...",
                "terms": [{"term": "pixel", "wording": "...", "topic": "1.2"}]}]}
没有小问的题只有一项,label 为 ""。terms 是评分细则中得分的关键术语及其
得分表述,供之后按大纲小节统计词频、整理成知识树。

选题参数:
    --syllabus 9618 --components 1,2,3
    --ids-file f              指定题号
    --marks-per-batch 60      每批的总分上限(按分值分批,输出量与分值成正比)
    --skip-done               跳过 explanation 已有内容的题
    --notes f.json            复核模式:{题号: 复核原因};批次文件附现有详解与评分细则
                              PDF 路径,agent 对照原件给出更正后的完整详解,结果格式不变,
                              用 write --override 覆盖
    --recheck                 与 --notes 同用:以当前(已对照原卷核对的)评分细则为准复核,不打开 PDF
9709、9231 用数学版的写作要求(解题过程写 LaTeX,points 的 mark 写评分码,terms 写公式)。
"""
import argparse, glob, json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))
from lib import db, paths  # noqa: E402
from pipeline.tags.tag_batches import needs_image  # noqa: E402

KEYS = ("approach", "points", "pitfalls", "answer", "terms")

ANSWER = {
    "cs": """4. answer:完整参考答案,即一份可以拿满分的作答,Markdown。
   代码与伪代码题给出完整代码,放在 ``` 代码块中,
   伪代码遵循 CAIE 9618 伪代码规范(DECLARE、←、ENDIF、ENDWHILE 等)。
   表格题用 Markdown 表格给出填好的表。
5. terms:这一问中需要背诵的关键术语,0 至 6 个。每个写
   term(英文术语,小写,单数)、wording(评分细则认可的定义或得分表述,英文)、
   topic(大纲小节码,只能从下表选)。纯计算、纯读代码的小问可以为空数组。""",
    "math": """4. answer:完整参考答案,即一份可以拿满分的解题过程,Markdown。公式写成 LaTeX,
   放在 $...$ 中(独立成行的式子用 $$...$$)。按评分细则的步骤写,每个得分步骤都要出现;
   最终答案的形式与精度和细则一致(如三位有效数字、精确值、角度制或弧度制)。
   证明题写出完整证明;作图题用文字说明图形的关键特征(与坐标轴的交点、渐近线、极值点等)。
5. terms:这一问用到、需要记住的公式、定理或标准结论,0 至 4 个。每个写
   term(英文名称,小写,如 "chain rule")、wording(公式或结论本身,LaTeX)、
   topic(大纲小节码,只能从下表选)。纯代数运算、没有需要记的公式时为空数组。
   points 的 mark 写评分细则的评分码(如 "M1"、"A1"、"B1"、"DM1"),
   point 写该步骤需要写出的式子或结论。""",
}

RECHECK = """以下 {n} 道 {exam} 真题已有详解,但详解写于评分细则全面改写之前。评分细则已逐题对照原卷
重写并核对过,以下每题给出的「该小问评分细则」是现在的准确版本。

对每一题:
1. 逐个小问对照现在的评分细则,核对现有详解:得分点(points)的个数、分值与表述是否与细则一致,
   参考答案(answer)是否能按细则拿满分,常见失分是否仍然成立。
2. 输出完整详解,格式与字段和现有详解相同(见下方写作要求)。与细则一致的内容原样保留,
   只改不一致的地方;不要为了改而改。
3. 需要时用 Read 打开题图核对题面。

写作要求:
{rules}

题目:

{items}"""

PROMPT = """你要为 {n} 道 {exam} 真题逐个小问写详解,供学生自学与背诵。

语言:中文;考试术语、关键词、代码与伪代码保留英文,术语与评分细则的原文措辞一致。

每个小问写五项:
1. approach:解题思路。这一问考的是哪个知识点,题面的哪些词决定了答法,
   应当按什么顺序作答。2 至 5 句。
2. points:得分点逐条说明。按评分细则逐个得分点写:
   mark 为该点的分值或给分方式(如 "1"、"1 per bullet, max 2"),
   point 为能拿到这一分的最简表述(英文,贴近细则原文),
   why 为这一点为什么给分、与题目哪个条件对应(中文)。
   细则中"任选其一"的要点合并为一条并注明可选。
3. pitfalls:常见失分,1 至 4 条。写具体的错误表述或遗漏,
   不写"注意审题"这类泛泛的话。
{answer_rule}

要求:
- 小问必须按每题给出的"小问"标签逐个写,标签原样照抄,不增不减;
  标签为 "" 表示整题只有一问。
- 以评分细则为准,不自创与细则矛盾的答案;细则明显有 OCR 错字时按题意更正。
- 每题都附有题图路径。标"必看"的题先用 Read 打开图片;其他题在题面文字缺表格、
  图、代码、数据或提到的内容找不到时,也必须先打开图片,以图片为准,不要从答案反推题面。
- 用 Write 把结果写到 {result},内容是一个 JSON 数组,不要任何其他文字:
  [{{"id": "9618_s21_11_q01", "parts": [{{"label": "a(i)", "approach": "...",
     "points": [{{"mark": "1", "point": "...", "why": "..."}}],
     "pitfalls": ["..."], "answer": "...",
     "terms": [{{"term": "pixel", "wording": "...", "topic": "1.2"}}]}}]}}]
- 写完后回复一行:"{name}: N 题已写入"。不要在回复中重复结果内容。

大纲小节码:
{table}

题目:

{items}"""


REVIEW = """以下 {n} 道 {exam} 真题已有详解,但题面或评分细则的识别文本有疑点(每题"复核原因"),
需要对照原件复核并给出更正后的完整详解。

对每一题:
1. 用 Read 打开题图;再用 Read 打开评分细则 PDF(pages 参数,每次不超过 20 页),
   找到该题所在页,以 PDF 原页为准,不以识别文本为准。
2. 核对现有详解的每个小问:得分点是否与细则原页一致,参考答案是否正确,
   题面被识别错或漏掉的内容(表格、图、上划线、连线)是否处理对。
3. 输出更正后的完整详解,格式、字段与要求和现有详解相同(见下方写作要求)。
   没有问题的小问原样保留。细则原页确实没有该小问的逐点给分时,在 approach
   末尾注明"细则未逐点给分,得分点按题意归纳"。

写作要求(与原批次相同):
{rules}

题目:

{items}"""


def syllabus_table(syl):
    spec = json.load(open(paths.SYLLABUS))[syl]["topics"]
    return {k: v["name"] for k, v in spec.items() if "." in k}


def labels(row):
    d = json.loads(row["part_data"]) if row["part_data"] else None
    return [p["label"] for p in (d or {}).get("parts") or []] or [""]


def item_text(r):
    d = json.loads(r["part_data"]) if r["part_data"] else None
    head = f"### {r['id']}  ({r['marks']} 分)"
    lines = [head, "小问: " + ", ".join(f'"{l}"' for l in labels(r))]
    img = paths.resolve(r["image"])
    if img:
        lines.append(f"[图片{'·必看' if needs_image(r) else ''}] {img}")
    if d and d.get("text_split") and d.get("parts"):
        if d.get("stem"):
            lines += ["[题干]", d["stem"]]
        for p in d["parts"]:
            lines += [f"[小问 {p['label']}]({p['marks']} 分)",
                      (p.get("intro") or "") + "\n" + p["text"],
                      "[该小问评分细则]", p.get("ms") or "(见整题细则)"]
        if any(not p.get("ms") for p in d["parts"]):
            lines += ["[整题评分细则]", r["ms"] or "(无)"]
    else:
        lines += ["[题干]", r["q"] or "(无,见图片)", "[评分细则]", r["ms"] or "(无)"]
    if r.get("note"):
        pdf = os.path.join(paths.RAW, "ms", re.sub(
            r"^(\w+?)_(\w\d\d)_(\d\d)_q\d+$", r"\1_\2_ms_\3.pdf", r["id"]))
        lines += ["[复核原因]", r["note"], f"[评分细则 PDF] {pdf}",
                  "[现有详解]", r["explanation"] or "(无)"]
    return "\n".join(lines) + "\n"


def select(con, a):
    rows = [dict(r) for r in con.execute(
        "SELECT id, syllabus, component, component_name, marks, marks_parts, part_data, "
        "has_diagram, q_quality, image, explanation, q AS qno, "
        "COALESCE(question_latex, question_text) AS q, "
        "COALESCE(ms_latex, ms_text) AS ms FROM questions WHERE syllabus=? "
        "ORDER BY component, series, paper, qno", (a.syllabus,))]
    comps = a.components.split(",")
    rows = [r for r in rows if r["component"] in comps]
    if a.ids_file:
        want = set(open(a.ids_file).read().split())
        rows = [r for r in rows if r["id"] in want]
    if a.skip_done:
        rows = [r for r in rows if not r["explanation"]]
    if a.notes:
        notes = json.load(open(a.notes))
        rows = [dict(r, note=notes[r["id"]]) for r in rows if r["id"] in notes]
    return rows


def ensure_column(con):
    cols = {r[1] for r in con.execute("PRAGMA table_info(questions)")}
    if "explanation" not in cols:
        con.execute("ALTER TABLE questions ADD COLUMN explanation TEXT")
        con.commit()


def plan(a):
    con = db.connect()
    ensure_column(con)
    rows = select(con, a)
    if not rows:
        sys.exit("没有选中任何题")
    os.makedirs(a.out, exist_ok=True)
    if glob.glob(os.path.join(a.out, "batch_*")):
        sys.exit(f"{a.out} 已有批次文件,换一个目录或先清空")
    batches, cur, total = [], [], 0
    for r in rows:
        m = r["marks"] or 5
        if cur and (total + m > a.marks_per_batch or r["component"] != cur[0]["component"]):
            batches.append(cur)
            cur, total = [], 0
        cur.append(r)
        total += m
    if cur:
        batches.append(cur)
    table = "\n".join(f"{k} {v}" for k, v in syllabus_table(a.syllabus).items())
    names = []
    for i, b in enumerate(batches, 1):
        name = f"batch_{i:03d}"
        names.append(name)
        json.dump({r["id"]: labels(r) for r in b},
                  open(os.path.join(a.out, name + ".json"), "w"), ensure_ascii=False)
        exam = f"{a.syllabus} Paper {b[0]['component']} ({b[0]['component_name']})"
        body = PROMPT.format(
            n=len(b), exam=exam, name=name, table=table,
            answer_rule=ANSWER["cs" if a.syllabus == "9618" else "math"],
            result=os.path.abspath(os.path.join(a.out, name + ".result.json")),
            items="\n".join(item_text(r) for r in b))
        if a.notes:                            # review: the same rules, the review task first
            rules, items = body.split("\n\n题目:\n\n", 1)
            body = (RECHECK if a.recheck else REVIEW).format(n=len(b), exam=exam, rules=rules, items=items)
        open(os.path.join(a.out, name + ".prompt.txt"), "w").write(body)
    json.dump({"args": vars(a), "batches": names},
              open(os.path.join(a.out, "plan.json"), "w"), ensure_ascii=False, indent=1)
    print(f"{len(rows)} 题,{sum(r['marks'] or 0 for r in rows)} 分,{len(batches)} 批 -> {a.out}")


def check(spec, data, codes):
    """Problems with one batch's result, [] when it is acceptable."""
    if not isinstance(data, list):
        return ["结果不是数组"]
    got = {q.get("id"): q for q in data if isinstance(q, dict)}
    errs = []
    if set(got) != set(spec):
        errs.append(f"题号不符:缺 {sorted(set(spec) - set(got))[:3]},"
                    f"多 {sorted(set(got) - set(spec))[:3]}")
    for qid, want in spec.items():
        q = got.get(qid)
        if not q:
            continue
        parts = q.get("parts") or []
        if [p.get("label") for p in parts] != want:
            errs.append(f"{qid} 小问标签 {[p.get('label') for p in parts]} ≠ {want}")
            continue
        for p in parts:
            miss = [k for k in KEYS if k not in p]
            if miss or not p.get("answer") or not p.get("points"):
                errs.append(f"{qid}({p['label']}) 缺 {miss or 'answer/points'}")
            bad = [t.get("topic") for t in p.get("terms") or []
                   if not isinstance(t, dict) or t.get("topic") not in codes]
            if bad:
                errs.append(f"{qid}({p['label']}) 术语小节码不在大纲中:{bad[:3]}")
    return errs


def apply_(a):
    pl = json.load(open(os.path.join(a.out, "plan.json")))
    codes = set(syllabus_table(pl["args"]["syllabus"]))
    accepted, missing, rejected = {}, [], {}
    for name in pl["batches"]:
        res = os.path.join(a.out, name + ".result.json")
        if not os.path.exists(res):
            missing.append(name)
            continue
        spec = json.load(open(os.path.join(a.out, name + ".json")))
        try:
            data = json.load(open(res))
        except ValueError as e:
            rejected[name] = [f"JSON 无法解析:{e}"]
            continue
        errs = check(spec, data, codes)
        if errs:
            rejected[name] = errs
        else:
            accepted.update({q["id"]: {"parts": q["parts"]} for q in data})
    json.dump(accepted, open(os.path.join(a.out, "accepted.json"), "w"),
              ensure_ascii=False)
    print(f"合格 {len(pl['batches']) - len(missing) - len(rejected)} 批,{len(accepted)} 题;"
          f"未完成 {len(missing)} 批;拒收 {len(rejected)} 批")
    if missing:
        print("未完成:", " ".join(missing))
    for name, errs in rejected.items():
        print(f"拒收 {name}:", ";".join(errs[:4]))


def write(a):
    accepted = json.load(open(os.path.join(a.out, "accepted.json")))
    for d in a.override or []:                 # later runs replace earlier answers
        accepted.update(json.load(open(os.path.join(d, "accepted.json"))))
    con = db.connect()
    ensure_column(con)
    print(f"{len(accepted)} 题待写入 explanation")
    if not a.write:
        print("(dry run;加 --write 写入)")
        return
    con.executemany("UPDATE questions SET explanation=? WHERE id=?",
                    [(json.dumps(v, ensure_ascii=False), k) for k, v in accepted.items()])
    con.commit()
    print("已写入")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mode", choices=["plan", "apply", "write"])
    ap.add_argument("--out", required=True)
    ap.add_argument("--syllabus", default="9618")
    ap.add_argument("--components", default="1,2,3")
    ap.add_argument("--ids-file")
    ap.add_argument("--marks-per-batch", type=int, default=60)
    ap.add_argument("--skip-done", action="store_true")
    ap.add_argument("--notes", help="复核:JSON {题号: 复核原因},只取这些题,附现有详解与细则 PDF")
    ap.add_argument("--recheck", action="store_true",
                    help="与 --notes 同用:对照当前(已核对的)评分细则复核现有详解,不打开 PDF")
    ap.add_argument("--override", action="append",
                    help="write:再读这些目录的 accepted.json,同一题以后者为准")
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    {"plan": plan, "apply": apply_, "write": write}[a.mode](a)


if __name__ == "__main__":
    main()
