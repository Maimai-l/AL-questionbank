// 练习:左边是当前这一套(一张卷,或一个主题下的题),中间是白板,右边判分与详解。
//
// 每次作答一块白板,题图(带答题区的版本优先)是白板底图;书写工具栏就是
// white-board 那一套(tools.js)。计时只算白板在眼前的时间,时间预算按考试时长
// 与本卷总分折算到每道题。
import { put, h, $, icon, ib, api, toast, pop, closePop, copyText, paperCode, sessionShort, sittingKey,
         state, fmtClock, fmtDate, isCaie } from "./core.js";
import { marking } from "./marking.js";
import { explain } from "./explain.js";
import { Tools } from "../tools.js";

export function workspace(app, createInkPad) {
  // ---------------------------------------------------------------- 结构
  const railHead = h("div.rail-head");
  const qrows = h("ul.qrows");
  const railFoot = h("div.rail-foot");
  const rail = h("aside.rail", railHead, qrows, railFoot);

  const qno = h("span.qno");
  const tariff = h("span.tariff");
  const topicEl = h("span.topic");
  const clockTime = h("span.num");
  const clockBudget = h("span.budget.num");
  const clock = h("span.clock", { title: "用时 / 建议用时" }, clockTime, clockBudget);
  const btn = {
    rail: ib("rail", "题目列表", () => toggle("rail")),
    prev: ib("back", "上一题", () => step(-1)),
    next: ib("forward", "下一题", () => step(1)),
    copy: ib("copy", "复制题干文本", () => copyQuestion()),
    history: ib("history", "作答记录", (e) => attempts(e.currentTarget)),
    restart: ib("refresh", "再做一遍", () => restart()),
    panel: ib("panel", "判分与详解", () => toggle("panel")),
  };
  const qhead = h("header.qhead", btn.rail, h("span", qno), tariff, topicEl, h("span.grow"), clock,
    h("span.qtools", btn.prev, btn.next, btn.copy, btn.history, btn.restart, btn.panel));
  const padHost = h("div#pad");
  const lockmark = h("div.lockmark", { hidden: true, html: icon("lock") + "<span>以前的作答</span>" });
  const board = h("div.board", padHost, lockmark);
  const desk = h("section.desk", qhead, board);

  const tabMark = h("button.on", { on: { click: () => tab("mark") } }, "评分");
  const tabExplain = h("button", { on: { click: () => tab("explain") } }, "详解");
  const body = h("div.panel-body");
  const total = h("span.total");
  const spent = h("span.spent");
  const record = h("button.bt.primary", { html: icon("check"), on: { click: () => save() } }, "记分");
  const foot = h("div.panel-foot", total, spent, h("span.grow"), record);
  const panel = h("aside.panel", h("nav.tabs", tabMark, tabExplain), body, foot);

  const root = h("div.ws", rail, desk, panel);

  const mk = marking(({ score, max }) => {
    put(total, String(score), h("small", ` / ${max}`));
  });

  // ---------------------------------------------------------------- 状态
  let set = { kind: "paper", ids: [] };
  let question = null, attempt = null, readonly = false, pad = null, current = "mark";
  const elapsed = new Map();        // 作答 → 已用秒数
  let ticking = null;

  const tools = new Tools(board, {
    onToolChange: (t) => pad?.setTool(t),
    onUndo: () => pad?.undo(),
    onRedo: () => pad?.redo(),
  }, $("#layer"));

  // 窄屏上列表与面板浮在白板上,默认收起
  const narrow = matchMedia("(max-width: 1280px)");
  const narrower = matchMedia("(max-width: 1000px)");
  function toggle(which, open) {
    if (which === "rail") {
      const cls = narrow.matches ? "rail-open" : "no-rail";
      const now = narrow.matches ? !root.classList.contains("rail-open") : root.classList.contains("no-rail");
      const want = open ?? now;
      root.classList.toggle(cls, narrow.matches ? want : !want);
      btn.rail.classList.toggle("on", want);
    } else {
      const want = open ?? root.classList.contains("no-panel");
      root.classList.toggle("no-panel", !want);
      btn.panel.classList.toggle("on", want);
    }
  }
  if (narrower.matches) toggle("panel", false); else btn.panel.classList.add("on");
  if (!narrow.matches) btn.rail.classList.add("on");

  // ---------------------------------------------------------------- 套题
  function setFor(qid, kind) {
    const rows = app.lists[app.exam] || [];
    const me = rows.find((r) => r.id === qid);
    if (!me) return { kind: "paper", ids: [qid] };
    if (kind === "topic" && me.topic) {
      const ids = rows.filter((r) => r.topic === me.topic)
        .sort((a, b) => b.year - a.year || a.paper.localeCompare(b.paper) || a.q - b.q).map((r) => r.id);
      return { kind, key: me.topic, ids };
    }
    const ids = rows.filter((r) => sittingKey(r) === sittingKey(me)).sort((a, b) => a.q - b.q).map((r) => r.id);
    return { kind: "paper", key: sittingKey(me), ids };
  }

  function renderRail() {
    const rows = app.lists[app.exam] || [];
    const byId = new Map(rows.map((r) => [r.id, r]));
    const items = set.ids.map((id) => byId.get(id)).filter(Boolean);
    const me = byId.get(question?.id) || items[0];
    if (!me) return;
    const f = app.filters[app.exam];
    const mode = h("div.mode",
      h(`button${set.kind === "paper" ? ".on" : ""}`, { on: { click: () => { set = setFor(question.id, "paper"); renderRail(); } } }, "整卷"),
      h(`button${set.kind === "topic" ? ".on" : ""}`, { disabled: !me.topic, on: { click: () => { set = setFor(question.id, "topic"); renderRail(); } } }, "同主题"),
      set.kind === "list" ? h("button.on", "失分") : null);
    if (set.kind === "topic") {
      put(railHead, h("div.code", me.topic), h("div.title", f.topics[me.topic] || me.topic_name || ""),
        h("div.meta.num", `${items.length} 题`), mode);
    } else if (set.kind === "list") {
      put(railHead, h("div.code", "复盘"), h("div.title", set.title || "失分题"), h("div.meta.num", `${items.length} 题`), mode);
    } else {
      const min = f.minutes?.[me.component];
      const max = items.reduce((s, r) => s + (r.marks || 1), 0);
      put(railHead, h("div.code", paperCode(me)),
        h("div.title", isCaie(app.exam) ? f.components[me.component] : f.name),
        h("div.meta.num", h("span", sessionShort(me)), min ? h("span", `${min} min`) : null, h("span", `${max}${isCaie(app.exam) ? " 分" : " 题"}`)),
        mode);
    }
    put(qrows, ...items.map((r) => {
      const a = r.attempt, st = state(a);
      return h(`li${r.id === question?.id ? ".on" : ""}`, { on: { click: () => { if (r.avail !== false) show(r.id); } }, style: r.avail === false ? { opacity: .4 } : null },
        h("span.qn", String(r.q)),
        h("span.qt", set.kind === "paper"
          ? [isCaie(app.exam) ? h("span.mono", `[${r.marks ?? "?"}] `) : null, r.topic_name || ""]
          : [h("span.mono", `${sessionShort(r)} · ${r.paper.split("/")[1]} `), r.topic_name || ""]),
        h(`span.qs.s-${st}`, a?.score != null ? `${a.score}/${a.max}` : a ? "·" : ""));
    }));
    const marked = items.filter((r) => r.attempt?.score != null);
    const got = marked.reduce((s, r) => s + r.attempt.score, 0);
    const of = set.kind === "paper" ? items.reduce((s, r) => s + (r.marks || 1), 0) : marked.reduce((s, r) => s + r.attempt.max, 0);
    put(railFoot, h("span.muted", set.kind === "paper" ? "本卷得分" : "已判得分"), h("b", String(got), h("small", ` / ${of}`)));
    qrows.querySelector("li.on")?.scrollIntoView({ block: "nearest" });
  }

  // ---------------------------------------------------------------- 题目
  async function open(qid, opts = {}) {
    if (opts.ids) set = { kind: "list", ids: opts.ids, title: opts.title };
    else if (!set.ids.includes(qid) || opts.kind) set = setFor(qid, opts.kind || set.kind);
    await show(qid, opts);
  }

  async function show(qid, opts = {}) {
    question = await api(`/api/question/${encodeURIComponent(qid)}`);
    app.question = question;
    const row = (app.lists[app.exam] || []).find((r) => r.id === qid);
    put(qno, h("i", "Q"), String(question.q));
    tariff.textContent = question.parts[0]?.kind === "choice" ? "" : `[${question.marks ?? "?"}]`;
    topicEl.textContent = question.topic_name || "";
    btn.copy.disabled = !question.text;
    tabExplain.disabled = !question.explanation;
    if (!question.explanation && current === "explain") tab("mark");
    budget(row);
    let a = question.current;
    if (opts.attempt) a = question.attempts.find((x) => x.n === opts.attempt) || a;
    if (opts.fresh) a = await api("/api/attempt", { qid: question.id, new: true });
    await openBoard(a, a.n !== (opts.fresh ? a.n : question.current.n));
    renderRail();
    app.remember({ qid });
    if (narrow.matches) toggle("rail", false);
  }

  function boardSpec(q, n) {
    const img = q.board_image || q.image;
    return {
      name: `${q.paper} Q${q.q}` + (n > 1 ? ` #${n}` : ""),
      canvas: { mode: "column", width: q.board_width },
      background: { pattern: "blank" },
      layers: img ? [{ src: img.src, x: 0, y: 0, width: q.board_width }] : [],
      data: { qid: q.id, attempt: n },
    };
  }

  async function openBoard(a, ro = false) {
    attempt = a;
    readonly = ro;
    const opts = { create: boardSpec(question, a.n), readonly: ro };
    if (!pad) {
      pad = createInkPad(padHost, { board: a.board, ...opts, storage: "qb:", tool: tools.toolState() });
      pad.on("status", (s) => app.sync(s));
      pad.on("history", ({ undo, redo }) => tools.setHistory(undo, redo));
      pad.on("outdated", () => toast("info", "服务端已升级,请刷新"));
      pad.on("error", ({ reason }) => toast("info", reason));
      app.sync(pad.status);
    } else {
      await pad.open(a.board, opts);
    }
    tools.setReadonly(ro);
    lockmark.hidden = !ro;
    record.disabled = ro;
    renderPanel();
    startClock();
  }

  function tab(which) {
    current = which;
    tabMark.classList.toggle("on", which === "mark");
    tabExplain.classList.toggle("on", which === "explain");
    renderPanel();
  }

  function renderPanel() {
    if (!question) return;
    foot.hidden = current !== "mark";
    if (current === "mark") {
      mk.render(question, attempt, readonly);
      put(body, mk.body);
    } else {
      put(body, explain(question));
    }
    body.scrollTop = 0;
  }

  async function save() {
    if (readonly) return;
    const { marks, score, max } = mk.collect();
    const seconds = Math.round(elapsed.get(key()) || 0);
    const a = await api("/api/attempt", { id: attempt.id, qid: question.id, marks, score, max, seconds });
    attempt = a;
    const i = question.attempts.findIndex((x) => x.n === a.n);
    if (i >= 0) question.attempts[i] = a; else question.attempts.push(a);
    question.current = a;
    toast("tick", `${score} / ${max}`);
    await app.refreshList();
    renderRail();
  }

  async function restart() {
    if (!question) return;
    const a = await api("/api/attempt", { qid: question.id, new: true });
    question.attempts = (await api(`/api/question/${encodeURIComponent(question.id)}`)).attempts;
    question.current = a;
    await openBoard(a);
    toast("refresh", `#${a.n}`);
  }

  function attempts(anchor) {
    if (!question) return;
    const rows = question.attempts.length ? question.attempts : [question.current];
    pop(anchor, rows.slice().reverse().map((a) => h(`button${a.n === attempt?.n ? ".on" : ""}`, {
      on: { click: async () => { closePop(); await openBoard(a, a.n !== question.current.n); } },
    }, `#${a.n}`, h("span.muted", a.marked ? fmtDate(a.marked) : "—"),
       h("span.r", a.score != null ? `${a.score}/${a.max}` : "未判"))));
  }

  async function copyQuestion() {
    if (question?.text && (await copyText(question.text))) toast("copy", "题干已复制");
  }

  function step(d) {
    const i = set.ids.indexOf(question?.id);
    const next = set.ids[i + d];
    if (next) show(next);
  }

  // ---------------------------------------------------------------- 计时
  let budgetSec = 0;
  function budget(row) {
    budgetSec = 0;
    if (!row) return;
    const f = app.filters[app.exam];
    const min = f.minutes?.[row.component];
    if (!min) return;
    const sitting = (app.lists[app.exam] || []).filter((r) => sittingKey(r) === sittingKey(row));
    const total = sitting.reduce((s, r) => s + (r.marks || 1), 0);
    budgetSec = (min * 60 * (row.marks || 1)) / total;
  }
  const key = () => `${question?.id}#${attempt?.n}`;
  function startClock() {
    clearInterval(ticking);
    if (!elapsed.has(key())) elapsed.set(key(), attempt?.seconds || 0);
    const draw = () => {
      const s = elapsed.get(key()) || 0;
      clockTime.textContent = fmtClock(s);
      clockBudget.textContent = budgetSec ? `/ ${fmtClock(budgetSec)}` : "";
      clock.classList.toggle("over", !!budgetSec && s > budgetSec);
      spent.textContent = s ? fmtClock(s) : "";
    };
    draw();
    ticking = setInterval(() => {
      if (readonly || document.hidden || root.closest("[hidden]")) return;
      elapsed.set(key(), (elapsed.get(key()) || 0) + 1);
      draw();
    }, 1000);
  }

  addEventListener("keydown", (e) => {
    if (root.closest("[hidden]") || e.target.closest("input, select, textarea") || e.metaKey || e.ctrlKey) return;
    if (e.key === "ArrowLeft") step(-1);
    if (e.key === "ArrowRight") step(1);
  });

  return { root, open, refresh: renderRail, get question() { return question; } };
}
