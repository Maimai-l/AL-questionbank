// 刷题页:选题、手写作答、按评分细则判分、看详解。
// 手写板按 inksync 2.0 的接口使用(docs/external/inksync-2.0-interface.zh-CN.md);
// 服务端在 2.0 未安装时提供同接口的替身,本文件不需要区分。
import { createInkPad } from "/inksync/inkpad.js";

const $ = (s) => document.querySelector(s);
const api = async (url, body) => {
  const r = await fetch(url, body ? { method: "POST", headers: { "Content-Type": "application/json" },
                                      body: JSON.stringify(body) } : undefined);
  if (!r.ok) throw new Error(`${url}: ${r.status}`);
  return r.json();
};
const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const tex = (el) => window.renderMathInElement?.(el, {
  delimiters: [{ left: "$$", right: "$$", display: true }, { left: "$", right: "$", display: false },
               { left: "\\(", right: "\\)", display: false }, { left: "\\[", right: "\\]", display: true }],
  throwOnError: false,
});

// 记住上次的筛选和题目(只是本机的方便,读写失败时忽略)
const saved = (() => { try { return JSON.parse(localStorage.getItem("qb:ui") || "{}"); } catch { return {}; } })();
const remember = (patch) => { Object.assign(saved, patch); try { localStorage.setItem("qb:ui", JSON.stringify(saved)); } catch {} };

let filters = {}, list = [], question = null, attempt = null, pad = null, readonly = false;

// ------------------------------------------------------------------ 筛选与列表

async function loadFilters() {
  filters = await api("/api/filters");
  const sel = $("#f-syllabus");
  sel.innerHTML = Object.entries(filters).map(([k, v]) => `<option value="${k}">${k} ${esc(v.name)}</option>`).join("");
  sel.value = saved.syllabus && filters[saved.syllabus] ? saved.syllabus : "9709";
  fillDependent();
  for (const id of ["component", "year", "topic", "status"]) {
    if (saved[id]) $(`#f-${id}`).value = saved[id];
  }
}

function fillDependent() {
  const f = filters[$("#f-syllabus").value];
  const opts = (first, entries) => `<option value="">${first}</option>` +
    entries.map(([v, t]) => `<option value="${esc(v)}">${esc(t)}</option>`).join("");
  $("#f-component").innerHTML = opts("全部卷别", Object.entries(f.components).sort().map(([k, n]) => [k, `卷 ${k} ${n || ""}`]));
  $("#f-year").innerHTML = opts("全部年份", f.years.slice().reverse().map((y) => [y, y]));
  $("#f-topic").innerHTML = opts("全部主题", Object.entries(f.topics)
    .sort((a, b) => a[0].localeCompare(b[0], undefined, { numeric: true })).map(([k, n]) => [k, `${k} ${n}`]));
}

async function loadList() {
  const q = new URLSearchParams();
  for (const id of ["syllabus", "component", "year", "topic", "status", "text"]) {
    const v = $(`#f-${id}`).value.trim();
    if (v) q.set(id, v);
    remember({ [id]: $(`#f-${id}`).value });
  }
  list = await api(`/api/questions?${q}`);
  $("#count").textContent = `${list.length} 题`;
  $("#list").innerHTML = list.map((r, i) => {
    const a = r.attempt, s = a && a.score != null
      ? `<span class="score ${a.score >= a.max ? "full" : a.score > 0 ? "part" : "zero"}">${a.score}/${a.max}</span>`
      : a ? `<span class="score">做过</span>` : "";
    return `<li data-i="${i}"><span class="qname">${esc(r.paper)} Q${r.q}</span>${s}
      <span class="topic">${esc(r.session || "")} · ${r.marks ?? "?"} 分 · ${esc(r.topic_name || "")}</span></li>`;
  }).join("");
  markCurrent();
}

function markCurrent() {
  for (const li of document.querySelectorAll("#list li")) {
    li.classList.toggle("on", question && list[li.dataset.i]?.id === question.id);
  }
}

// ------------------------------------------------------------------ 题目与手写板

function boardSpec(q, n) {
  const create = {
    name: `${q.paper} Q${q.q}` + (n > 1 ? ` 第 ${n} 次` : ""),
    canvas: { mode: "column", width: q.board_width },       // 宽度固定,向下留出作答空间
    background: { pattern: "blank" },
    layers: q.image ? [{ src: q.image.src, x: 0, y: 0, width: q.board_width }] : [],
    data: { qid: q.id, attempt: n },
  };
  return create;
}

async function openBoard(a, ro = false) {
  attempt = a;
  readonly = ro;
  const opts = { create: boardSpec(question, a.n), readonly: ro };
  if (!pad) {
    pad = createInkPad($("#pad"), { board: a.board, ...opts, storage: "qb:" });
    pad.on("status", (s) => ($("#sync").textContent = { online: "已同步", syncing: "同步中", offline: "未连接", local: "仅本机" }[s] || s));
    pad.on("history", ({ undo, redo }) => { $("#undo").disabled = !undo; $("#redo").disabled = !redo; });
    pad.on("outdated", () => banner("服务端已升级,请刷新页面"));
    pad.on("error", ({ reason }) => banner(`手写板:${reason}`));
    $("#sync").textContent = { local: "仅本机" }[pad.status] || pad.status || "";
  } else {
    await pad.open(a.board, opts);
  }
  $("#toolbar").classList.toggle("readonly", ro);
}

async function show(qid) {
  question = await api(`/api/question/${encodeURIComponent(qid)}`);
  remember({ qid });
  $("#title").textContent = `${question.paper} Q${question.q} · ${question.marks ?? "?"} 分 · ${question.topic_name || ""}`;
  markCurrent();
  fillAttempts();
  await openBoard(question.current);
  renderMarking();
  renderExplain();
}

function fillAttempts() {
  const as = question.attempts;
  const cur = question.current;
  const rows = as.length ? as : [cur];
  $("#attempts").innerHTML = rows.map((a) =>
    `<option value="${a.n}">第 ${a.n} 次${a.score != null ? ` · ${a.score}/${a.max}` : ""}</option>`).join("");
  $("#attempts").value = cur.n;
}

// ------------------------------------------------------------------ 判分

function renderMarking() {
  const q = question, prior = attempt.marks || {};
  const html = q.parts.map((p, pi) => {
    const got = prior[p.label] || {};
    const head = `<h3><span>${p.label ? `(${esc(p.label)})` : "整题"}</span><span class="muted">${p.marks ?? "?"} 分</span></h3>`;
    let body = "";
    if (p.kind === "choice") {
      const letters = p.options ? Object.keys(p.options) : ["A", "B", "C", "D", "E"];
      body = `<div class="options">${letters.map((l) =>
        `<button data-choice="${l}" data-p="${pi}">${l}${p.options ? ` ${esc(p.options[l])}` : ""}</button>`).join("")}</div>`;
    } else if (p.kind === "codes" || p.kind === "points") {
      body = p.items.map((it, ii) => {
        const ticked = got.ticks?.[ii];
        const control = it.partial?.length
          ? `<select data-p="${pi}" data-i="${ii}">${[it.value, ...it.partial].map((v) =>
              `<option value="${v}" ${ticked === v ? "selected" : ""}>${v}</option>`).join("")}<option value="" ${ticked == null ? "selected" : ""}>—</option></select>`
          : `<input type="checkbox" data-p="${pi}" data-i="${ii}" ${ticked ? "checked" : ""}>`;
        return `<label class="item" data-p="${pi}" data-i="${ii}">${control}<span class="code">${esc(it.code)}</span>
          <span class="ans">${esc(it.answer)}</span>${it.guidance ? `<span class="guide">${esc(it.guidance)}</span>` : ""}</label>`;
      }).join("");
    } else {
      body = `<label>得分 <input type="number" min="0" max="${p.marks ?? 99}" step="1" data-p="${pi}" data-score value="${got.score ?? ""}"></label>`;
    }
    const scheme = p.ms ? `<details><summary>评分细则原文</summary><div class="scheme">${esc(p.ms)}</div></details>` : "";
    return `<div class="part">${head}${body}${scheme}</div>`;
  }).join("");
  const whole = q.scheme ? `<details><summary>整题评分细则</summary><div class="scheme">${esc(q.scheme)}</div></details>` : "";
  $("#marking").innerHTML = html + whole +
    `<div class="total"><span id="total"></span><button id="save">保存判分</button></div>`;
  tex($("#marking"));
  if (prior && Object.keys(prior).length) restoreChoice(prior);
  updateTotal();
}

function restoreChoice(prior) {
  question.parts.forEach((p, pi) => {
    const c = prior[p.label]?.choice;
    if (p.kind === "choice" && c) pickChoice(pi, c, false);
  });
}

function pickChoice(pi, letter, update = true) {
  const p = question.parts[pi];
  for (const b of document.querySelectorAll(`[data-choice][data-p="${pi}"]`)) {
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
    const dep = document.querySelector(`input[data-p="${pi}"][data-i="${it.depends}"]`);
    const me = document.querySelector(`[data-p="${pi}"][data-i="${ii}"]:is(input,select)`);
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
        const el = document.querySelector(`[data-p="${pi}"][data-i="${ii}"]:is(input,select)`);
        if (el.type === "checkbox") return el.checked ? it.value : null;
        return el.value === "" ? null : Number(el.value);
      });
      const sum = Math.min(ticks.reduce((s, v) => s + (v || 0), 0), partMax || Infinity);
      marks[p.label] = { ticks, score: sum };
      score += sum;
    } else {
      const v = document.querySelector(`[data-p="${pi}"][data-score]`).value;
      const s = v === "" ? 0 : Math.min(Number(v), partMax || Infinity);
      marks[p.label] = { score: s };
      score += s;
    }
  });
  return { marks, score, max };
}

function updateTotal() {
  const { score, max } = collect();
  $("#total").textContent = `合计 ${score} / ${max}`;
}

async function saveMarks() {
  if (readonly) { banner("这是以前的作答,只能查看"); return; }
  const { marks, score, max } = collect();
  const a = await api("/api/attempt", { id: attempt.id, qid: question.id, marks, score, max });
  attempt = a;
  const i = question.attempts.findIndex((x) => x.n === a.n);
  if (i >= 0) question.attempts[i] = a; else question.attempts.push(a);
  question.current = a;
  fillAttempts();
  banner(`已保存:${score}/${max}`);
  renderExplain(true);
  loadList();
}

// ------------------------------------------------------------------ 详解

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

function renderExplain(open = false) {
  const ex = question.explanation;
  if (!ex) { $("#explain").innerHTML = ""; return; }
  $("#explain").innerHTML = `<details ${open ? "open" : ""}><summary>详解</summary>` + ex.parts.map((p) => `
    <h4>${p.label ? `(${esc(p.label)})` : "整题"}</h4>
    <p>${inline(p.approach)}</p>
    <ul>${(p.points || []).map((x) => `<li><b>[${esc(x.mark)}]</b> ${inline(x.point)} <span class="muted">${inline(x.why)}</span></li>`).join("")}</ul>
    ${(p.pitfalls || []).length ? `<p class="muted">常见失分</p><ul>${p.pitfalls.map((x) => `<li>${inline(x)}</li>`).join("")}</ul>` : ""}
    <div class="answer">${md(p.answer)}</div>
    ${(p.terms || []).map((t) => `<span class="term" title="${esc(t.wording)}">${esc(t.term)}</span>`).join("")}
  `).join("") + "</details>";
  tex($("#explain"));
}

// ------------------------------------------------------------------ 其他

function banner(text) {
  const b = $("#banner");
  b.textContent = text;
  b.hidden = false;
  clearTimeout(banner.t);
  banner.t = setTimeout(() => (b.hidden = true), 2500);
}

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

function step(d) {
  const i = list.findIndex((r) => r.id === question?.id);
  const next = list[i + d];
  if (next) show(next.id);
}

function bind() {
  for (const id of ["syllabus", "component", "year", "topic", "status"]) {
    $(`#f-${id}`).addEventListener("change", () => { if (id === "syllabus") fillDependent(); loadList(); });
  }
  let t;
  $("#f-text").addEventListener("input", () => { clearTimeout(t); t = setTimeout(loadList, 300); });
  $("#list").addEventListener("click", (e) => {
    const li = e.target.closest("li");
    if (li) show(list[li.dataset.i].id);
  });
  $("#toggle-side").addEventListener("click", () => $("#side").classList.toggle("hidden"));
  $("#prev").addEventListener("click", () => step(-1));
  $("#next").addEventListener("click", () => step(1));

  for (const b of document.querySelectorAll("[data-tool]")) {
    b.addEventListener("click", () => {
      pad?.setTool({ ...pad.tool, tool: b.dataset.tool });
      for (const o of document.querySelectorAll("[data-tool]")) o.setAttribute("aria-pressed", String(o === b));
    });
  }
  for (const b of document.querySelectorAll("[data-color]")) {
    b.addEventListener("click", () => {
      pad?.setTool({ ...pad.tool, color: b.dataset.color });
      for (const o of document.querySelectorAll("[data-color]")) o.setAttribute("aria-pressed", String(o === b));
    });
  }
  $("#undo").addEventListener("click", () => pad?.undo());
  $("#redo").addEventListener("click", () => pad?.redo());
  $("#fit").addEventListener("click", () => pad?.fit());
  $("#copy").addEventListener("click", async () => {
    if (!question) return;
    banner(question.text && (await copyText(question.text)) ? "已复制题干文本" : "这道题没有可用的题干文本");
  });
  $("#restart").addEventListener("click", async () => {
    if (!question) return;
    const a = await api("/api/attempt", { qid: question.id, new: true });
    question.attempts = (await api(`/api/question/${encodeURIComponent(question.id)}`)).attempts;
    question.current = a;
    fillAttempts();
    await openBoard(a);
    renderMarking();
  });
  $("#attempts").addEventListener("change", async () => {
    const n = Number($("#attempts").value);
    const a = question.attempts.find((x) => x.n === n) || question.current;
    await openBoard(a, n !== question.current.n);      // 以前的作答只读
    renderMarking();
  });
  $("#toggle-mark").addEventListener("click", () => {
    const p = $("#panel");
    p.hidden = !p.hidden;
    $("#toggle-mark").setAttribute("aria-pressed", String(!p.hidden));
  });
  $("#marking").addEventListener("change", (e) => {
    if (e.target.matches("[data-p]")) updateTotal();
  });
  $("#marking").addEventListener("input", (e) => {
    if (e.target.matches("[data-score]")) updateTotal();
  });
  $("#marking").addEventListener("click", (e) => {
    const c = e.target.closest("[data-choice]");
    if (c) pickChoice(Number(c.dataset.p), c.dataset.choice);
    if (e.target.id === "save") saveMarks();
  });
}

(async () => {
  bind();
  await loadFilters();
  await loadList();
  const first = list.find((r) => r.id === saved.qid) || list[0];
  if (first) await show(first.id);
})();
