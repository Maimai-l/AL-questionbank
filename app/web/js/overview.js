// 总览:一门考试的全部真题,一卷一行、一题一格,格宽与分值成正比;右边是考纲主题。
import { put, h, icon, tip, hideTip, paperCode, sessionShort, sessionKey, sittingKey, state, pct,
         fmtMin, isCaie } from "./core.js";

const STATE_NAME = { new: "未做", done: "做过", full: "满分", part: "部分得分", zero: "零分" };

export function overview(app) {
  const main = h("section.ov-main");
  const side = h("aside.ov-side");
  const root = h("div.ov", main, side);
  let topic = null;         // 选中的主题:墙上其他格子淡出
  let rows = [];

  function render() {
    const exam = app.exam;
    const f = app.filters[exam];
    rows = app.lists[exam] || [];
    put(main, masthead(exam, f), legend(), ...components(exam, f));
    put(side, ...syllabus(exam, f));
    applyTopic();
  }

  // ---------------------------------------------------------------- 标题与数字

  function masthead(exam, f) {
    const done = rows.filter((r) => r.attempt);
    const marked = done.filter((r) => r.attempt.score != null);
    const got = marked.reduce((s, r) => s + r.attempt.score, 0);
    const max = marked.reduce((s, r) => s + r.attempt.max, 0);
    const years = rows.map((r) => r.year);
    const papers = new Set(rows.map(sittingKey)).size;
    return h("header.masthead",
      h("div",
        h("div.kicker", isCaie(exam) ? "Cambridge International AS & A Level" : "Admissions test"),
        h("h1", f.name, " ", h("em", isCaie(exam) ? exam : "")),
        h("div.sub.num", `${papers} 套卷 · ${rows.length} 题 · ${Math.min(...years)}–${Math.max(...years)}`)),
      h("div.figures",
        figure(done.length, `/${rows.length}`, "已做"),
        figure(max ? pct(got, max) : "—", max ? "%" : "", "得分率"),
        figure(max - got, "", "失分"),
        resume()));
  }

  // 上次做到的那道题;没有时是最新一卷里第一道没做的
  function resume() {
    const last = rows.find((r) => r.id === app.saved.qidBy?.[app.exam]);
    const next = last || [...rows].sort((a, b) => sessionKey(b) - sessionKey(a) || a.paper.localeCompare(b.paper) || a.q - b.q)
      .find((r) => !r.attempt && r.avail !== false);
    if (!next) return null;
    return h("button.resume", { on: { click: () => app.open(next.id, { kind: "paper" }) } },
      h("span.kicker", last ? "继续" : "开始"),
      h("span.mono", `${paperCode(next)} · Q${next.q}`),
      h("span", { html: icon("forward") }));
  }
  const figure = (v, unit, label) => h("div.fig", h("b", v, unit ? h("small", unit) : null), h("span", label));

  function legend() {
    return h("div.legend",
      ...["new", "done", "full", "part", "zero"].map((s) => h("span", h(`i.sw.s-${s}`), STATE_NAME[s])),
      h("span.scale", "格宽 ∝ 分值"));
  }

  // ---------------------------------------------------------------- 题墙

  function components(exam, f) {
    const width = Math.max(main.clientWidth - 80, 600);
    const comps = [...new Set(rows.map((r) => r.component))].sort();
    return comps.map((c) => {
      const cr = rows.filter((r) => r.component === c);
      const variants = [...new Set(cr.map((r) => r.variant))].sort();
      // 一次考试的一卷:按卷号和考季分组
      const sittings = new Map();
      for (const r of cr) {
        const k = sittingKey(r);
        if (!sittings.has(k)) sittings.set(k, []);
        sittings.get(k).push(r);
      }
      for (const qs of sittings.values()) qs.sort((a, b) => a.q - b.q);
      const total = (qs) => qs.reduce((s, r) => s + (r.marks || 1), 0);
      const maxMarks = Math.max(...[...sittings.values()].map(total));
      const maxQ = Math.max(...[...sittings.values()].map((q) => q.length));
      const ppm = Math.min(isCaie(exam) ? 5 : 18,
        (width - 70 - variants.length * 18) / variants.length / (maxMarks + maxQ * 0.6));
      const sessions = [...new Map([...sittings.values()].map((qs) => [qs[0].series, qs[0]])).values()]
        .sort((a, b) => sessionKey(b) - sessionKey(a));

      const grid = h("div.wall", { style: { gridTemplateColumns: `56px repeat(${variants.length}, max-content)` } });
      grid.append(h("span"), ...variants.map((v) => h("span.vh", isCaie(exam) ? `${exam}/${c}${v}` : "")));
      let lastYear = null;
      for (const s of sessions) {
        grid.append(h(`span.sess${s.year !== lastYear ? ".year" : ""}`, sessionShort(s)));
        lastYear = s.year;
        for (const v of variants) {
          const qs = sittings.get(`${exam}/${c}${v}|${s.series}`) || sittings.get(`${s.paper.split("/")[0]}/${c}${v}|${s.series}`);
          grid.append(qs ? strip(qs, ppm) : h("span.strip.empty", { style: { width: `${maxMarks * ppm}px` } }));
        }
      }
      const doneQ = cr.filter((r) => r.attempt).length;
      const min = f.minutes?.[c];
      return h("section.paper-block",
        h("div.paper-head",
          h("h2", isCaie(exam) ? `Paper ${c}` : (f.components[c] || "").split(" (")[0]),
          h("span.meta", isCaie(exam) ? f.components[c] : ""),
          h("span.meta.num", [min ? fmtMin(min) : null, maxMarks ? `${maxMarks}${isCaie(exam) ? " 分" : " 题"}` : null].filter(Boolean).join(" · ")),
          h("span.pstat.num", `${doneQ} / ${cr.length}`)),
        grid);
    });
  }

  function strip(qs, ppm) {
    return h("span.strip", qs.map((r) => {
      const st = state(r.attempt);
      const cell = h(`button.cell.s-${st}`, {
        style: { width: `${Math.max(6, (r.marks || 1) * ppm + 0.6 * ppm)}px` },
        "aria-label": `${paperCode(r)} Q${r.q}`,
        "data-topic": r.topic || "",
        "data-id": r.id,
        class: r.avail === false ? "off" : null,
        on: {
          click: () => { hideTip(); if (r.avail !== false) app.open(r.id, { kind: "paper" }); },
          mouseenter: (e) => tip(e.currentTarget, cellTip(r, st)),
          mouseleave: hideTip,
          focus: (e) => tip(e.currentTarget, cellTip(r, st)),
          blur: hideTip,
        },
      });
      if (app.question?.id === r.id) cell.classList.add("here");
      return cell;
    }));
  }

  function cellTip(r, st) {
    const a = r.attempt;
    return [
      h("div.t1", h("span", `${paperCode(r)}  Q${r.q}`), h("span", `[${r.marks ?? "?"}]`)),
      h("div.t2", r.topic_name || ""),
      h("div.t2", a?.score != null ? `${a.score} / ${a.max} · ${STATE_NAME[st]}` : STATE_NAME[st]),
      r.avail === false ? h("div.t2", "预览未收录") : null,
    ];
  }

  // ---------------------------------------------------------------- 考纲主题

  function syllabus(exam, f) {
    const by = new Map();
    for (const r of rows) {
      if (!r.topic) continue;
      const t = by.get(r.topic) || { total: 0, done: 0, got: 0, max: 0 };
      t.total++;
      if (r.attempt) t.done++;
      if (r.attempt?.score != null) { t.got += r.attempt.score; t.max += r.attempt.max; }
      by.set(r.topic, t);
    }
    const codes = [...by.keys()].sort((a, b) => a.localeCompare(b, undefined, { numeric: true }));
    const list = h("ul.topics", codes.map((code) => {
      const t = by.get(code);
      const li = h(`li${code === topic ? ".on" : ""}`, {
        on: { click: () => { topic = topic === code ? null : code; put(side, ...syllabus(exam, f)); applyTopic(); } },
      },
        h("span.code", code),
        h("span.name", { title: f.topics[code] || "" }, f.topics[code] || code),
        h("span.rate.num", `${t.done}/${t.total}`),
        h("span.bar", { title: t.max ? `得分率 ${pct(t.got, t.max)}%` : "" }, bar(t)));
      return li;
    }));
    const head = h("div.side-h", h("h3", "考纲主题"), h("span.muted.num", `${codes.length}`));
    if (!topic) return [head, list];
    const n = rows.filter((r) => r.topic === topic).length;
    return [head,
      h("div.topic-act",
        h("button.bt.primary", { on: { click: () => app.practiseTopic(topic) }, html: icon("pen") }, `练习 ${n} 题`),
        h("button.bt", { on: { click: () => { topic = null; put(side, ...syllabus(exam, f)); applyTopic(); } } }, "全部")),
      list];
  }

  // 覆盖了多少题;其中得到的分(墨色)与丢掉的分(红色)按比例分开
  function bar(t) {
    const cov = t.total ? t.done / t.total : 0;
    const rate = t.max ? t.got / t.max : 1;
    return [h("i", { style: { width: `${cov * rate * 100}%` } }),
            t.max ? h("i.lost", { style: { left: `${cov * rate * 100}%`, width: `${cov * (1 - rate) * 100}%` } }) : null,
            !t.max && t.done ? h("i.done", { style: { width: `${cov * 100}%` } }) : null];
  }

  function applyTopic() {
    for (const c of main.querySelectorAll(".cell[data-topic]")) {
      c.classList.toggle("dim", !!topic && c.dataset.topic !== topic);
    }
  }

  return { root, render };
}
