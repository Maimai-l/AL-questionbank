// 跳转:⌘K 或 / 打开,按试卷代码找题。认得 s23、M/J、12、q5、2023、P3、主题编号和主题名,
// 例如「s23 12 5」「m/j 23 p3」「1.6 q2」「integration」。
import { put, h, icon, EXAMS, paperCode, sessionKey, state } from "./core.js";

const SERIES = { "f/m": "m", "m/j": "s", "o/n": "w" };

function matcher(token, exam) {
  const t = token.toLowerCase();
  if (/^[mswt]\d{2}$/.test(t)) return (r) => r.series === t;
  if (SERIES[t]) return (r) => r.series[0] === SERIES[t];
  if (/^q\d{1,2}$/.test(t)) return (r) => r.q === Number(t.slice(1));
  if (/^p\d$/.test(t)) return (r) => r.component === t.slice(1);
  if (/^\d{4}$/.test(t)) return (r) => r.year === Number(t);
  if (/^\d{1,2}$/.test(t)) {
    // 两位数可能是卷号(12)、年份(23)或题号(5):都算命中,卷号最优先
    const n = Number(t);
    return (r) => (r.paper.split("/")[1] === t ? 3 : 0) || (r.series.slice(1) === t.padStart(2, "0") ? 2 : 0) || (r.q === n ? 1 : 0);
  }
  if (/^\d+\.\d+/.test(t)) return (r) => (r.topic || "").startsWith(t);
  return (r) => (r.topic_name || "").toLowerCase().includes(t) || (r.topic || "").toLowerCase() === t;
}

export function palette(app) {
  let node = null, sel = 0, results = [];

  function open() {
    if (node) return;
    const input = h("input", { placeholder: "s23 12 q5 · 1.6 · integration", autocomplete: "off", spellcheck: "false" });
    const list = h("ul");
    const scrim = h("div.pscrim", { on: { click: close } });
    node = h("div.palette", { role: "dialog", "aria-label": "跳转到题目" },
      h("div.in", { html: icon("search") }, input, h("span.hint", app.exam)), list);
    document.getElementById("layer").append(scrim, node);
    node.scrim = scrim;
    const draw = () => {
      results = search(input.value);
      sel = Math.min(sel, Math.max(0, results.length - 1));
      put(list, ...results.map((r, i) => h(`li${i === sel ? ".sel" : ""}`, {
        on: { click: () => pick(r), mousemove: () => { if (sel !== i) { sel = i; draw(); } } },
      }, h("span.c", r.code), h("span.n", r.name), h("span.k", r.k))));
      list.querySelector(".sel")?.scrollIntoView({ block: "nearest" });
    };
    input.addEventListener("input", () => { sel = 0; draw(); });
    input.addEventListener("keydown", (e) => {
      if (e.key === "ArrowDown") { sel = Math.min(sel + 1, results.length - 1); draw(); e.preventDefault(); }
      if (e.key === "ArrowUp") { sel = Math.max(sel - 1, 0); draw(); e.preventDefault(); }
      if (e.key === "Enter" && results[sel]) pick(results[sel]);
      if (e.key === "Escape") close();
    });
    draw();
    input.focus();
  }

  function close() {
    node?.scrim.remove();
    node?.remove();
    node = null;
  }

  function pick(r) {
    close();
    r.go();
  }

  function search(q) {
    const tokens = q.trim().split(/\s+/).filter(Boolean);
    const out = [];
    const exam = tokens.find((t) => EXAMS.includes(t.toUpperCase()));
    if (exam && exam.toUpperCase() !== app.exam) {
      out.push({ code: exam.toUpperCase(), name: app.filters[exam.toUpperCase()]?.name || "", k: "切换", go: () => app.setExam(exam.toUpperCase()) });
    }
    const rest = tokens.filter((t) => t !== exam);
    const rows = app.lists[app.exam] || [];
    if (!rest.length) return out.concat(recent(rows));
    const ms = rest.map((t) => matcher(t, app.exam));
    const scored = [];
    for (const r of rows) {
      let s = 0;
      for (const m of ms) {
        const v = Number(m(r));
        if (!v) { s = -1; break; }
        s += v;
      }
      if (s > 0) scored.push([s, r]);
    }
    const hits = scored.sort((a, b) => b[0] - a[0] || sessionKey(b[1]) - sessionKey(a[1])
      || a[1].paper.localeCompare(b[1].paper) || a[1].q - b[1].q).slice(0, 60).map(([, r]) => r);
    // 主题:名字或编号对上时,给一条「练这个主题」
    const f = app.filters[app.exam];
    const word = rest.join(" ").toLowerCase();
    for (const [code, name] of Object.entries(f.topics)) {
      if (out.length > 4) break;
      if (code.toLowerCase() === word || (word.length > 2 && name.toLowerCase().includes(word))) {
        const n = rows.filter((r) => r.topic === code).length;
        out.push({ code, name, k: `${n} 题`, go: () => app.practiseTopic(code) });
      }
    }
    return out.concat(hits.map(row));
  }

  const row = (r) => ({
    code: `${paperCode(r)} Q${r.q}`, name: r.topic_name || "",
    k: `[${r.marks ?? "?"}]${r.attempt?.score != null ? ` ${r.attempt.score}/${r.attempt.max}` : ""}`,
    go: () => app.open(r.id, { kind: "paper" }),
  });

  function recent(rows) {
    // 没输入时:未做完的卷里最新的题,以及上次做的那道
    const last = rows.find((r) => r.id === app.saved.qid);
    const fresh = rows.filter((r) => state(r.attempt) === "new").sort((a, b) => sessionKey(b) - sessionKey(a)).slice(0, 8);
    return [last, ...fresh].filter(Boolean).map(row);
  }

  addEventListener("keydown", (e) => {
    const typing = e.target.closest?.("input, textarea, select");
    if ((e.key === "k" && (e.metaKey || e.ctrlKey)) || (e.key === "/" && !typing)) {
      e.preventDefault();
      node ? close() : open();
    }
  });

  return { open, close };
}
