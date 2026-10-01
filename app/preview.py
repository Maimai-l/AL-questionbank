#!/usr/bin/env python3
"""A static copy of the practice page with sample questions, for previewing
the interface without running the server.

    python3 app/preview.py OUT_DIR [--ids-file f]

OUT_DIR gets the page (index.html, written to be published as an Artifact:
no <html>/<head>/<body> of its own), the page's script and style, the stand-in
pad, KaTeX, data.json with the sample questions in the server's own format
(app/server.py detail()), and their images under q/. The page answers its
/api calls from data.json and keeps attempts in the browser's localStorage;
the boards are the stand-in pad's, also in localStorage.
"""
import argparse, json, os, re, shutil, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib import db, paths  # noqa: E402
from app import server, store  # noqa: E402

WEB = server.WEB
SAMPLE = [  # (syllabus, paper id prefix, how many)
    ("9709", "9709_s23_12_", 11), ("9231", "9231_s23_31_", 4),
    ("9618", "9618_s23_12_", 8), ("9618", "9618_s23_22_", 3), ("TMUA", "TMUA-2023-P1-", 10),
]

SHIM = r"""
<script>
// 静态预览:用 data.json 回答页面的 /api 请求,作答记录存在本机浏览器
(function () {
  let data = null;
  const load = async () => data || (data = await (await fetch("data.json")).json());
  const KEY = "qb-preview:attempts";
  const read = () => { try { return JSON.parse(localStorage.getItem(KEY) || "{}"); } catch { return {}; } };
  const write = (v) => { try { localStorage.setItem(KEY, JSON.stringify(v)); } catch {} };
  const board = (qid, n) => "qb-" + qid + (n === 1 ? "" : "-" + n);
  const current = (qid) => { const a = read()[qid] || []; return a[a.length - 1] ||
    { id: null, qid, n: 1, board: board(qid, 1), score: null, max: null, marks: null }; };
  const start = (qid) => { const all = read(); const a = all[qid] || (all[qid] = []);
    const n = a.length + 1; const row = { id: qid + "#" + n, qid, n, board: board(qid, n), started: Date.now() / 1000,
      score: null, max: null, marks: null }; a.push(row); write(all); return row; };
  window.QB_INKPAD = new URL("inksync/inkpad.js", location.href).href;
  window.QB_API = async (url, body) => {
    const d = await load();
    const u = new URL(url, location.href);
    if (u.pathname.endsWith("/api/filters")) return d.filters;
    if (u.pathname.endsWith("/api/questions")) {
      const q = u.searchParams, all = read();
      return d.list.filter((r) => r.syllabus === (q.get("syllabus") || "9709")
        && (!q.get("component") || r.component === q.get("component"))
        && (!q.get("year") || String(r.year) === q.get("year"))
        && (!q.get("topic") || r.topic === q.get("topic"))
        && (!q.get("text") || (d.details[r.id].text || "").toLowerCase().includes(q.get("text").toLowerCase())))
        .map((r) => { const a = all[r.id]; const last = a && a[a.length - 1];
          return { ...r, attempt: last ? { attempts: a.length, score: last.score, max: last.max } : null }; })
        .filter((r) => { const s = q.get("status"); const a = r.attempt;
          return !s || (s === "new" ? !a : s === "done" ? !!a : a && a.score != null && a.score < a.max); });
    }
    if (u.pathname.includes("/api/question/")) {
      const qid = decodeURIComponent(u.pathname.split("/api/question/")[1]);
      return { ...d.details[qid], attempts: read()[qid] || [], current: current(qid) };
    }
    if (u.pathname.endsWith("/api/attempt")) {
      if (body.new) { if (!(read()[body.qid] || []).length) start(body.qid); return start(body.qid); }
      const all = read(); let a = (all[body.qid] || []).find((x) => x.id === body.id);
      if (!a) { start(body.qid); return (await window.QB_API(url, { ...body, id: body.qid + "#1" })); }
      Object.assign(a, { marks: body.marks, score: body.score, max: body.max, marked: Date.now() / 1000 });
      write(all); return a;
    }
    throw new Error("preview: " + url);
  };
})();
</script>
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("out")
    a = ap.parse_args()
    out = a.out
    if os.path.isdir(out):
        shutil.rmtree(out)
    os.makedirs(out)
    con = db.connect()
    rows = []
    for syl, prefix, n in SAMPLE:
        rows += con.execute("SELECT * FROM questions WHERE syllabus=? AND id LIKE ? ORDER BY q LIMIT ?",
                            (syl, prefix + "%", n)).fetchall()
    details, listing, filters = {}, [], {}
    for r in rows:
        d = server.detail(r, [], None, image_prefix="q/")
        details[r["id"]] = d
        listing.append({"id": r["id"], "syllabus": r["syllabus"], "component": r["component"],
                        "paper": r["paper"], "session": r["session"], "year": r["year"], "q": r["q"],
                        "marks": r["marks"], "topic": r["topic"], "topic_name": r["topic_name"],
                        "q_quality": r["q_quality"]})
        f = filters.setdefault(r["syllabus"], {"name": server.EXAMS[r["syllabus"]], "components": {},
                                               "years": [], "topics": {}})
        f["components"][r["component"]] = r["component_name"]
        if r["year"] not in f["years"]:
            f["years"].append(r["year"])
        if r["topic"]:
            f["topics"][r["topic"]] = r["topic_name"]
        if d["image"]:
            src = paths.resolve(r["image"])
            dst = os.path.join(out, d["image"]["src"])
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy(src, dst)
    json.dump({"filters": filters, "list": listing, "details": details},
              open(os.path.join(out, "data.json"), "w"), ensure_ascii=False)
    shutil.copy(os.path.join(WEB, "app.js"), out)
    shutil.copy(os.path.join(WEB, "style.css"), out)
    shutil.copytree(os.path.join(WEB, "inksync-stub"), os.path.join(out, "inksync"),
                    ignore=shutil.ignore_patterns("test*"))
    shutil.copytree(os.path.join(paths.ASSETS, "vendor", "katex"), os.path.join(out, "katex"))
    html = open(os.path.join(WEB, "index.html")).read()
    body = re.search(r"<body>(.*)</body>", html, re.S).group(1)
    body = body.replace('<script type="module" src="/static/app.js"></script>',
                        SHIM + '<script type="module" src="app.js"></script>')
    page = ('<title>刷题页预览</title>\n'
            '<link rel="stylesheet" href="katex/katex.min.css">\n'
            '<link rel="stylesheet" href="style.css">\n'
            '<script defer src="katex/katex.min.js"></script>\n'
            '<script defer src="katex/auto-render.min.js"></script>\n' + body)
    open(os.path.join(out, "index.html"), "w").write(page)
    n = sum(len(fs) for _, _, fs in os.walk(out))
    print(f"{len(rows)} 题,{n} 个文件 -> {out}")


if __name__ == "__main__":
    main()
