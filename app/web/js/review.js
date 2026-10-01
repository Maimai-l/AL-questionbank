// 复盘:每道题最近一次判分里没拿到的分,逐个分码列出;左边是失分的构成与主题排行。
import { put, h, icon, ib, esc, tex, api, paperCode, fmtDate, fmtClock, pct } from "./core.js";

// 分码的种类:颜色与说明
const KINDS = {
  M: { name: "方法分", desc: "Method:方法正确即得", color: "var(--ink)" },
  A: { name: "准确分", desc: "Accuracy:依赖前面的方法分", color: "var(--red)" },
  B: { name: "独立分", desc: "Independent:结果正确即得", color: "var(--cell-part)" },
  DM: { name: "依赖方法分", desc: "依赖前面带 * 的方法分", color: "var(--blue)" },
  DB: { name: "依赖独立分", desc: "依赖前面带 * 的方法分", color: "var(--blue)" },
  P: { name: "得分点", desc: "评分细则的逐条要点", color: "var(--red)" },
  choice: { name: "选择题", desc: "选错的题", color: "var(--red)" },
  score: { name: "手动评分", desc: "细则无分码,按填写的分数", color: "var(--ink-4)" },
};
const kindOf = (k) => {
  const s = (k || "").replace(/^SC ?/, "");
  return KINDS[s] ? s : "score";
};

export function review(app) {
  const side = h("aside.rv-side");
  const main = h("section.rv-main");
  const root = h("div.rv", side, main);
  let data = { lost: [], history: [] };
  let filter = null;          // {topic} | {kind}

  async function render() {
    data = await api(`/api/review?syllabus=${encodeURIComponent(app.exam)}`);
    draw();
  }

  function rowsById() { return new Map((app.lists[app.exam] || []).map((r) => [r.id, r])); }

  function draw() {
    const byId = rowsById();
    const f = app.filters[app.exam];
    const entries = data.lost.map((e) => ({ ...e, row: byId.get(e.qid) })).filter((e) => e.row);
    const items = entries.flatMap((e) => e.items.map((it) => ({ ...it, e })));
    const lostTotal = items.reduce((s, it) => s + it.lost, 0);

    // 构成
    const byKind = new Map();
    for (const it of items) byKind.set(kindOf(it.kind), (byKind.get(kindOf(it.kind)) || 0) + it.lost);
    const kinds = [...byKind.entries()].sort((a, b) => b[1] - a[1]);
    // 主题排行
    const byTopic = new Map();
    for (const it of items) {
      const t = it.e.row.topic || "—";
      byTopic.set(t, (byTopic.get(t) || 0) + it.lost);
    }
    const topics = [...byTopic.entries()].sort((a, b) => b[1] - a[1]).slice(0, 12);
    const top = topics[0]?.[1] || 1;

    put(side, 
      h("div.kicker", f.name),
      h("h1", "失分", h("span.muted.num", { style: { fontSize: "18px", marginLeft: "10px" } }, `${lostTotal} 分 · ${entries.length} 题`)),
      lostTotal ? h("div.lostbar", kinds.map(([k, v]) => h("i", {
        title: `${KINDS[k].name} ${v}`, style: { flex: v, background: KINDS[k].color },
      }))) : null,
      h("ul.kinds", kinds.map(([k, v]) => h("li", {
        style: { cursor: "pointer" },
        on: { click: () => { filter = filter?.kind === k ? null : { kind: k }; draw(); } },
      },
        h("i", { style: { background: KINDS[k].color } }),
        h("span", { title: KINDS[k].desc }, h("b", k === "P" || k === "choice" || k === "score" ? "" : `${k} `), h("span.desc", KINDS[k].name)),
        h("span.num.mono", { style: filter?.kind === k ? { color: "var(--blue)" } : null }, `${v} · ${pct(v, lostTotal)}%`)))),
      topics.length ? h("div.side-h", h("h3", "失分最多的主题")) : null,
      h("ul.rank", topics.map(([t, v]) => h(`li${filter?.topic === t ? ".on" : ""}`, {
        on: { click: () => { filter = filter?.topic === t ? null : { topic: t }; draw(); } },
      }, h("span.name", `${t}  ${f.topics[t] || ""}`), h("span.v", `−${v}`), h("span.bar", h("i", { style: { width: `${(v / top) * 100}%` } }))))),
      data.history.length ? h("div.side-h", { style: { marginTop: "28px" } }, h("h3", "最近作答")) : null,
      h("ul.hist", data.history.slice(0, 30).map((a) => {
        const r = byId.get(a.qid);
        if (!r) return null;
        return h("li", { on: { click: () => app.open(a.qid, { attempt: a.n }) } },
          h("span.d", fmtDate(a.marked)),
          h("span", `${paperCode(r)} Q${r.q}`),
          h("span.t", a.seconds ? fmtClock(a.seconds) : ""),
          h("span.s", `${a.score}/${a.max}`));
      })));

    // 账本
    const shown = entries.filter((e) => !filter
      || (filter.topic && (e.row.topic || "—") === filter.topic)
      || (filter.kind && e.items.some((it) => kindOf(it.kind) === filter.kind)));
    const ids = shown.map((e) => e.qid);
    put(main, 
      h("div.ledger-h",
        h("h2", filter?.topic ? `${filter.topic} ${f.topics[filter.topic] || ""}` : filter?.kind ? KINDS[filter.kind].name : "逐项失分"),
        h("span.muted.num", `${shown.length} 题`),
        shown.length ? h("button.bt.primary", { style: { marginLeft: "auto" }, html: icon("refresh"),
          on: { click: () => app.open(ids[0], { ids, title: "失分题", fresh: true }) } }, "依次重做") : null),
      shown.length ? null : h("div.empty-state", { html: icon("ledger") }, h("p", entries.length ? "没有符合的记录" : "判过分的题,没拿到的分会列在这里")),
      ...shown.map((e) => entry(e, ids)));
    tex(main);
  }

  function entry(e, ids) {
    const r = e.row;
    const items = filter?.kind ? e.items.filter((it) => kindOf(it.kind) === filter.kind) : e.items;
    return h("article.entry",
      h("div.where",
        h("span.q", `Q${r.q}`),
        h("span.code", paperCode(r)),
        h("span.tn", r.topic_name || ""),
        h("span.score.num", `${e.score} / ${e.max}`)),
      h("div.items", items.map((it) => h("div.item",
        h("span.pl", h("span.p", it.part ? `(${it.part})` : ""),
          h("span.chip.lost", it.kind === "choice" ? `→ ${it.code}` : it.code || `−${it.lost}`)),
        h("div.ans", { html: esc(it.answer || (it.kind === "score" ? "未按分码评分" : "")) }),
        it.kind === "choice" ? (it.guidance ? h("div.gd", `选了 ${it.guidance}`) : null)
          : it.guidance ? h("div.gd", it.guidance) : null))),
      h("div.act",
        ib("history", "看原作答", () => app.open(e.qid, { ids, title: "失分题", attempt: e.n })),
        ib("refresh", "重做", () => app.open(e.qid, { ids, title: "失分题", fresh: true }))));
  }

  return { root, render };
}
