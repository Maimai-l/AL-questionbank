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

write 把 accepted.json 写进 questions.explanation(JSON,缺列时新建):
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
"""
import argparse, glob, json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))
from lib import db, paths  # noqa: E402
from pipeline.tags.tag_batches import needs_image  # noqa: E402

KEYS = ("approach", "points", "pitfalls", "answer", "terms")

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
4. answer:完整参考答案,即一份可以拿满分的作答,Markdown。
   代码与伪代码题给出完整代码,放在 ``` 代码块中,
   伪代码遵循 CAIE 9618 伪代码规范(DECLARE、←、ENDIF、ENDWHILE 等)。
   表格题用 Markdown 表格给出填好的表。
5. terms:这一问中需要背诵的关键术语,0 至 6 个。每个写
   term(英文术语,小写,单数)、wording(评分细则认可的定义或得分表述,英文)、
   topic(大纲小节码,只能从下表选)。纯计算、纯读代码的小问可以为空数组。

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
        open(os.path.join(a.out, name + ".prompt.txt"), "w").write(PROMPT.format(
            n=len(b), exam=exam, name=name, table=table,
            result=os.path.abspath(os.path.join(a.out, name + ".result.json")),
            items="\n".join(item_text(r) for r in b)))
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
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    {"plan": plan, "apply": apply_, "write": write}[a.mode](a)


if __name__ == "__main__":
    main()
