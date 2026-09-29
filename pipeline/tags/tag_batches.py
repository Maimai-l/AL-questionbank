#!/usr/bin/env python3
"""Tag questions by sub-part with the `tagger` subagent, in batches.

    python3 pipeline/tags/tag_batches.py plan  --out DIR [选题参数]
    python3 pipeline/tags/tag_batches.py apply --out DIR

Roles are fixed: the subagent (.claude/agents/tagger.md, Read only) reads a
batch file and returns JSON; it never writes. The main process saves each
reply, and `apply` validates it and writes `pipeline/tags/retag_model.json`.
The database is not touched here.

plan 在 DIR 下生成:
    batch_NN.json          本批题号、卷别与主题码集合
    batch_NN.prompt.txt    给 tagger 的批次文件:任务说明 + 主题表 + 题目
    agent_NN.task.txt      一个 tagger 依次处理的若干批(--per-agent)
    plan.json              选题参数与批次清单

回收:把 tagger 的回复原样存成 DIR/agent_NN.result.json(对象,键为批次名)
或 DIR/batch_NN.result.json(数组),然后运行 apply。

选题参数(可组合):
    --syllabus 9709 --component 1   只取某科、某卷
    --ids a,b,c / --ids-file f      指定题号
    --sample N --seed S             每个 component 随机抽 N 题
    --size 12                       每批题数
    --per-agent 8                   每个 tagger 依次处理的批数

输出格式(每题):
    {"id": "...", "parts": [{"part": "a", "marks": 2, "topic": "1.1"},
                            {"part": "b", "marks": 3, "topic": "1.7"}],
     "topic": "1.7", "why": "..."}
主标签由 apply 重新计算:各主题的小问分值相加,取最多者;相同时取单个小问
分值最高者,仍相同取先出现者。模型给的 topic 与计算结果不同时,以计算结果为准并报告。

apply 的校验:
    - 每批返回的 id 集合与 batch_NN.json 完全一致
    - 每个小问的主题码属于该卷考纲(COMPONENT_TOPICS)
    - TSA 每卷 25 PS + 25 CT,BMAT 2020 年起每卷 16 PS + 16 CT
      (只对 retag_model.json 中整卷都有结果的卷检查)
    - 小问分值之和与数据库 marks 不同时只报告,不拒收(库中分值本身可能有误)
不合格的批整批拒收,须删除其结果后重派,不得手工修改结果。
"""
import argparse, datetime, glob, json, os, random, re, sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))          # 项目根目录
from lib import db, paths
from pipeline.tags import tag_any

RETAG_DEFAULT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     "retag_model.json")
Q_CHARS, MS_CHARS = 1500, 800
OUTCOME_CHARS = 400

# ------------------------------------------------------------ topic tables

TMUA = {"MM1": "Algebra and functions", "MM2": "Sequences and series",
        "MM3": "Coordinate geometry", "MM4": "Trigonometry",
        "MM5": "Exponentials and logarithms", "MM6": "Differentiation",
        "MM7": "Integration", "MM8": "Graphs of functions",
        "M1": "Units", "M2": "Number", "M3": "Ratio and proportion",
        "M5": "Geometry", "M6": "Statistics", "M7": "Probability"}
# TARA Question Guide 的分类,与 tag_admissions.py 的 CT_TYPES 一致
TARA = {"PS": "Problem Solving:数值、空间或数据推理,找出解题步骤并算出结果",
        "CT-main": "Critical Thinking: Identifying the Main Conclusion",
        "CT-draw": "Critical Thinking: Drawing a Conclusion",
        "CT-assm": "Critical Thinking: Identifying an Assumption",
        "CT-evid": "Critical Thinking: Assessing the Impact of Additional Evidence",
        "CT-flaw": "Critical Thinking: Detecting Reasoning Errors",
        "CT-match": "Critical Thinking: Matching Arguments",
        "CT-prin": "Critical Thinking: Applying Principles"}
# 每卷 (PS, CT) 题数;BMAT 2020 年之前含 Data Analysis,不作断言
PS_CT = {"TSA": lambda year: (25, 25),
         "BMAT": lambda year: (16, 16) if year >= 2020 else None}


def topic_table(syl, comp):
    """{code: 说明} — the codes this component may be tagged with."""
    if syl == "TMUA":
        return dict(TMUA)
    if syl in PS_CT:
        return dict(TARA)
    TOPICS, COMP = tag_any.load(syl)
    spec = json.load(open(paths.SYLLABUS))[syl]["topics"]
    out = {}
    # 9709 P2 and P6 have no keyword table (tag.py): take the component's
    # topics from the syllabus itself
    codes = COMP.get(str(comp)) or sorted(
        (k for k in spec if k.split(".")[0] == str(comp)),
        key=lambda k: [int(x) for x in k.split(".")])
    for code in codes:
        name = TOPICS[code][0] if code in TOPICS else spec[code]["name"]
        if syl == "9618":       # 9618 按大节标注,列出其下各小节
            subs = [f"{k} {v['name']}" for k, v in spec.items()
                    if k.split(".")[0] == code]
            out[code] = f"{name}(含 {'; '.join(subs)})"
        else:
            oc = "; ".join(spec.get(code, {}).get("outcomes", []))
            if len(oc) > OUTCOME_CHARS:
                oc = oc[:OUTCOME_CHARS].rsplit(";", 1)[0] + "; …"
            out[code] = f"{name} — {oc}" if oc else name
    return out


def paper_key(r):
    """One sitting of one paper: the unit the PS/CT counts apply to."""
    return (r["syllabus"], r["paper"], r["series"])

# -------------------------------------------------------------------- plan

PROMPT = """你要给 {n} 道 {exam} 真题逐个小问判定大纲主题码。

对每一题:
1. 按题面的小问拆分:(a)、(b)(i) 这类小问各算一项,part 写 "a"、"b(i)";
   没有小问的题只写一项,part 写 ""。marks 取题面方括号中的分值,看不到写 null,
   不要估计。
2. 每个小问判断实际考查的方法属于哪个主题,不按题面出现的词判断。
   只用来求一个中间量的工具(例如配方只为判断导数符号)不单列。
3. topic 填整题的主标签:各主题的小问分值相加后最多的那个。
4. 列有"图片"的题,用 Read 打开图片再判断;题面文字可能不完整,以图片为准。
   库中各小问分值只作参考,可能有误;与图片不符时以图片为准。
5. 不要写文件,不要改任何东西。

整个回复只输出一个 JSON 数组,不要任何其他文字(示例只说明格式):
[{{"id": "9709_w21_13_q03", "parts": [{{"part": "a", "marks": 2, "topic": "1.1"}},
  {{"part": "b", "marks": 3, "topic": "1.7"}}], "topic": "1.7",
  "why": "(a) 配方;(b) 求导判断单调性"}}]

主题码只能取以下之一:
{table}

题目:

{items}"""

AGENT_TASK = """依次处理以下 {n} 个批次文件,每个都用 Read 打开并按其中的要求执行:
{files}

整个回复只输出一个 JSON 对象,键为批次名,值为该批次文件要求的 JSON 数组:
{{{keys}}}"""


def exam_label(r):
    if r["syllabus"] in ("TSA", "BMAT", "TMUA"):
        return f"{r['syllabus']} {r['component_name']}"
    return f"{r['syllabus']} Paper {r['component']} ({r['component_name']})"


def tariffs(r):
    try:
        t = json.loads(r["marks_parts"] or "[]")
    except ValueError:
        return []
    return [m for m in t if isinstance(m, int)]


def looks_incomplete(r):
    """Fewer part labels in the text than tariffs in the database.

    Some stems still stop at the page break (the text has not been rebuilt
    from the new split yet), e.g. 9231_w21_12_q07: 17 marks, only (a)-(c)."""
    t = tariffs(r)
    if len(t) < 2:
        return False
    labels = set(re.findall(r"\(([a-h])\)", r["q"] or "")) | set(
        re.findall(r"\((i{1,3}|iv|v|vi{0,3})\)", r["q"] or ""))
    return len(labels) < len(t)


def needs_image(r):
    return (bool(r["has_diagram"]) or (r["q_quality"] or "ok") != "ok"
            or looks_incomplete(r))


def clip(text, n):
    """Head and tail of a long stem, plus the part lines from the middle.

    Cutting only the tail loses exactly what matters: a shared passage puts
    the actual question last (BMAT-2015-S1-q8), and a 9618 Paper 4 question
    puts most of its parts and marks past the first 1500 characters."""
    if len(text) <= n:
        return text
    head, tail = text[:n * 3 // 5], text[-(n * 2 // 5):]
    middle = text[len(head):len(text) - len(tail)]
    parts = [l.strip()[:100] for l in middle.split("\n")
             if re.match(r"\s*\(?(?:[a-h]|i{1,3}|iv|v|vi{0,3})\)", l)
             or re.search(r"\[\d+\]\s*$", l)][:20]
    note = f"\n…(中间略去 {len(middle)} 字"
    note += ",其中的小问行如下)\n" + "\n".join(parts) + "\n…\n" if parts else ")…\n"
    return head + note + tail


def item_text(r):
    q = clip(r["q"] or "", Q_CHARS)
    ms = (r["ms"] or "(无)")[:MS_CHARS]
    t = tariffs(r)
    head = f"### {r['id']}"
    if r["marks"]:
        head += (f"  ({r['marks']} 分;库中各小问分值依次为 {'+'.join(map(str, t))})"
                 if len(t) > 1 else f"  ({r['marks']} 分)")
    lines = [head]
    if needs_image(r):
        img = paths.resolve(r["image"])
        if img:
            lines.append(f"[图片] {img}")
    lines += ["[题干]", q, "[评分细则]" if r["syllabus"][0].isdigit()
              else "[答案与解析]", ms, ""]
    return "\n".join(lines)


def select(con, a):
    rows = con.execute(
        "SELECT id, syllabus, component, component_name, paper, series, year, "
        "q AS qno, marks, marks_parts, has_diagram, q_quality, image, topic, topic_source, "
        "COALESCE(question_latex, question_text) AS q, "
        "COALESCE(ms_latex, ms_text) AS ms FROM questions "
        "ORDER BY syllabus, component, series, paper, qno").fetchall()
    rows = [dict(r) for r in rows]
    if a.syllabus:
        rows = [r for r in rows if r["syllabus"] == a.syllabus]
    if a.component:
        rows = [r for r in rows if r["component"] == a.component]
    if a.groups:
        want = {tuple(g.split(":")) for g in a.groups.split(",")}
        rows = [r for r in rows if (r["syllabus"], r["component"]) in want]
    if a.skip_done and os.path.exists(a.retag):
        done = set(json.load(open(a.retag))) - {"_"}
        rows = [r for r in rows if r["id"] not in done]
    ids = None
    if a.ids:
        ids = a.ids.split(",")
    if a.ids_file:
        ids = open(a.ids_file).read().split()
    if ids is not None:
        want = set(ids)
        missing = want - {r["id"] for r in rows}
        if missing:
            sys.exit(f"库中没有这些题号:{sorted(missing)[:5]}")
        rows = [r for r in rows if r["id"] in want]
    if a.sample:
        by = defaultdict(list)
        for r in rows:
            by[(r["syllabus"], r["component"])].append(r)
        rng = random.Random(a.seed)
        rows = []
        for k in sorted(by):
            g = by[k]
            rows += sorted(rng.sample(g, min(a.sample, len(g))),
                           key=lambda r: (r["series"], r["paper"], r["qno"]))
    return rows


def plan(a):
    con = db.connect()
    rows = select(con, a)
    if not rows:
        sys.exit("没有选中任何题")
    if os.path.isdir(a.out) and glob.glob(os.path.join(a.out, "batch_*")):
        sys.exit(f"{a.out} 已有批次文件,换一个目录或先清空")
    os.makedirs(a.out, exist_ok=True)

    # a batch never mixes components: one topic table per batch
    groups = defaultdict(list)
    for r in rows:
        groups[(r["syllabus"], r["component"])].append(r)
    batches = []
    for k in sorted(groups):
        g = groups[k]
        for i in range(0, len(g), a.size):
            batches.append((k, g[i:i + a.size]))

    listing = []
    for bi, ((syl, comp), batch) in enumerate(batches, 1):
        name = f"batch_{bi:02d}"
        table = topic_table(syl, comp)
        text = PROMPT.format(
            n=len(batch), exam=exam_label(batch[0]),
            table="\n".join(f"  {c}  {d}" for c, d in table.items()),
            items="\n".join(item_text(r) for r in batch))
        base = os.path.join(a.out, name)
        json.dump({"syllabus": syl, "component": comp,
                   "ids": [r["id"] for r in batch], "codes": list(table)},
                  open(base + ".json", "w"), ensure_ascii=False, indent=1)
        open(base + ".prompt.txt", "w", encoding="utf-8").write(text)
        listing.append({"batch": name, "syllabus": syl, "component": comp,
                        "n": len(batch),
                        "images": sum(needs_image(r) for r in batch),
                        "chars": len(text)})

    names = [b["batch"] for b in listing]
    agents = [names[i:i + a.per_agent] for i in range(0, len(names), a.per_agent)]
    for ai, group in enumerate(agents, 1):
        files = "\n".join(f"{j}. {os.path.abspath(os.path.join(a.out, b))}"
                          ".prompt.txt" for j, b in enumerate(group, 1))
        keys = ", ".join(f'"{b}": [...]' for b in group)
        open(os.path.join(a.out, f"agent_{ai:02d}.task.txt"), "w",
             encoding="utf-8").write(AGENT_TASK.format(
                 n=len(group), files=files, keys=keys))
    json.dump({"args": {k: v for k, v in vars(a).items() if k != "func"},
               "batches": listing,
               "agents": {f"agent_{i:02d}": g for i, g in enumerate(agents, 1)}},
              open(os.path.join(a.out, "plan.json"), "w"),
              ensure_ascii=False, indent=1)

    imgs = sum(b["images"] for b in listing)
    print(f"{len(rows)} 题 → {len(batches)} 批(每批 ≤{a.size})→ "
          f"{len(agents)} 个 tagger(每个 ≤{a.per_agent} 批)-> {a.out}/")
    print(f"其中 {imgs} 题附图")
    for b in listing:
        print(f"  {b['batch']}  {b['syllabus']} P{b['component']:<2} "
              f"{b['n']:>3} 题  图 {b['images']:>2}  {b['chars']:>6} 字")
    print("把 agent_NN.task.txt 的内容交给 tagger,回复原样存成 "
          "agent_NN.result.json,然后运行 apply")
    return 0

# ------------------------------------------------------------------- apply

def parse_reply(path):
    """{batch_name: [...]} from a saved reply; tolerates a ```json fence."""
    raw = open(path, encoding="utf-8").read().strip()
    raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw)
    data = json.loads(raw)
    base = os.path.basename(path)[:-len(".result.json")]
    if isinstance(data, list):
        return {base: data}
    return data


def primary(parts):
    """Topic with the most marks summed over its parts; see module doc."""
    total, best, first = Counter(), Counter(), {}
    for i, p in enumerate(parts):
        m = p.get("marks") if isinstance(p.get("marks"), int) else 0
        t = p["topic"]
        total[t] += m
        best[t] = max(best[t], m)
        first.setdefault(t, i)
    return min(total, key=lambda t: (-total[t], -best[t], first[t]))


def check_batch(name, spec, data, rows):
    """(clean records, problems). Any problem rejects the whole batch."""
    probs, recs, warn = [], {}, []
    if not isinstance(data, list):
        return {}, ["回复不是数组"], []
    got = [d.get("id") for d in data if isinstance(d, dict)]
    want = spec["ids"]
    if len(got) != len(data) or sorted(got) != sorted(want):
        return {}, [f"题号对不上:少 {sorted(set(want) - set(got))[:3]} "
                    f"多 {sorted(set(got) - set(want))[:3]}"
                    + (" 有重复" if len(set(got)) != len(got) else "")], []
    codes = set(spec["codes"])
    for d in data:
        parts = d.get("parts")
        if not isinstance(parts, list) or not parts:
            probs.append(f"{d['id']} 没有 parts")
            continue
        # 9618 is tagged by section, but its table lists the sub-sections and
        # the model sometimes answers "13.3": keep that as the part's `sub`
        for p in parts:
            t = p.get("topic") if isinstance(p, dict) else None
            if (spec["syllabus"] == "9618" and isinstance(t, str)
                    and t not in codes and t.split(".")[0] in codes):
                p["sub"], p["topic"] = t, t.split(".")[0]
        bad = [p.get("topic") for p in parts
               if not isinstance(p, dict) or p.get("topic") not in codes]
        if bad:
            probs.append(f"{d['id']} 主题码不属于该卷考纲:{bad}")
            continue
        parts = [dict({"part": str(p.get("part") or ""),
                       "marks": p.get("marks") if isinstance(p.get("marks"), int) else None,
                       "topic": p["topic"]}, **({"sub": p["sub"]} if p.get("sub") else {}))
                 for p in parts]
        top = primary(parts)
        if d.get("topic") != top:
            warn.append(f"{d['id']} 模型主标签 {d.get('topic')},按分值应为 {top}")
        r = rows[d["id"]]
        s = sum(p["marks"] or 0 for p in parts)
        if r["marks"] and all(p["marks"] is not None for p in parts) and s != r["marks"]:
            warn.append(f"{d['id']} 小问分值和 {s} ≠ 库中 {r['marks']}")
        recs[d["id"]] = {"topic": top, "parts": parts,
                         "note": str(d.get("why") or "")[:200], "batch": name}
    return (recs if not probs else {}), probs, warn


def check_ps_ct(merged, rows):
    """Papers whose every question has a result: (report lines, bad ids)."""
    out, bad, partial = [], set(), 0
    papers = defaultdict(list)
    for r in rows.values():
        if r["syllabus"] in PS_CT:
            papers[paper_key(r)].append(r)
    for key in sorted(papers):
        qs = papers[key]
        want = PS_CT[key[0]](qs[0]["year"])
        done = [r for r in qs if r["id"] in merged]
        if not done:
            continue
        if len(done) < len(qs):
            partial += 1
            continue
        ps = sum(merged[r["id"]]["topic"] == "PS" for r in qs)
        ct = len(qs) - ps
        ok = want is None or (ps, ct) == want
        out.append(f"  {key[0]} {qs[0]['year']}: PS {ps} CT {ct}"
                   + ("" if ok else f"  ✗ 应为 PS {want[0]} CT {want[1]}"))
        if not ok:
            bad |= {r["id"] for r in qs}
    if partial:
        out.append(f"  另有 {partial} 卷只有部分题有结果,不检查配比")
    return out, bad


def rebucket(got, owner, replies, warnings, fname):
    """File each record under the batch its id belongs to.

    A tagger working through several batches sometimes files a question under
    the neighbouring batch, or answers it twice. The batch label is only
    bookkeeping; what is checked is that every id comes back exactly once.
    Two answers for one id are kept only if their parts agree."""
    seen = {}
    for name, data in got.items():
        if not isinstance(data, list):
            replies[name] = data        # check_batch reports it
            continue
        for d in data:
            i = d.get("id") if isinstance(d, dict) else None
            home = owner.get(i, name)
            if home != name:
                warnings.append(f"{fname}: {i} 放在 {name},已归入 {home}")
            if i in seen:
                prev = seen[i]
                if prev.get("parts") != d.get("parts"):
                    replies.setdefault(home, []).append(d)   # duplicate id -> rejected
                    continue
                if len(str(d.get("why") or "")) > len(str(prev.get("why") or "")):
                    prev["why"] = d.get("why")
                warnings.append(f"{fname}: {i} 回答了两次,内容一致,只保留一份")
                continue
            seen[i] = d
            replies.setdefault(home, []).append(d)


def apply_(a):
    con = db.connect()
    rows = {r["id"]: dict(r) for r in con.execute(
        "SELECT id, syllabus, component, paper, series, year, marks, topic, "
        "topic_source FROM questions")}
    specs = {os.path.basename(f)[:-5]: json.load(open(f))
             for f in sorted(glob.glob(os.path.join(a.out, "batch_*.json")))
             if not f.endswith(".result.json")}
    if not specs:
        sys.exit(f"{a.out} 下没有批次文件")

    replies, rejected, warnings = {}, {}, []
    owner = {i: n for n, sp in specs.items() for i in sp["ids"]}
    for f in sorted(glob.glob(os.path.join(a.out, "*.result.json"))):
        try:
            got = parse_reply(f)
        except Exception as e:
            rejected[os.path.basename(f)] = [f"JSON 读不了:{e}"]
            continue
        rebucket(got, owner, replies, warnings, os.path.basename(f))
    accepted = {}
    for name, spec in specs.items():
        if name not in replies:
            continue
        recs, probs, warn = check_batch(name, spec, replies[name], rows)
        warnings += warn
        if probs:
            rejected[name] = probs
        else:
            accepted.update(recs)
    for name in replies:
        if name not in specs:
            rejected[name] = ["不在本目录的批次清单中"]

    RETAG = a.retag
    cur = json.load(open(RETAG)) if os.path.exists(RETAG) else {}
    meta = cur.pop("_", None)
    today = datetime.date.today().isoformat()
    merged = dict(cur)
    for i, rec in accepted.items():
        merged[i] = dict(rec, at=today, run=os.path.basename(os.path.abspath(a.out)))

    ps_lines, ps_bad = check_ps_ct(merged, rows)
    if ps_bad:
        for i in ps_bad & set(accepted):
            why = rejected.setdefault(accepted[i]["batch"], [])
            if "所在卷 PS/CT 配比不符" not in why:
                why.append("所在卷 PS/CT 配比不符")
        for i in ps_bad:
            if i in accepted:
                merged.pop(i)
                if i in cur:
                    merged[i] = cur[i]
        accepted = {i: r for i, r in accepted.items() if i not in ps_bad}

    new = {i: merged[i] for i in sorted(merged)}
    out = {"_": meta or "tagger 子 agent 按小问判定的主题;tag_batches.py apply 写入"}
    out.update(new)
    # one question per line, so a rerun shows up as a readable diff
    with open(RETAG, "w", encoding="utf-8") as f:
        f.write("{\n" + ",\n".join(
            f"{json.dumps(k)}: {json.dumps(v, ensure_ascii=False)}"
            for k, v in out.items()) + "\n}\n")

    print(f"批次 {len(specs)},收到回复 {len(replies)},通过 {len(accepted)} 题"
          f" -> {os.path.relpath(RETAG, paths.ROOT)}(共 {len(new)} 题)")
    if ps_lines:
        print("PS/CT 配比:")
        print("\n".join(ps_lines))
    report(accepted, rows, a.out)
    if warnings:
        print(f"\n提示 {len(warnings)} 条(不拒收):")
        for w in warnings[:20]:
            print("  " + w)
    missing = [n for n in specs if n not in replies]
    if missing:
        print(f"\n尚未收到回复:{', '.join(missing)}")
    if rejected:
        print(f"\n{len(rejected)} 批拒收,删除其结果后重派,不要手工修改:")
        for n, why in rejected.items():
            print(f"  {n}: {'; '.join(why[:3])}")
        return 1
    return 0


def report(accepted, rows, out_dir):
    """Disagreement with the tags now in the database, per component."""
    if not accepted:
        return
    by = defaultdict(list)
    for i, rec in accepted.items():
        r = rows[i]
        by[(r["syllabus"], r["component"])].append((r, rec))
    diff = []
    print("\n与库中现有标签比较(主标签不同 / 现有标签不在任何小问中):")
    for k in sorted(by):
        g = by[k]
        d1 = [(r, rec) for r, rec in g if rec["topic"] != r["topic"]]
        d2 = [(r, rec) for r, rec in d1
              if r["topic"] not in {p["topic"] for p in rec["parts"]}]
        src = Counter(r["topic_source"] for r, _ in g)
        print(f"  {k[0]:<5}P{k[1]}  {len(g):>3} 题  主标签不同 {len(d1):>2}  "
              f"完全不含 {len(d2):>2}   现有来源 {dict(src)}")
        diff += [{"id": r["id"], "db": r["topic"], "db_source": r["topic_source"],
                  "model": rec["topic"], "parts": rec["parts"], "note": rec["note"]}
                 for r, rec in d1]
    path = os.path.join(out_dir, "disagree.json")
    json.dump(diff, open(path, "w"), ensure_ascii=False, indent=1)
    print(f"不一致明细 -> {path}")


# ------------------------------------------------------------------- write

def names_for(con):
    """{(syllabus, code): topic_name} as the bank already spells them.

    9618 names its sections, TSA/BMAT prefix the CT type; reusing the names
    already in the table keeps the page's topic filter from splitting."""
    out = {}
    for syl, code, name in con.execute(
            "SELECT syllabus, topic, topic_name FROM questions "
            "WHERE topic IS NOT NULL GROUP BY 1, 2"):
        out[(syl, code)] = name
    for syl in ("9709", "9231", "9618"):
        TOPICS, _ = tag_any.load(syl)
        for code, v in TOPICS.items():
            out.setdefault((syl, code), v[0])
    for code, name in TMUA.items():
        out.setdefault(("TMUA", code), name)
    for syl in PS_CT:
        for code, name in TARA.items():
            out.setdefault((syl, code), "Problem Solving" if code == "PS" else name)
    return out


def write(a, syllabi=None):
    """retag_model.json -> questions. Rerun after combine.py, which rebuilds
    the rows; merge_admissions.py calls this itself with syllabi set to the
    exams it has just re-inserted."""
    res = {k: v for k, v in json.load(open(a.retag)).items() if k != "_"}
    con = db.connect()
    db.add_column(con, "questions", "topic_parts")
    names = names_for(con)
    rows = {r["id"]: dict(r) for r in con.execute(
        "SELECT id, syllabus, topic, topic_all, subtopic, subtopic_name "
        "FROM questions")}
    missing = [i for i in res if i not in rows]
    if missing:
        sys.exit(f"retag_model.json 中有库里没有的题号:{missing[:5]}")
    if syllabi:
        res = {i: v for i, v in res.items() if rows[i]["syllabus"] in syllabi}

    upd, moved = [], Counter()
    for i, rec in res.items():
        r = rows[i]
        top = rec["topic"]
        # shortlist: the parts' topics by marks, then the old shortlist
        by = Counter()
        for p in rec["parts"]:
            by[p["topic"]] += p["marks"] or 0
        seen = [top] + sorted((t for t in by if t != top), key=lambda t: -by[t])
        try:
            old = json.loads(r["topic_all"] or "[]")
        except ValueError:
            old = []
        for t in old:
            if t not in seen:
                seen.append(t)
        sub, sub_name = r["subtopic"], r["subtopic_name"]
        if sub and not (sub == top or sub.startswith(top + ".")):
            sub = sub_name = None   # a sub-topic of the old topic no longer applies
        if top != r["topic"]:
            moved[f"{r['syllabus']}: {r['topic']} -> {top}"] += 1
        upd.append((top, names.get((r["syllabus"], top), top),
                    json.dumps(seen[:3]), rec.get("note") or None,
                    json.dumps(rec["parts"], ensure_ascii=False),
                    sub, sub_name, i))

    print(f"写入 {len(upd)} 题,主标签改变 {sum(moved.values())} 题")
    for k, v in moved.most_common(15):
        print(f"  {v:>4}  {k}")
    if a.dry_run:
        print("(--dry-run,未写入)")
        return 0
    con.executemany(
        "UPDATE questions SET topic=?, topic_name=?, topic_all=?, topic_note=?, "
        "topic_parts=?, topic_source='model', topic_confident=1, "
        "topic_margin=NULL, subtopic=?, subtopic_name=? WHERE id=?", upd)
    con.execute("DELETE FROM q_fts")
    con.execute("INSERT INTO q_fts(id,question_text,ms_text,topic_name) SELECT id, "
                "COALESCE(question_latex,question_text), COALESCE(ms_latex,ms_text), "
                "topic_name FROM questions")
    con.commit()
    for r in con.execute("SELECT topic_source, COUNT(*) FROM questions GROUP BY 1"):
        print(f"  {r[0]:<20}{r[1]}")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mode", choices=["plan", "apply", "write"])
    ap.add_argument("--out", default=os.path.join(paths.RAW, "tag_batches"))
    ap.add_argument("--retag", default=RETAG_DEFAULT,
                    help="apply 写入的文件(默认 pipeline/tags/retag_model.json)")
    ap.add_argument("--syllabus")
    ap.add_argument("--component")
    ap.add_argument("--groups", help="如 9231:2,9709:5,TMUA:1")
    ap.add_argument("--skip-done", action="store_true",
                    help="跳过 retag_model.json 中已有结果的题")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--ids")
    ap.add_argument("--ids-file")
    ap.add_argument("--sample", type=int)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--size", type=int, default=12)
    ap.add_argument("--per-agent", type=int, default=8)
    a = ap.parse_args()
    return {"plan": plan, "apply": apply_, "write": write}[a.mode](a)


if __name__ == "__main__":
    sys.exit(main())
