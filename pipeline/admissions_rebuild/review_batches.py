#!/usr/bin/env python3
"""把"需要看图才能判"的题分批派给 subagent,并把回收结果校验后落盘。

    python3 review_batches.py plan  --what options [--exam TSA] [--size 12]
    python3 review_batches.py apply --what options

分工是固定的,别绕过:**subagent 只看图、只返回 JSON,不写任何文件**;
主进程负责分批、落盘、校验。理由有两个 —— 多个 agent 同时写同一个文件会
互相覆盖;更要紧的是,agent 一旦自己改了文件,你就无法再从校验数字反推
是哪一批判错了,只能全部重来。

plan 会在 <out>/ 下生成:
    batch_01.json         这批的题号与图片路径
    batch_01.prompt.txt   直接可以塞给 subagent 的任务描述
apply 读取同目录下你保存的 batch_01.result.json(agent 回的那段 JSON),
校验后写进 options_patch.json 或 retag_*.json,并明确告诉你哪几批要重看。
"""
import argparse, json, os, re, sys

MM = {"MM1": "代数与函数", "MM2": "数列", "MM3": "坐标几何", "MM4": "三角",
      "MM5": "指对数", "MM6": "微分", "MM7": "积分", "MM8": "函数图像",
      "M1": "单位", "M2": "数论", "M3": "比例", "M5": "几何",
      "M6": "统计", "M7": "概率"}
CT = ["PS", "CT-main", "CT-draw", "CT-assm", "CT-evid", "CT-flaw",
      "CT-match", "CT-prin"]


def qid(q):
    if q["exam"] == "TMUA":
        return f"TMUA-{q['year']}-P{q['paper']}-q{q['q']}"
    return f"{q['exam']}-{q['year']}-S1-q{q['q']}"


def load():
    if not os.path.exists("questions_adm.json"):
        sys.exit("在 questions_adm.json 所在目录跑这个脚本")
    return json.load(open("questions_adm.json"))


def needs_options(q):
    a = q.get("answer") or ""
    if not re.fullmatch(r"[A-H]", a):
        return False
    body = q.get("text", "")
    return not (a in (q.get("options") or [])
                or re.search(rf"^(?:\*\*)?{a}(?:\*\*)?[\s.):]", body, re.M)
                or re.search(rf"\\(?:textbf|mathbf|bf)\s*{{\s*{a}\s*}}", body))


def needs_topic(q):
    return q["exam"] == "TMUA" and not q.get("topic_confident", 1)


PROMPT_OPTIONS = """你要核对 {n} 道{exam}真题印在卷面上的选项字母表。

对每一题:
1. 用 Read 打开对应的图片(路径在下面清单里)
2. 只记录**卷面上真的印着**的选项字母,不要推断、不要替它补全
3. 不要写文件,不要改任何东西

整个回复只输出一个 JSON 数组,不要任何其他文字:
[{{"id": "TSA-2019-S1-q6", "letters": "ABCDE", "kind": "text", "note": ""}},
 {{"id": "TSA-2019-S1-q7", "letters": "ABCDE", "kind": "figure",
   "note": "五幅柱状图,字母印在每张图左上角"}}]

kind:text(文字选项)/ figure(图形选项)/ table(表格选项)
看不清、或这一页根本没有选项:letters 填 "",note 写清楚原因。

清单:
{items}"""

PROMPT_TOPIC = """你要给 {n} 道 TMUA 真题判定考点主题(机器打分置信度低,需要人眼)。

对每一题:
1. 用 Read 打开对应的图片
2. 判断这道题**实际考的是什么方法**(不是题面出现了什么词)
3. 不要写文件,不要改任何东西

整个回复只输出一个 JSON 数组:
[{{"id": "TMUA-2021-P1-q7", "topic": "MM7", "why": "考定积分的奇偶对称性"}}]

topic 只能取以下之一:
{codes}

清单:
{items}"""


def plan(args):
    qs = load()
    pick = needs_options if args.what == "options" else needs_topic
    sel = [q for q in qs if pick(q) and (not args.exam or q["exam"] == args.exam)]
    if not sel:
        print("没有需要复核的题 —— 不用开 agent")
        return 0
    os.makedirs(args.out, exist_ok=True)
    miss = [qid(q) for q in sel
            if not os.path.exists(os.path.join(args.img, qid(q) + ".png"))]
    if miss:
        print(f"⚠️  {len(miss)} 题还没有图,先跑 render_adm_imgs.py:{miss[:3]}")

    batches = [sel[i:i + args.size] for i in range(0, len(sel), args.size)]
    for bi, batch in enumerate(batches, 1):
        ids = [qid(q) for q in batch]
        items = "\n".join(f"  {i}  →  {os.path.join(args.img, i + '.png')}"
                          for i in ids)
        tmpl = PROMPT_OPTIONS if args.what == "options" else PROMPT_TOPIC
        text = tmpl.format(n=len(ids), exam=(args.exam or "入学考"),
                           items=items,
                           codes="\n".join(f"  {k}  {v}" for k, v in MM.items()))
        base = os.path.join(args.out, f"batch_{bi:02d}")
        json.dump({"what": args.what, "ids": ids}, open(base + ".json", "w"),
                  ensure_ascii=False, indent=1)
        open(base + ".prompt.txt", "w", encoding="utf-8").write(text)
    print(f"{len(sel)} 题 → {len(batches)} 批(每批 {args.size})-> {args.out}/")
    print("把每个 batch_NN.prompt.txt 派给一个 subagent,"
          "回来的 JSON 存成 batch_NN.result.json,然后跑 apply")
    return 0


def apply_(args):
    qs = {qid(q): q for q in load()}
    results, bad_batches = {}, []
    for f in sorted(os.listdir(args.out)):
        if not f.endswith(".result.json"):
            continue
        base = f[:-len(".result.json")]
        try:
            data = json.load(open(os.path.join(args.out, f)))
        except Exception as e:
            bad_batches.append((base, f"JSON 读不了:{e}"))
            continue
        want = set(json.load(open(os.path.join(args.out, base + ".json")))["ids"])
        got = {r["id"] for r in data}
        if got != want:
            bad_batches.append((base, f"题号对不上:少 {list(want-got)[:3]} "
                                      f"多 {list(got-want)[:3]}"))
            continue
        results[base] = data

    if args.what == "options":
        patch, rejects = {}, []
        for base, data in results.items():
            for r in data:
                q = qs.get(r["id"])
                letters = (r.get("letters") or "").strip().upper()
                ans = q.get("answer") or ""
                # 硬校验:官方答案字母必须落在 agent 报的字母表里
                if not letters or ans not in letters:
                    rejects.append((base, r["id"], letters, ans))
                    continue
                patch[r["id"]] = {"options": list(letters),
                                  "kind": r.get("kind", ""),
                                  "note": r.get("note", "")}
        for base, *_ in rejects:
            if base not in [b for b, _ in bad_batches]:
                bad_batches.append((base, "有题没通过答案∈选项校验"))
        json.dump(patch, open("options_patch.json", "w"),
                  ensure_ascii=False, indent=1)
        print(f"通过 {len(patch)} 题 -> options_patch.json")
        for base, i, letters, ans in rejects[:10]:
            print(f"  ✗ {i}: agent 报 {letters or '(空)'},官方答案 {ans}")
    else:
        out = "retag_tmua.json"
        cur = json.load(open(out)) if os.path.exists(out) else {"_": "模型复核改判"}
        n = 0
        for base, data in results.items():
            for r in data:
                t = (r.get("topic") or "").strip()
                if t not in MM:
                    bad_batches.append((base, f"{r['id']} 主题码非法:{t}"))
                    continue
                q = qs[r["id"]]
                cur[f"{q['year']}-{q['paper']}-{q['q']}"] = t
                n += 1
        json.dump(cur, open(out, "w"), ensure_ascii=False, indent=1)
        print(f"写入 {n} 条改判 -> {out}(tag_admissions.py 会读它)")

    if bad_batches:
        print(f"\n⚠️  {len(set(b for b,_ in bad_batches))} 批要重看:")
        for b, why in dict(bad_batches).items():
            print(f"   {b}: {why}")
        print("重看时把该批的 result.json 删掉再派一次,不要手工改数值 —— "
              "手工改等于把校验绕过去了")
    else:
        print("\n全部批次通过校验。记得抽 5% 自己再看一眼图。")
    return 1 if bad_batches else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mode", choices=["plan", "apply"])
    ap.add_argument("--what", choices=["options", "topic"], default="options")
    ap.add_argument("--exam", choices=["TMUA", "TSA", "BMAT"])
    ap.add_argument("--size", type=int, default=12)
    ap.add_argument("--out", default="/tmp/review")
    ap.add_argument("--img", default="img_adm")
    a = ap.parse_args()
    return plan(a) if a.mode == "plan" else apply_(a)


if __name__ == "__main__":
    sys.exit(main())
