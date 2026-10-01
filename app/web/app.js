// 刷题页:白板铺满窗口,题图是白板底图;选题、作答记录、判分、详解浮在上面。
// 界面照 white-board:只用图标,书写工具栏与 iPad 笔具盘就是白板那一套(tools.js、wb/)。
// 手写板按 inksync 的接口使用;服务端没装 inksync 时提供同接口的替身,本文件不区分。
// 静态预览(app/preview.py)在载入本文件之前设置 window.QB_API 和 window.QB_INKPAD,
// 用打包的样题代替服务端;平时两者都不存在。
import { icon } from "./icons-qb.js";
import { Tools, iconButton } from "./tools.js";
import { el } from "./wb/util.js";

const { createInkPad } = await import(window.QB_INKPAD || "/inksync/inkpad.js");

const $ = (s, root = document) => root.querySelector(s);
const api = window.QB_API || (async (url, body) => {
  const r = await fetch(url, body ? { method: "POST", headers: { "Content-Type": "application/json" },
                                      body: JSON.stringify(body) } : undefined);
  if (!r.ok) throw new Error(`${url}: ${r.status}`);
  return r.json();
});
const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const tex = (node) => window.renderMathInElement?.(node, {
  delimiters: [{ left: "$$", right: "$$", display: true }, { left: "$", right: "$", display: false },
               { left: "\\(", right: "\\)", display: false }, { left: "\\[", right: "\\]", display: true }],
  throwOnError: false,
});

// 记住上次的筛选和题目(只是本机的方便,读写失败时忽略)
const saved = (() => { try { return JSON.parse(localStorage.getItem("qb:ui") || "{}"); } catch { return {}; } })();
const remember = (patch) => { Object.assign(saved, patch); try { localStorage.setItem("qb:ui", JSON.stringify(saved)); } catch {} };

let filters = {}, list = [], question = null, attempt = null, pad = null, readonly = false;
const narrow = matchMedia("(max-width: 640px)");
const touch = navigator.maxTouchPoints > 1;

// ------------------------------------------------------------------ 浮在白板上的控件

const ui = $("#ui");
const status = el("div", { id: "status", title: "同步状态" });
const qname = el("span", { class: "qname" });
const lockMark = el("span", { class: "icon-btn", title: "以前的作答,只能查看", html: icon("lock"), hidden: "" });
const qbar = el("div", { id: "qbar", class: "pill" }, [
  iconButton("back", "上一题", () => step(-1)), qname, lockMark, iconButton("forward", "下一题", () => step(1)),
]);
const buttons = {
  list: iconButton("list", "题目", () => toggleSheet(sheets.list)),
  history: iconButton("history", "作答记录", (e) => showAttempts(e.currentTarget)),
  restart: iconButton("refresh", "再做一遍", () => restart()),
  copy: iconButton("copy", "复制题干文本", () => copyQuestion()),
  explain: iconButton("bulb", "详解", () => toggleSheet(sheets.explain)),
  mark: iconButton("check", "判分", () => toggleSheet(sheets.mark)),
};
const corner = el("div", { id: "topright", class: touch ? "pill tinted" : "pill" }, Object.values(buttons));
const zoombar = el("div", { id: "zoombar", class: "pill" }, [
  iconButton("zoomIn", "放大", () => pad?.zoom(1.25)),
  iconButton("fit", "全览", () => pad?.fit()),
  iconButton("zoomOut", "缩小", () => pad?.zoom(0.8)),
]);
ui.append(status, qbar, corner, zoombar);

const tools = new Tools(ui, {
  onToolChange: (t) => pad?.setTool(t),
  onUndo: () => pad?.undo(),
  onRedo: () => pad?.redo(),
});

// 侧板:列表在左,判分与详解在右(同一时间只开一块);不加遮罩,白板照常能写
function makeSheet(side, button) {
  const node = el("div", { class: `sheet ${side}`, hidden: "" });
  node.button = button;
  ui.append(node);
  return node;
}
const sheets = {
  list: makeSheet("left", buttons.list),
  mark: makeSheet("right", buttons.mark),
  explain: makeSheet("right", buttons.explain),
};

function toggleSheet(sheet, open = sheet.hidden) {
  tools.closePopover();
  for (const s of Object.values(sheets)) {
    const same = s === sheet;
    const sameSide = s.classList.contains("left") === sheet.classList.contains("left");
    // 窄屏上一次只开一块
    if (!same && !(open && (sameSide || narrow.matches))) continue;
    s.hidden = same ? !open : true;
    s.button.classList.toggle("active", !s.hidden);
  }
}

const closeButton = (sheet) => iconButton("close", "关闭", () => toggleSheet(sheet, false));

function toast(name, text) {
  const node = el("div", { class: "toast", html: icon(name) });
  if (text) node.append(el("span", { text }));
  ui.append(node);
  setTimeout(() => node.remove(), 1600);
}

// 页面自己解决不了的事才用一句话
function notice(text) {
  const node = el("div", { class: "notice", html: icon("info") }, [el("span", { text })]);
  node.addEventListener("click", () => node.remove());
  ui.append(node);
  setTimeout(() => node.remove(), 5000);
}

// ------------------------------------------------------------------ 题目列表

const search = el("input", { class: "board-search", type: "search", autocomplete: "off", "aria-label": "搜索题干" });
const sel = Object.fromEntries(["syllabus", "component", "year", "topic", "status"]
  .map((k) => [k, el("select", { "aria-label": k })]));
const qlist = el("ol", { class: "qlist" });
sheets.list.append(
  el("div", { class: "sheet-head" }, [
    el("label", { class: "search-box" }, [el("span", { class: "search-icon", html: icon("search", 18) }), search]),
    closeButton(sheets.list),
  ]),
  el("div", { class: "filters" }, Object.values(sel)),
  qlist,
);

async function loadFilters() {
  filters = await api("/api/filters");
  sel.syllabus.innerHTML = Object.entries(filters)
    .map(([k, v]) => `<option value="${k}">${k} ${esc(v.name)}</option>`).join("");
  sel.syllabus.value = saved.syllabus && filters[saved.syllabus] ? saved.syllabus : "9709";
  sel.status.innerHTML = [["", "全部"], ["new", "未做"], ["done", "做过"], ["wrong", "未拿满分"]]
    .map(([v, t]) => `<option value="${v}">${t}</option>`).join("");
  fillDependent();
  for (const k of ["component", "year", "topic", "status"]) if (saved[k]) sel[k].value = saved[k];
  search.value = saved.text || "";
}

function fillDependent() {
  const f = filters[sel.syllabus.value];
  const opts = (first, entries) => `<option value="">${first}</option>` +
    entries.map(([v, t]) => `<option value="${esc(v)}">${esc(t)}</option>`).join("");
  sel.component.innerHTML = opts("全部卷别", Object.entries(f.components).sort().map(([k, n]) => [k, `${k} ${n || ""}`]));
  sel.year.innerHTML = opts("全部年份", f.years.slice().reverse().map((y) => [y, y]));
  sel.topic.innerHTML = opts("全部主题", Object.entries(f.topics)
    .sort((a, b) => a[0].localeCompare(b[0], undefined, { numeric: true })).map(([k, n]) => [k, `${k} ${n}`]));
}

const scoreClass = (a) => (a.score >= a.max ? "full" : a.score > 0 ? "part" : "zero");

async function loadList() {
  const q = new URLSearchParams();
  for (const [k, node] of Object.entries(sel)) {
    if (node.value) q.set(k, node.value);
    remember({ [k]: node.value });
  }
  if (search.value.trim()) q.set("text", search.value.trim());
  remember({ text: search.value });
  list = await api(`/api/questions?${q}`);
  qlist.innerHTML = list.map((r, i) => {
    const a = r.attempt;
    const got = a && a.score != null ? `<span class="got ${scoreClass(a)}">${a.score}/${a.max}</span>`
      : a ? `<span class="got">·</span>` : "";
    return `<li data-i="${i}"><span class="name">${esc(r.paper)} · Q${r.q}</span>${got}
      <span class="sub">${esc(r.session || "")} · [${r.marks ?? "?"}] · ${esc(r.topic_name || "")}</span></li>`;
  }).join("");
  markCurrent();
}

function markCurrent() {
  for (const li of qlist.children) li.classList.toggle("on", !!question && list[li.dataset.i]?.id === question.id);
}

// ------------------------------------------------------------------ 题目与手写板

function boardSpec(q, n) {
  // 题图在上,带答题线的版本优先:每个小问下面保留原卷的答题区
  const img = q.board_image || q.image;
  return {
    name: `${q.paper} Q${q.q}` + (n > 1 ? ` #${n}` : ""),
    canvas: { mode: "column", width: q.board_width },       // 宽度固定,向下留出作答空间
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
    pad = createInkPad($("#pad"), { board: a.board, ...opts, storage: "qb:", tool: tools.toolState() });
    pad.on("status", (s) => (status.className = s));
    pad.on("history", ({ undo, redo }) => tools.setHistory(undo, redo));
    pad.on("outdated", () => notice("服务端已升级,请刷新页面"));
    pad.on("error", ({ reason }) => notice(reason));
    status.className = pad.status || "";
  } else {
    await pad.open(a.board, opts);
  }
  tools.setReadonly(ro);
  lockMark.hidden = !ro;
}

async function show(qid) {
  question = await api(`/api/question/${encodeURIComponent(qid)}`);
  remember({ qid });
  qname.textContent = `${question.paper} · Q${question.q}`;
  qname.title = `${question.session || ""} · [${question.marks ?? "?"}] · ${question.topic_name || ""}`;
  markCurrent();
  await openBoard(question.current);
  renderMarking();
  renderExplain();
  buttons.explain.disabled = !question.explanation;
  buttons.copy.disabled = !question.text;
  if (!question.explanation && !sheets.explain.hidden) toggleSheet(sheets.explain, false);
}

function step(d) {
  const i = list.findIndex((r) => r.id === question?.id);
  const next = list[i + d];
  if (next) show(next.id);
}

// 作答记录:每次一块白板,以前的只读
function showAttempts(anchor) {
  if (!question) return;
  const rows = question.attempts.length ? question.attempts : [question.current];
  const box = el("div", { class: "attempts" });
  for (const a of rows.slice().reverse()) {
    const got = a.score != null ? el("span", { class: `got ${scoreClass(a)}`, text: `${a.score}/${a.max}` }) : null;
    box.append(el("button", {
      class: a.n === attempt?.n ? "on" : "",
      onclick: async () => {
        tools.closePopover();
        await openBoard(a, a.n !== question.current.n);
        renderMarking();
      },
    }, [el("span", { text: `#${a.n}` }), got]));
  }
  tools.showPopover(anchor, [box]);
}

async function restart() {
  if (!question) return;
  const a = await api("/api/attempt", { qid: question.id, new: true });
  question.attempts = (await api(`/api/question/${encodeURIComponent(question.id)}`)).attempts;
  question.current = a;
  await openBoard(a);
  renderMarking();
  toast("refresh", `#${a.n}`);
}

async function copyQuestion() {
  if (!question?.text) return;
  if (await copyText(question.text)) toast("copy");
  else notice("复制失败");
}

// ------------------------------------------------------------------ 判分

const total = el("span", { class: "total" });
const saveButton = el("button", { class: "btn primary", title: "保存判分", html: icon("check"),
                                  onclick: () => saveMarks() });
const markBody = el("div");
sheets.mark.append(
  el("div", { class: "sheet-head" }, [total, el("span", { class: "grow" }), saveButton, closeButton(sheets.mark)]),
  markBody,
);

function schemeBlock(text) {
  const pre = el("div", { class: "scheme", text, hidden: "" });
  const toggle = iconButton("doc", "评分细则原文", () => {
    pre.hidden = !pre.hidden;
    toggle.classList.toggle("active", !pre.hidden);
  }, "scheme-toggle");
  return [toggle, pre];
}

function renderMarking() {
  const q = question, prior = attempt.marks || {};
  markBody.innerHTML = "";
  q.parts.forEach((p, pi) => {
    const got = prior[p.label] || {};
    const [toggle, pre] = p.ms ? schemeBlock(p.ms) : [null, null];
    const head = el("div", { class: "part-head" }, [
      el("span", { text: p.label ? `(${p.label})` : `Q${q.q}` }), toggle,
      el("span", { class: "tariff", text: `[${p.marks ?? "?"}]` }),
    ]);
    const body = el("div");
    if (p.kind === "choice") {
      const letters = p.options ? Object.keys(p.options) : ["A", "B", "C", "D", "E"];
      body.className = "options";
      body.innerHTML = letters.map((l) =>
        `<button data-choice="${l}" data-p="${pi}">${l}${p.options ? ` ${esc(p.options[l])}` : ""}</button>`).join("");
    } else if (p.kind === "codes" || p.kind === "points") {
      body.innerHTML = p.items.map((it, ii) => {
        const ticked = got.ticks?.[ii];
        const control = it.partial?.length
          ? `<select data-p="${pi}" data-i="${ii}">${[it.value, ...it.partial].map((v) =>
              `<option value="${v}" ${ticked === v ? "selected" : ""}>${v}</option>`).join("")}<option value="" ${ticked == null ? "selected" : ""}>—</option></select>`
          : `<input type="checkbox" data-p="${pi}" data-i="${ii}" ${ticked ? "checked" : ""}>`;
        return `<label class="item" data-p="${pi}" data-i="${ii}">${control}<span class="code">${esc(it.code)}</span>
          <span class="ans">${esc(it.answer)}</span>${it.guidance ? `<span class="guide">${esc(it.guidance)}</span>` : ""}</label>`;
      }).join("");
    } else {
      body.className = "manual";
      body.innerHTML = `<input type="number" min="0" max="${p.marks ?? 99}" step="1" inputmode="numeric"
        data-p="${pi}" data-score value="${got.score ?? ""}"><span>/ ${p.marks ?? "?"}</span>`;
    }
    markBody.append(el("div", { class: "part" }, [head, pre, body]));
  });
  if (q.scheme && !q.parts.some((p) => p.ms)) {
    const [toggle, pre] = schemeBlock(q.scheme);
    markBody.append(el("div", { class: "part" }, [el("div", { class: "part-head" }, [toggle]), pre]));
  }
  tex(markBody);
  restoreChoice(prior);
  q.parts.forEach((_, pi) => applyDependencies(pi));
  updateTotal();
  saveButton.disabled = readonly;
}

function restoreChoice(prior) {
  question.parts.forEach((p, pi) => {
    p._choice = null;
    const c = prior[p.label]?.choice;
    if (p.kind === "choice" && c) pickChoice(pi, c, false);
  });
}

function pickChoice(pi, letter, update = true) {
  const p = question.parts[pi];
  for (const b of markBody.querySelectorAll(`[data-choice][data-p="${pi}"]`)) {
    b.classList.remove("right", "wrong");
    b.setAttribute("aria-pressed", String(b.dataset.choice === letter));
    if (b.dataset.choice === p.answer) b.classList.add("right");
    else if (b.dataset.choice === letter) b.classList.add("wrong");
  }
  p._choice = letter;
  if (update) updateTotal();
}

// 勾选时维持依赖:A 依赖其前面的 M,DM 依赖其前面的 *M
function applyDependencies(pi) {
  const p = question.parts[pi];
  if (p.kind !== "codes") return;
  p.items.forEach((it, ii) => {
    if (it.depends == null) return;
    const dep = markBody.querySelector(`input[data-p="${pi}"][data-i="${it.depends}"]`);
    const me = markBody.querySelector(`[data-p="${pi}"][data-i="${ii}"]:is(input,select)`);
    const ok = !dep || dep.checked;
    me.closest(".item").classList.toggle("locked", !ok);
    if (!ok) { if (me.type === "checkbox") me.checked = false; else me.value = ""; }
  });
}

function collect() {
  const marks = {};
  let score = 0, max = 0;
  question.parts.forEach((p, pi) => {
    const partMax = p.marks ?? 0;
    max += partMax;
    if (p.kind === "choice") {
      const ok = p._choice && p._choice === p.answer;
      marks[p.label] = { choice: p._choice || null, score: ok ? 1 : 0 };
      score += ok ? 1 : 0;
    } else if (p.kind === "codes" || p.kind === "points") {
      applyDependencies(pi);
      const ticks = p.items.map((it, ii) => {
        const node = markBody.querySelector(`[data-p="${pi}"][data-i="${ii}"]:is(input,select)`);
        if (node.type === "checkbox") return node.checked ? it.value : null;
        return node.value === "" ? null : Number(node.value);
      });
      const sum = Math.min(ticks.reduce((s, v) => s + (v || 0), 0), partMax || Infinity);
      marks[p.label] = { ticks, score: sum };
      score += sum;
    } else {
      const v = markBody.querySelector(`[data-p="${pi}"][data-score]`).value;
      const s = v === "" ? 0 : Math.min(Number(v), partMax || Infinity);
      marks[p.label] = { score: s };
      score += s;
    }
  });
  return { marks, score, max };
}

function updateTotal() {
  const { score, max } = collect();
  total.textContent = `${score} / ${max}`;
}

async function saveMarks() {
  if (readonly) return;
  const { marks, score, max } = collect();
  const a = await api("/api/attempt", { id: attempt.id, qid: question.id, marks, score, max });
  attempt = a;
  const i = question.attempts.findIndex((x) => x.n === a.n);
  if (i >= 0) question.attempts[i] = a; else question.attempts.push(a);
  question.current = a;
  toast("check", `${score}/${max}`);
  loadList();
}

markBody.addEventListener("change", (e) => { if (e.target.matches("[data-p]")) updateTotal(); });
markBody.addEventListener("input", (e) => { if (e.target.matches("[data-score]")) updateTotal(); });
markBody.addEventListener("click", (e) => {
  const c = e.target.closest("[data-choice]");
  if (c && !readonly) pickChoice(Number(c.dataset.p), c.dataset.choice);
});

// ------------------------------------------------------------------ 详解

const explainBody = el("div", { class: "explain" });
sheets.explain.append(el("div", { class: "sheet-head" }, [el("span", { class: "grow" }), closeButton(sheets.explain)]),
                      explainBody);

// 详解里的 answer 是 Markdown:代码块、表格、加粗、行内代码、列表
function md(src) {
  const out = [];
  const lines = String(src || "").split("\n");
  for (let i = 0; i < lines.length; i++) {
    const l = lines[i];
    if (l.startsWith("```")) {
      const code = [];
      for (i++; i < lines.length && !lines[i].startsWith("```"); i++) code.push(lines[i]);
      out.push(`<pre><code>${esc(code.join("\n"))}</code></pre>`);
    } else if (/^\s*\|.*\|\s*$/.test(l)) {
      const rows = [];
      for (; i < lines.length && /^\s*\|.*\|\s*$/.test(lines[i]); i++) rows.push(lines[i]);
      i--;
      out.push("<table>" + rows.filter((r) => !/^\s*\|[\s|:-]+\|\s*$/.test(r)).map((r, ri) =>
        "<tr>" + r.trim().slice(1, -1).split("|").map((c) => `<${ri ? "td" : "th"}>${inline(c.trim())}</${ri ? "td" : "th"}>`).join("") + "</tr>").join("") + "</table>");
    } else if (/^\s*[-*] /.test(l)) {
      out.push(`<ul><li>${inline(l.replace(/^\s*[-*] /, ""))}</li></ul>`);
    } else if (l.trim()) {
      out.push(`<p>${inline(l)}</p>`);
    }
  }
  return out.join("");
}
const inline = (s) => esc(s).replace(/\*\*(.+?)\*\*/g, "<b>$1</b>").replace(/`([^`]+)`/g, "<code>$1</code>");

function renderExplain() {
  const ex = question.explanation;
  explainBody.innerHTML = !ex ? "" : ex.parts.map((p) => `
    <div class="part">
      <div class="part-head"><span>${p.label ? `(${esc(p.label)})` : `Q${question.q}`}</span></div>
      <p>${inline(p.approach)}</p>
      <ul>${(p.points || []).map((x) => `<li><span class="mk">[${esc(x.mark)}]</span> ${inline(x.point)}
        <span class="why">${inline(x.why)}</span></li>`).join("")}</ul>
      ${(p.pitfalls || []).map((x) => `<div class="pit">${icon("alert")}<span>${inline(x)}</span></div>`).join("")}
      <div class="answer">${md(p.answer)}</div>
      ${(p.terms || []).length ? `<div class="terms">${p.terms.map((t) =>
        `<span title="${esc(t.wording)}">${esc(t.term)}</span>`).join("")}</div>` : ""}
    </div>`).join("");
  tex(explainBody);
}

// ------------------------------------------------------------------ 其他

// http 的局域网地址不是安全上下文,Safari 没有 navigator.clipboard;退回 execCommand
async function copyText(text) {
  try { await navigator.clipboard.writeText(text); return true; } catch {}
  const t = $("#clip");
  t.value = text;
  t.select();
  t.setSelectionRange(0, text.length);
  const ok = document.execCommand("copy");
  t.blur();
  return ok;
}

function bind() {
  for (const [k, node] of Object.entries(sel)) {
    node.addEventListener("change", () => { if (k === "syllabus") fillDependent(); loadList(); });
  }
  let t;
  search.addEventListener("input", () => { clearTimeout(t); t = setTimeout(loadList, 300); });
  qlist.addEventListener("click", (e) => {
    const li = e.target.closest("li");
    if (!li) return;
    show(list[li.dataset.i].id);
    if (narrow.matches) toggleSheet(sheets.list, false);
  });
  addEventListener("keydown", (e) => {
    if (e.target.closest("input, select, textarea")) return;
    if (e.key === "ArrowLeft") step(-1);
    if (e.key === "ArrowRight") step(1);
  });
}

(async () => {
  bind();
  await loadFilters();
  await loadList();
  const first = list.find((r) => r.id === saved.qid) || list[0];
  if (first) await show(first.id);
  else toggleSheet(sheets.list, true);
})();
