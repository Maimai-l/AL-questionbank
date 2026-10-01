#!/usr/bin/env python3
"""A static copy of the practice workbench, for previewing the interface without
running the server.

    python3 app/preview.py OUT_DIR

OUT_DIR gets the page (index.html, written to be published as an Artifact: no
<html>/<head>/<body> of its own), the page's scripts and styles, the stand-in
pad, KaTeX, and data.json: the index of every question in the bank (so the
overview shows the whole bank), the full detail of a few sample papers with
their images under q/, and demo attempts at the sample questions so the
overview and the review have something to show. The page answers its /api calls
from data.json and keeps attempts in the browser's localStorage; questions
outside the sample papers show in the overview but do not open.
"""
import argparse, json, os, random, re, shutil, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import db, paths  # noqa: E402
from app import marking, server  # noqa: E402

WEB = server.WEB
SAMPLE = ["9709_s23_12_", "9709_w22_32_", "9231_s23_31_", "9618_s23_12_", "TMUA-2023-P1-"]
LIST_FIELDS = ("id", "paper", "series", "component", "variant", "session", "year", "q", "marks",
               "topic", "topic_name")

SHIM = r"""
<script>
// 静态预览:用 data.json 回答页面的 /api 请求,作答记录存在本机浏览器
(function () {
  let data = null;
  const load = async () => data || (data = await (await fetch("data.json")).json());
  const KEY = "qb-preview:attempts:v2";
  const read = () => { try { return JSON.parse(localStorage.getItem(KEY) || "null"); } catch { return null; } };
  const write = (v) => { try { localStorage.setItem(KEY, JSON.stringify(v)); } catch {} };
  let mem = null;
  const all = () => mem || (mem = read() || seed());
  const save = () => write(mem);
  function seed() {
    const out = {}, t0 = Date.now() / 1000 - 86400 * 9;
    let i = 0;
    for (const [qid, a] of Object.entries(data.demo)) {
      const at = t0 + (i++) * 7300;
      out[qid] = [{ id: qid + "#1", qid, n: 1, board: board(qid, 1), started: at - a.seconds, marked: at, ...a }];
    }
    write(out);
    return out;
  }
  const board = (qid, n) => "qb-" + qid + (n === 1 ? "" : "-" + n);
  const blank = (qid) => ({ id: null, qid, n: 1, board: board(qid, 1), started: null, marked: null, score: null,
    max: null, marks: null, seconds: null });
  const current = (qid) => { const a = all()[qid] || []; return a[a.length - 1] || blank(qid); };
  const start = (qid) => { const s = all(); const a = s[qid] || (s[qid] = []); const n = a.length + 1;
    const row = { ...blank(qid), id: qid + "#" + n, n, board: board(qid, n), started: Date.now() / 1000 };
    a.push(row); save(); return row; };
  function lost(parts, marks) {
    const out = [];
    for (const p of parts) {
      const got = (marks || {})[p.label] || {};
      if (p.kind === "codes" || p.kind === "points") {
        p.items.forEach((it, i) => { const t = (got.ticks || [])[i] || 0; if (it.value - t > 0)
          out.push({ part: p.label, code: it.code, kind: it.kind || "P", lost: it.value - t, answer: it.answer, guidance: it.guidance }); });
      } else if (p.kind === "choice") {
        if (got.choice !== p.answer) out.push({ part: "", code: p.answer, kind: "choice", lost: 1,
          answer: (p.options || {})[p.answer] || "", guidance: got.choice || "" });
      } else if ((p.marks || 0) - (got.score || 0) > 0) {
        out.push({ part: p.label, code: "", kind: "score", lost: (p.marks || 0) - (got.score || 0), answer: "", guidance: "" });
      }
    }
    return out;
  }
  window.QB_INKPAD = new URL("inksync/inkpad.js", location.href).href;
  window.QB_API = async (url, body) => {
    const d = await load();
    const u = new URL(url, location.href);
    const q = u.searchParams;
    if (u.pathname.endsWith("/api/filters")) return d.filters;
    if (u.pathname.endsWith("/api/questions")) {
      const s = all();
      return (d.lists[q.get("syllabus") || "9709"] || []).map((r) => {
        const a = s[r.id]; const last = a && a[a.length - 1];
        return { ...r, avail: !!d.details[r.id],
          attempt: last ? { attempts: a.length, score: last.score, max: last.max, marked: last.marked } : null };
      });
    }
    if (u.pathname.includes("/api/question/")) {
      const qid = decodeURIComponent(u.pathname.split("/api/question/")[1]);
      return { ...d.details[qid], attempts: all()[qid] || [], current: current(qid) };
    }
    if (u.pathname.endsWith("/api/review")) {
      const syl = q.get("syllabus") || "9709", s = all(), lostList = [], history = [];
      for (const [qid, as] of Object.entries(s)) {
        const det = d.details[qid];
        if (!det || det.syllabus !== syl) continue;
        for (const a of as) if (a.marked) history.push({ qid, n: a.n, marked: a.marked, score: a.score, max: a.max, seconds: a.seconds });
        const m = as.filter((a) => a.marked).pop();
        if (!m) continue;
        const items = lost(det.parts, m.marks);
        if (items.length) lostList.push({ qid, n: m.n, marked: m.marked, score: m.score, max: m.max, items });
      }
      lostList.sort((a, b) => b.marked - a.marked);
      history.sort((a, b) => b.marked - a.marked);
      return { lost: lostList, history };
    }
    if (u.pathname.endsWith("/api/attempt")) {
      if (body.new) { if (!(all()[body.qid] || []).length) start(body.qid); return start(body.qid); }
      let a = (all()[body.qid] || []).find((x) => x.id === body.id);
      if (!a) a = start(body.qid);
      Object.assign(a, { marks: body.marks, score: body.score, max: body.max, marked: Date.now() / 1000,
                         seconds: body.seconds ?? a.seconds });
      save();
      return a;
    }
    throw new Error("preview: " + url);
  };
})();
</script>
"""


def demo_attempts(con, ids, seed=7):
    """Plausible marked attempts at the sample questions, from their real mark items."""
    rnd = random.Random(seed)
    out = {}
    for qid in ids:
        r = con.execute("SELECT * FROM questions WHERE id=?", (qid,)).fetchone()
        if rnd.random() < 0.25:
            continue                              # some questions left undone
        parts = marking.parts(r)
        skill = rnd.random()
        marks, score, mx = {}, 0, 0
        for p in parts:
            if p["kind"] in ("codes", "points"):
                ticks = []
                for it in p["items"]:
                    dep = it.get("depends")
                    ok = rnd.random() < 0.5 + skill * 0.5 and (dep is None or ticks[dep] is not None)
                    ticks.append(it["value"] if ok else None)
                s = min(sum(t or 0 for t in ticks), p["marks"] or 99)
                marks[p["label"]] = {"ticks": ticks, "score": s}
                score, mx = score + s, mx + (p["marks"] or 0)
            elif p["kind"] == "choice":
                letters = list((p["options"] or dict.fromkeys("ABCDE")).keys())
                c = p["answer"] if rnd.random() < 0.7 else rnd.choice(letters)
                marks[""] = {"choice": c, "score": int(c == p["answer"])}
                score, mx = score + int(c == p["answer"]), mx + 1
            else:
                s = round((p["marks"] or 0) * (0.5 + skill / 2))
                marks[p["label"]] = {"score": s}
                score, mx = score + s, mx + (p["marks"] or 0)
        out[qid] = {"marks": marks, "score": score, "max": mx, "seconds": rnd.randint(90, 840)}
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("out")
    out = ap.parse_args().out
    if os.path.isdir(out):
        shutil.rmtree(out)
    os.makedirs(out)
    con = db.connect()

    filters, lists = {}, {}
    for r in con.execute("SELECT * FROM questions ORDER BY syllabus, year DESC, series, paper, q"):
        syl = r["syllabus"]
        f = filters.setdefault(syl, {"name": server.EXAMS.get(syl, syl), "components": {}, "years": [],
                                     "topics": {}, "minutes": server.MINUTES.get(syl, {})})
        f["components"][r["component"]] = r["component_name"]
        if r["year"] and r["year"] not in f["years"]:
            f["years"].append(r["year"])
        if r["topic"]:
            f["topics"][r["topic"]] = r["topic_name"]
        lists.setdefault(syl, []).append({k: r[k] for k in LIST_FIELDS})
    for f in filters.values():
        f["years"].sort()

    details = {}
    for prefix in SAMPLE:
        for r in con.execute("SELECT * FROM questions WHERE id LIKE ? ORDER BY q", (prefix + "%",)):
            d = server.detail(r, [], None, image_prefix="q/")
            d["syllabus"] = r["syllabus"]
            d["board_image"] = server.image_info(paths.answer_space(r["image"]), "q/")
            details[r["id"]] = d
            for key, src in (("image", paths.resolve(r["image"])),
                             ("board_image", paths.answer_space(r["image"]))):
                if d[key]:
                    dst = os.path.join(out, d[key]["src"])
                    os.makedirs(os.path.dirname(dst), exist_ok=True)
                    shutil.copy(src, dst)
    demo = demo_attempts(con, list(details))
    json.dump({"filters": filters, "lists": lists, "details": details, "demo": demo},
              open(os.path.join(out, "data.json"), "w"), ensure_ascii=False, separators=(",", ":"))

    for f in ("app.js", "tools.js", "icons-qb.js", "style.css"):
        shutil.copy(os.path.join(WEB, f), out)
    for d in ("js", "wb", "fonts"):
        shutil.copytree(os.path.join(WEB, d), os.path.join(out, d), ignore=shutil.ignore_patterns("*.md", "*.txt"))
    shutil.copytree(os.path.join(WEB, "inksync-stub"), os.path.join(out, "inksync"),
                    ignore=shutil.ignore_patterns("test*"))
    shutil.copytree(os.path.join(paths.ASSETS, "vendor", "katex"), os.path.join(out, "katex"))

    html = open(os.path.join(WEB, "index.html")).read()
    head = re.search(r"<head>(.*)</head>", html, re.S).group(1)
    body = re.search(r"<body>(.*)</body>", html, re.S).group(1)
    head = re.sub(r'\s*<meta charset[^>]*>|\s*<meta name="viewport"[^>]*>', "", head)
    head = head.replace("/static/", "").replace("/vendor/", "")
    body = body.replace('<script type="module" src="/static/app.js"></script>',
                        SHIM + '<script type="module" src="app.js"></script>')
    open(os.path.join(out, "index.html"), "w").write(head.strip() + "\n" + body)
    n = sum(len(fs) for _, _, fs in os.walk(out))
    print(f"{len(details)} 题详情,{sum(map(len, lists.values()))} 题索引,{len(demo)} 条示例作答,"
          f"{n} 个文件 -> {out}")


if __name__ == "__main__":
    main()
