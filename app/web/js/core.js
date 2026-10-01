// Shared by every view: data access, element helper, formatting, the floating layer.
import { icon } from "../icons-qb.js";

export { icon };

// 静态预览(app/preview.py)在载入前设置 window.QB_API,用打包的样题代替服务端
export const api = window.QB_API || (async (url, body) => {
  const r = await fetch(url, body ? { method: "POST", headers: { "Content-Type": "application/json" },
                                      body: JSON.stringify(body) } : undefined);
  if (!r.ok) throw new Error(`${url}: ${r.status}`);
  return r.json();
});

/** h("div.cls#id", {on: {click}, ...attrs}, ...children) */
export function h(spec, props, ...children) {
  const [, tag = "div", rest = ""] = spec.match(/^([a-z0-9]*)(.*)$/i);
  const node = document.createElement(tag || "div");
  for (const part of rest.match(/[.#][^.#]+/g) || []) {
    if (part[0] === ".") node.classList.add(part.slice(1));
    else node.id = part.slice(1);
  }
  if (props && (typeof props !== "object" || props instanceof Node || Array.isArray(props))) {
    children.unshift(props);
    props = null;
  }
  for (const [k, v] of Object.entries(props || {})) {
    if (v == null || v === false) continue;
    if (k === "on") for (const [ev, fn] of Object.entries(v)) node.addEventListener(ev, fn);
    else if (k === "html") node.innerHTML = v;
    else if (k === "text") node.textContent = v;
    else if (k === "style" && typeof v === "object") Object.assign(node.style, v);
    else if (k === "class") node.className += ` ${v}`;
    else if (v === true) node.setAttribute(k, "");
    else node.setAttribute(k, v);
  }
  for (const c of children.flat(Infinity)) {
    if (c == null || c === false) continue;
    node.append(c instanceof Node ? c : document.createTextNode(String(c)));
  }
  return node;
}

export const $ = (s, root = document) => root.querySelector(s);
/** replaceChildren that skips null / false and flattens arrays */
export function put(node, ...kids) {
  node.replaceChildren(...kids.flat(Infinity).filter((k) => k != null && k !== false)
    .map((k) => (k instanceof Node ? k : document.createTextNode(String(k)))));
  return node;
}
export const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
export const svg = (name) => h("span", { html: icon(name), style: { display: "contents" } });

export function ib(name, title, onclick, cls = "") {
  return h(`button.ib${cls ? "." + cls : ""}`, { title, "aria-label": title, html: icon(name), on: { click: onclick } });
}

export const tex = (node) => window.renderMathInElement?.(node, {
  delimiters: [{ left: "$$", right: "$$", display: true }, { left: "$", right: "$", display: false },
               { left: "\\(", right: "\\)", display: false }, { left: "\\[", right: "\\]", display: true }],
  throwOnError: false,
  errorColor: "inherit",          // 细则里个别公式写坏了:照原文显示,不标红(红色留给分数)
});

// 本机的小记忆:上次的考试、视图、题目(读写失败时忽略)
const KEY = "qb:v2";
export const saved = (() => { try { return JSON.parse(localStorage.getItem(KEY) || "{}"); } catch { return {}; } })();
export const remember = (patch) => {
  Object.assign(saved, patch);
  try { localStorage.setItem(KEY, JSON.stringify(saved)); } catch {}
};

// ------------------------------------------------------------------ the exams

export const EXAMS = ["9709", "9231", "9618", "TMUA", "TSA", "BMAT"];
export const isCaie = (syl) => /^\d{4}$/.test(syl);
const SERIES = { m: "F/M", s: "M/J", w: "O/N" };
const SERIES_ORDER = { w: 3, s: 2, m: 1 };

/** 9709/12/M/J/23, the code printed on every Cambridge paper; TMUA P1 2023 otherwise. */
export function paperCode(r) {
  const yy = (r.series || "").slice(1);
  if (isCaie(r.paper.split("/")[0])) return `${r.paper}/${SERIES[r.series[0]] || "?"}/${yy}`;
  const [syl, c] = r.paper.split("/");
  return `${syl} ${syl === "TMUA" ? "P" : "S"}${c} · ${r.year}`;
}
export function sessionShort(r) {
  return isCaie(r.paper.split("/")[0]) ? `${SERIES[r.series[0]] || "?"} ${(r.series || "").slice(1)}` : String(r.year);
}
/** Newest first: a year's November, then June, then March. */
export const sessionKey = (r) => r.year * 10 + (SERIES_ORDER[r.series[0]] || 0);
/** One sitting of one paper: 9709/12 in s23. */
export const sittingKey = (r) => `${r.paper}|${r.series}`;

export function state(a) {
  if (!a) return "new";
  if (a.score == null) return "done";
  if (a.score >= a.max) return "full";
  return a.score > 0 ? "part" : "zero";
}

export const fmtClock = (s) => {
  s = Math.max(0, Math.round(s));
  const hh = Math.floor(s / 3600), mm = Math.floor((s % 3600) / 60), ss = s % 60;
  return (hh ? `${hh}:${String(mm).padStart(2, "0")}` : String(mm).padStart(2, "0")) + `:${String(ss).padStart(2, "0")}`;
};
export const fmtMin = (min) => (min >= 60 ? `${Math.floor(min / 60)}h${min % 60 ? String(min % 60).padStart(2, "0") : ""}` : `${min}′`);
export const fmtDate = (t) => {
  const d = new Date(t * 1000);
  return `${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
};
export const pct = (a, b) => (b ? Math.round((a / b) * 100) : 0);

// ------------------------------------------------------------------ floating layer

const layer = () => $("#layer");

export function toast(name, text) {
  const t = h("div.toast2", { html: icon(name) }, text ? h("span", text) : null);
  layer().append(t);
  setTimeout(() => t.remove(), 1700);
}

let tipNode = null;
export function tip(anchor, lines) {
  hideTip();
  if (!lines) return;
  const r = anchor.getBoundingClientRect();
  tipNode = h("div.tip", lines);
  layer().append(tipNode);
  const w = tipNode.offsetWidth;
  const x = Math.min(Math.max(r.left + r.width / 2, w / 2 + 8), innerWidth - w / 2 - 8);
  tipNode.style.left = `${x}px`;
  tipNode.style.top = `${r.top}px`;
  if (r.top - tipNode.offsetHeight - 14 < 0) {
    tipNode.style.transform = "translate(-50%, 10px)";
    tipNode.style.top = `${r.bottom}px`;
  }
}
export function hideTip() { tipNode?.remove(); tipNode = null; }

let popNode = null, popCloser = null;
export function pop(anchor, content) {
  closePop();
  const r = anchor.getBoundingClientRect();
  popNode = h("div.pop", content);
  layer().append(popNode);
  const w = popNode.offsetWidth, ht = popNode.offsetHeight;
  popNode.style.left = `${Math.min(Math.max(8, r.right - w), innerWidth - w - 8)}px`;
  popNode.style.top = `${r.bottom + ht + 8 < innerHeight ? r.bottom + 6 : Math.max(8, r.top - ht - 6)}px`;
  popCloser = (e) => { if (!popNode?.contains(e.target) && !anchor.contains(e.target)) closePop(); };
  setTimeout(() => addEventListener("pointerdown", popCloser, true), 0);
  return popNode;
}
export function closePop() {
  popNode?.remove();
  popNode = null;
  if (popCloser) removeEventListener("pointerdown", popCloser, true);
  popCloser = null;
}

// http 的局域网地址不是安全上下文,Safari 没有 navigator.clipboard;退回 execCommand
export async function copyText(text) {
  try { await navigator.clipboard.writeText(text); return true; } catch {}
  const t = $("#clip");
  t.value = text;
  t.select();
  t.setSelectionRange(0, text.length);
  const ok = document.execCommand("copy");
  t.blur();
  return ok;
}
