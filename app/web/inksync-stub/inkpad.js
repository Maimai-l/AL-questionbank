// inksync 2.0 前端替身（stub）
//
// 用途：inksync 2.0 发布之前，刷题页面按 2.0 的前端接口开发和测试。接口依据
// docs/external/inksync-2.0-interface.zh-CN.md 第 4、5、7 节。2.0 发布后把
// import 路径从本文件换成服务端提供的 /inksync/inkpad.js 即可，调用方式不变。
//
// 与真正的 2.0 的差异：
//   - 不联网。不管 options.transport 填什么都按 "local" 工作，status 固定为 "local"；
//     options.report 忽略。
//   - 每块白板的 {meta, strokes} 存在 localStorage（键为 storage 前缀 + 白板 id），
//     不是 IndexedDB；没有「最多缓存 200 块」的淘汰。
//   - 像素橡皮擦（eraserMode "pixel"）未实现，退化为整笔擦除（object）。
//     读入的笔画带 m（擦除遮罩）或 cut（切口）时照原样保存，但绘制时忽略它们。
//   - 笔迹轮廓是简化版：每个采样点一个圆，相邻两圆之间补公切线梯形，一次填充。
//     没有用 perfect-freehand，所以转弯处和笔锋与 2.0 略有不同；粗细随压感的
//     曲线沿用白板项目 stroke.js 的 strokeRadius。
//   - 权限规则只有 readonly；caps.unlock 恒为 false，locked 恒为 null。
//   - 不接外壳：window.whiteboardShell 只装一个空对象，shell.active 恒为 false。
//   - 不会触发 locked、deleted、interrupted、outdated、rejected、shell、message，
//     但 on() 接受这些事件名。
//   - 约定没有写 op 事件里 op 的格式，这里沿用 1.0.1 的：
//       {op:"add", strokes}、{op:"remove", ids}、{op:"restore", strokes}、
//       {op:"clear"}、{op:"meta", meta: patch}
//   - 只依赖浏览器原生 API，不依赖白板项目的其他文件。

const VERSION = "2.0.0-stub";
const BOARD_ID = /^[A-Za-z0-9_-]{1,64}$/;
const SPACE_NAME = /^[a-z0-9-]{0,32}$/;
const COLOR = /^#[0-9a-fA-F]{6}$/;
const TOOLS = ["pen", "marker", "highlighter", "eraser"];
const INK_TOOLS = ["pen", "marker", "highlighter"];
const PATTERNS = ["blank", "grid", "lines", "dots"];
const EVENTS = [
  "status", "history", "meta", "change", "op", "strokestart", "strokeend", "locked", "caps",
  "deleted", "error", "rejected", "interrupted", "outdated", "shell", "message",
];
const DEFAULT_TOOL = { tool: "pen", color: "#1b1b1f", width: 3, eraserMode: "object" };

// 第 5、7 节的上限
const MAX_POINTS = 20000;
const MAX_LAYERS = 1000;
const MAX_DATA_BYTES = 16 * 1024;
const MAX_NAME = 64;
const MAX_DIM = 100000;
const BUCKETS = [640, 1024, 1600, 2400]; // src 中 {w} 的档位

const MIN_SCALE = 0.05;
const MAX_SCALE = 20;
const HIGHLIGHTER_ALPHA = 0.3;
const ERASER_MIN = 16; // 橡皮擦直径（屏幕像素）不小于这个值
const EXPORT_MARGIN = 32;
const EXPORT_MAX_SIDE = 16384; // 浏览器画布的边长上限，超出时自动降低 scale
const EXPORT_MAX_PIXELS = 64e6;

// 外观，取自白板项目 renderer.js
const OUTSIDE = "#e5e5ea";
const LINE = "#d7dbe6";
const SHADOW = "rgba(60, 60, 67, .2)";
const SHADOW_BLUR = 16;
const SHADOW_LIFT = 3;
const GRID_STEP = 40;
const MIN_PATTERN_PX = 14;
const TAU = Math.PI * 2;

// 约定 4.5 节：SDK 只装这一个全局对象。替身不接外壳，留空。
if (typeof window !== "undefined" && !window.whiteboardShell) window.whiteboardShell = {};

export function createInkPad(container, options = {}) {
  return new InkPad(container, options);
}

// ------------------------------------------------------------------ 小工具

const clamp = (v, lo, hi) => Math.min(hi, Math.max(lo, v));
const clone = (v) => (v === undefined ? undefined : JSON.parse(JSON.stringify(v)));
const isObj = (v) => v !== null && typeof v === "object" && !Array.isArray(v);
const nowSec = () => Date.now() / 1000;
const round = (v, k = 100) => Math.round(v * k) / k;

function uid(n) {
  const bytes = crypto.getRandomValues(new Uint8Array(n));
  return Array.from(bytes, (b) => "0123456789abcdefghijklmnopqrstuvwxyz"[b % 36]).join("");
}

function fail(message) {
  throw new TypeError(message);
}

// ------------------------------------------------------------------ 校验（5.1 节）

function normalizeName(name) {
  if (typeof name !== "string") fail("name 必须是字符串");
  if ([...name].length > MAX_NAME) fail(`name 超过 ${MAX_NAME} 个字符`);
  return name;
}

function dimension(v, what) {
  if (typeof v !== "number" || !Number.isFinite(v) || v < 1 || v > MAX_DIM) {
    fail(`${what} 必须是 1 到 ${MAX_DIM} 的数`);
  }
  return v;
}

function normalizeCanvas(c) {
  if (c == null) return { mode: "infinite" };
  if (!isObj(c)) fail("canvas 必须是对象");
  const mode = c.mode ?? "infinite";
  if (mode === "infinite") return { mode };
  if (mode === "column") return { mode, width: dimension(c.width, "canvas.width") };
  if (mode === "fixed") {
    return { mode, width: dimension(c.width, "canvas.width"), height: dimension(c.height, "canvas.height") };
  }
  return fail(`canvas.mode 不合法：${mode}`);
}

function normalizeBackground(b) {
  if (b == null) b = {};
  if (!isObj(b)) fail("background 必须是对象");
  const pattern = b.pattern ?? "grid";
  const paper = b.paper ?? "#ffffff";
  if (!PATTERNS.includes(pattern)) fail(`background.pattern 不合法：${pattern}`);
  if (!COLOR.test(paper)) fail(`background.paper 不合法：${paper}`);
  return { pattern, paper };
}

// DefaultPolicy.allow_src 的规则。真正的规则由服务端的 Policy 决定、可能被覆盖，
// 所以替身只提醒，不拒绝。
function defaultAllowSrc(src) {
  return src.startsWith("/") && !src.startsWith("//") && !src.includes("..") && !src.includes("\\") && !src.includes(":");
}

function normalizeLayers(list) {
  if (list == null) return [];
  if (!Array.isArray(list)) fail("layers 必须是数组");
  if (list.length > MAX_LAYERS) fail(`layers 最多 ${MAX_LAYERS} 项`);
  return list.map((l, i) => {
    if (!isObj(l)) fail(`layers[${i}] 必须是对象`);
    if (typeof l.src !== "string" || !l.src) fail(`layers[${i}].src 必须是非空字符串`);
    if (!defaultAllowSrc(l.src)) console.warn(`[inksync-stub] layers[${i}].src 通不过 DefaultPolicy.allow_src：${l.src}`);
    for (const k of ["x", "y"]) {
      if (typeof l[k] !== "number" || !Number.isFinite(l[k])) fail(`layers[${i}].${k} 必须是数`);
    }
    if (typeof l.width !== "number" || !(l.width > 0) || !Number.isFinite(l.width)) fail(`layers[${i}].width 必须是正数`);
    const out = { src: l.src, x: l.x, y: l.y, width: l.width };
    if (l.height != null) {
      if (typeof l.height !== "number" || !(l.height > 0) || !Number.isFinite(l.height)) fail(`layers[${i}].height 必须是正数`);
      out.height = l.height;
    }
    if (l.z != null) {
      if (l.z !== "below" && l.z !== "above") fail(`layers[${i}].z 必须是 below 或 above`);
      out.z = l.z;
    }
    if (l.sheet != null) out.sheet = !!l.sheet;
    return out;
  });
}

function normalizeData(d) {
  if (d == null) return {};
  if (!isObj(d)) fail("data 必须是 JSON 对象");
  const text = JSON.stringify(d);
  if (new TextEncoder().encode(text).length > MAX_DATA_BYTES) fail("data 序列化后超过 16 KB");
  return JSON.parse(text);
}

/** 由 create（或存储、initial 中的 meta）生成完整的元数据。 */
function buildMeta(id, spec, keepTimes = false) {
  if (!isObj(spec)) fail("create 必须是对象");
  const t = nowSec();
  return {
    id,
    name: normalizeName(spec.name ?? ""),
    created: keepTimes && typeof spec.created === "number" ? spec.created : t,
    updated: keepTimes && typeof spec.updated === "number" ? spec.updated : t,
    canvas: normalizeCanvas(spec.canvas),
    background: normalizeBackground(spec.background),
    layers: normalizeLayers(spec.layers),
    data: normalizeData(spec.data),
  };
}

function normalizeTool(t) {
  if (!isObj(t)) fail("tool 必须是对象");
  if (!TOOLS.includes(t.tool)) fail(`tool.tool 不合法：${t.tool}`);
  if (!COLOR.test(t.color)) fail(`tool.color 不合法：${t.color}`);
  if (typeof t.width !== "number" || !Number.isFinite(t.width)) fail("tool.width 必须是数");
  if (t.eraserMode !== "object" && t.eraserMode !== "pixel") fail(`tool.eraserMode 不合法：${t.eraserMode}`);
  return { tool: t.tool, color: t.color, width: clamp(t.width, 0.5, 96), eraserMode: t.eraserMode };
}

/** 读入的笔画（5.3 节）。不合格的丢弃并提醒。 */
function normalizeStrokes(list) {
  if (list == null) return [];
  if (!Array.isArray(list)) fail("strokes 必须是数组");
  const out = [];
  for (const s of list) {
    const ok =
      isObj(s) && typeof s.id === "string" && INK_TOOLS.includes(s.tool) && COLOR.test(s.color) &&
      typeof s.w === "number" && s.w >= 0.5 && s.w <= 96 && typeof s.n === "number" &&
      Array.isArray(s.p) && s.p.length >= 3 && s.p.length % 3 === 0 && s.p.length / 3 <= MAX_POINTS &&
      s.p.every((v) => typeof v === "number" && Number.isFinite(v));
    if (ok) out.push(clone(s));
    else console.warn("[inksync-stub] 丢弃一条不合格的笔画", s);
  }
  return out.sort((a, b) => a.n - b.n);
}

// ------------------------------------------------------------------ 笔画几何

// 压感到半径的曲线，取自白板项目 stroke.js（strokeRadius / penForce）：
// iPad Safari 的压感读数挤在 0.007～0.125，先按膝点展开再算粗细。
// 钢笔跟随压感，马克笔和荧光笔等宽。
const PEN_KNEE = 0.05;
const PEN_FLOOR = 0.2;
const PEN_GAMMA = 1.2;

function radiusAt(tool, w, pressure) {
  const half = Math.max(0.3, w / 2);
  if (tool !== "pen") return half;
  const p = clamp(pressure, 0, 1);
  const force = (p * (1 + PEN_KNEE)) / (p + PEN_KNEE);
  return half * (PEN_FLOOR + (1 - PEN_FLOOR) * Math.pow(force, PEN_GAMMA));
}

// 几何缓存放在 WeakMap 里，笔画对象本身保持 5.3 节的纯数据，snapshot 直接复制。
const pathCache = new WeakMap();
const boxCache = new WeakMap();

/**
 * 笔画的可填充路径：每个点一个圆，相邻两圆之间补上外公切线围成的梯形。
 * 所有子路径同向绕行，nonzero 填充的结果就是它们的并集，一次 fill 画完——
 * 半透明的荧光笔在自身重叠处不会变深。
 */
function strokePath(s, cache = true) {
  if (cache && pathCache.has(s)) return pathCache.get(s);
  const path = new Path2D();
  const p = s.p;
  let px = 0, py = 0, pr = 0;
  for (let i = 0; i + 2 < p.length; i += 3) {
    const x = p[i], y = p[i + 1], r = radiusAt(s.tool, s.w, p[i + 2]);
    path.moveTo(x + r, y);
    path.arc(x, y, r, 0, TAU);
    if (i > 0) hull(path, px, py, pr, x, y, r);
    px = x; py = y; pr = r;
  }
  if (cache) pathCache.set(s, path);
  return path;
}

function hull(path, x1, y1, r1, x2, y2, r2) {
  const dx = x2 - x1, dy = y2 - y1;
  const d = Math.hypot(dx, dy);
  if (d <= Math.abs(r1 - r2) + 1e-9) return; // 一个圆包含另一个
  const base = Math.atan2(dy, dx);
  const a = Math.acos((r1 - r2) / d);
  const pts = [
    [x1 + r1 * Math.cos(base + a), y1 + r1 * Math.sin(base + a)],
    [x2 + r2 * Math.cos(base + a), y2 + r2 * Math.sin(base + a)],
    [x2 + r2 * Math.cos(base - a), y2 + r2 * Math.sin(base - a)],
    [x1 + r1 * Math.cos(base - a), y1 + r1 * Math.sin(base - a)],
  ];
  // 和 arc(…, 0, TAU) 同向（鞋带公式为正）
  let area = 0;
  for (let i = 0; i < 4; i++) {
    const [ax, ay] = pts[i], [bx, by] = pts[(i + 1) % 4];
    area += ax * by - bx * ay;
  }
  if (area < 0) pts.reverse();
  path.moveTo(pts[0][0], pts[0][1]);
  for (let i = 1; i < 4; i++) path.lineTo(pts[i][0], pts[i][1]);
  path.closePath();
}

/** 外框（含半径），r 为最大半径，擦除命中判定用。 */
function strokeBox(s) {
  if (boxCache.has(s)) return boxCache.get(s);
  const p = s.p;
  let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity, r = 0;
  for (let i = 0; i + 2 < p.length; i += 3) {
    x0 = Math.min(x0, p[i]); x1 = Math.max(x1, p[i]);
    y0 = Math.min(y0, p[i + 1]); y1 = Math.max(y1, p[i + 1]);
    r = Math.max(r, radiusAt(s.tool, s.w, p[i + 2]));
  }
  const box = { x0: x0 - r, y0: y0 - r, x1: x1 + r, y1: y1 + r, r };
  boxCache.set(s, box);
  return box;
}

function drawStroke(ctx, s, cache = true) {
  ctx.globalAlpha = s.tool === "highlighter" ? HIGHLIGHTER_ALPHA : 1;
  ctx.fillStyle = s.color;
  ctx.fill(strokePath(s, cache));
  ctx.globalAlpha = 1;
}

function segDist(px, py, ax, ay, bx, by) {
  const dx = bx - ax, dy = by - ay;
  const len = dx * dx + dy * dy;
  const t = len > 0 ? clamp(((px - ax) * dx + (py - ay) * dy) / len, 0, 1) : 0;
  return Math.hypot(px - (ax + dx * t), py - (ay + dy * t));
}

/** 橡皮（圆心 x,y，半径 r）是否碰到这条笔画。 */
function strokeHit(s, x, y, r) {
  const b = strokeBox(s);
  if (x < b.x0 - r || x > b.x1 + r || y < b.y0 - r || y > b.y1 + r) return false;
  const p = s.p;
  const reach = r + b.r;
  if (p.length === 3) return Math.hypot(p[0] - x, p[1] - y) <= reach;
  for (let i = 0; i + 5 < p.length; i += 3) {
    if (segDist(x, y, p[i], p[i + 1], p[i + 3], p[i + 4]) <= reach) return true;
  }
  return false;
}

function unionBox(a, b) {
  if (!a) return b ? { ...b } : null;
  if (!b) return { ...a };
  return { x0: Math.min(a.x0, b.x0), y0: Math.min(a.y0, b.y0), x1: Math.max(a.x1, b.x1), y1: Math.max(a.y1, b.y1) };
}

/** 背景图案，画在屏幕坐标里；ox/oy 是白板原点在屏幕上的位置。取自白板项目 renderer.js。 */
function drawPattern(ctx, kind, scale, ox, oy, rect) {
  let step = GRID_STEP * scale;
  if (kind === "blank" || step <= 0) return;
  while (step < MIN_PATTERN_PX) step *= 2;
  const { x0, y0, x1, y1 } = rect;
  const sx = x0 + ((((ox - x0) % step) + step) % step);
  const sy = y0 + ((((oy - y0) % step) + step) % step);
  ctx.save();
  ctx.strokeStyle = LINE;
  ctx.fillStyle = LINE;
  ctx.lineWidth = Math.max(0.5, Math.min(1, scale));
  ctx.beginPath();
  if (kind === "dots") {
    const r = Math.max(0.8, Math.min(1.8, 1.2 * scale));
    for (let x = sx; x <= x1; x += step) {
      for (let y = sy; y <= y1; y += step) {
        ctx.moveTo(x + r, y);
        ctx.arc(x, y, r, 0, TAU);
      }
    }
    ctx.fill();
  } else {
    if (kind === "grid") {
      for (let x = sx; x <= x1; x += step) {
        ctx.moveTo(Math.round(x) + 0.5, y0);
        ctx.lineTo(Math.round(x) + 0.5, y1);
      }
    }
    for (let y = sy; y <= y1; y += step) {
      ctx.moveTo(x0, Math.round(y) + 0.5);
      ctx.lineTo(x1, Math.round(y) + 0.5);
    }
    ctx.stroke();
  }
  ctx.restore();
}

/** src 中的 {w} 换成不小于所需像素宽度的最小档位（都不够时取最大档）。 */
function resolveSrc(src, pixels) {
  if (!src.includes("{w}")) return src;
  const w = BUCKETS.find((b) => b >= pixels) ?? BUCKETS[BUCKETS.length - 1];
  return src.replaceAll("{w}", String(w));
}

// ------------------------------------------------------------------ 手写板

class InkPad {
  #root;
  #base;
  #live;
  #ro;
  #prefix;
  #readonly;
  #defaultReadonly;
  #fingerDraw;
  #undoLimit;
  #tool;
  #initial;
  #meta = null;
  #strokes = [];
  #undo = [];
  #redo = [];
  #caps;
  #listeners = new Map();
  #lastHistory = null;
  #view = { scale: 1, x: 0, y: 0 };
  #views = new Map(); // 白板 id -> 离开时的视图，切回来时恢复
  #needView = false; // 容器还没有尺寸，初始视图等第一次 resize 再定
  #size = { w: 0, h: 0, dpr: 1 };
  #frame = 0;
  #dirtyBase = false;
  #gesture = null; // {kind: "ink"|"erase"|"pan"|"pinch", touch, id, …}
  #touches = new Map(); // 触摸点 id -> 屏幕坐标
  #images = new Map(); // 解析后的 url -> {img, ok, failed, promise}
  #lastImage = new Map(); // 图层 src 模板 -> 最近一张载入成功的图（换档时先画旧图，不闪）
  #idPrefix = `${uid(12)}-${uid(4)}`;
  #seq = 0;
  #destroyed = false;

  constructor(container, options) {
    if (!(container instanceof Element)) throw new TypeError("container 必须是 DOM 元素");
    if (!isObj(options)) throw new TypeError("options 必须是对象");
    const { board } = options;
    if (typeof board !== "string" || !BOARD_ID.test(board)) throw new TypeError(`board 不合法：${board}`);
    const space = options.space ?? "";
    if (typeof space !== "string" || !SPACE_NAME.test(space)) throw new TypeError(`space 不合法：${space}`);
    // 约定写的默认值是 "inksync:<space>"；空间非空时这里多加一个冒号，避免和白板 id 连在一起产生歧义
    this.#prefix = typeof options.storage === "string" ? options.storage : `inksync:${space ? space + ":" : ""}`;
    this.#defaultReadonly = !!options.readonly;
    this.#readonly = this.#defaultReadonly;
    this.#fingerDraw = !!options.fingerDraw;
    this.#undoLimit = Number.isFinite(options.undoLimit) ? Math.max(0, Math.floor(options.undoLimit)) : 200;
    this.#tool = normalizeTool({ ...DEFAULT_TOOL, ...(options.tool || {}) });
    this.#initial = options.initial || null;
    this.#caps = this.#capsFor(this.#readonly);

    // DOM：一块铺满容器的区域，底层画背景、图片层和已提交的笔画，上层画正在写的一笔
    const root = document.createElement("div");
    root.className = "inksync-pad";
    Object.assign(root.style, {
      position: "relative", width: "100%", height: "100%", overflow: "hidden",
      touchAction: "none", userSelect: "none", webkitUserSelect: "none", webkitTouchCallout: "none",
      cursor: "crosshair",
    });
    this.#base = document.createElement("canvas");
    this.#live = document.createElement("canvas");
    for (const c of [this.#base, this.#live]) {
      Object.assign(c.style, { position: "absolute", left: "0", top: "0", width: "100%", height: "100%", display: "block" });
    }
    this.#live.style.pointerEvents = "none";
    root.append(this.#base, this.#live);
    container.appendChild(root);
    this.#root = root;

    // 只在手写板自身的区域里监听、拦截；页面其他位置不受影响
    root.addEventListener("pointerdown", this.#onDown);
    root.addEventListener("pointermove", this.#onMove);
    root.addEventListener("pointerup", this.#onUp);
    root.addEventListener("pointercancel", this.#onUp);
    root.addEventListener("wheel", this.#onWheel, { passive: false });
    root.addEventListener("contextmenu", (e) => e.preventDefault());
    this.#ro = new ResizeObserver(() => this.#resize());
    this.#ro.observe(root);
    this.#resize();

    // 载入推迟到微任务：宿主在 createInkPad 返回后同步调用 on() 也能收到第一批事件
    queueMicrotask(() => {
      if (this.#destroyed) return;
      this.#emit("status", "local");
      this.#open(board, { create: options.create, readonly: options.readonly }, true).catch(() => {});
    });
  }

  // ---------------------------------------------------------------- 只读属性

  get board() { return clone(this.#meta) ?? null; }
  get status() { return "local"; }
  get tool() { return { ...this.#tool }; }
  get caps() { return { ...this.#caps }; }
  get locked() { return null; }
  get shell() { return { active: false, version: "", bridge: false }; }
  get version() { return VERSION; }
  get info() { return {}; }

  // ---------------------------------------------------------------- 方法

  open(board, { create, readonly } = {}) {
    if (this.#destroyed) return Promise.reject(new Error("手写板已销毁"));
    return this.#open(board, { create, readonly }, false);
  }

  setTool(tool) {
    this.#tool = normalizeTool({ ...this.#tool, ...tool });
  }

  undo() {
    const action = this.#undo.pop();
    if (!action || !this.#meta) return;
    this.#redo.push(action);
    this.#apply(action, true);
  }

  redo() {
    const action = this.#redo.pop();
    if (!action || !this.#meta) return;
    this.#undo.push(action);
    this.#apply(action, false);
  }

  clear() {
    if (!this.#meta || !this.#caps.clear || !this.#strokes.length) return;
    this.#cancelInk();
    const removed = this.#strokes;
    this.#strokes = [];
    this.#record({ type: "remove", strokes: removed, clear: true });
    this.#commit({ op: "clear" });
  }

  fit() {
    const m = this.#meta;
    const { w, h } = this.#size;
    if (!m) return;
    if (!w || !h) {
      this.#needView = true;
      return;
    }
    const c = m.canvas;
    const v = this.#view;
    if (c.mode === "fixed") {
      v.scale = clamp(Math.min(w / c.width, h / c.height), MIN_SCALE, MAX_SCALE);
      v.x = (w - c.width * v.scale) / 2;
      v.y = (h - c.height * v.scale) / 2;
    } else if (c.mode === "column") {
      v.scale = clamp(w / c.width, MIN_SCALE, MAX_SCALE);
      v.x = 0;
      v.y = 0;
    } else {
      const box = this.#inkBounds();
      if (!box) {
        Object.assign(v, { scale: 1, x: 0, y: 0 });
      } else {
        const pad = 24;
        const bw = Math.max(1, box.x1 - box.x0), bh = Math.max(1, box.y1 - box.y0);
        // 最大放到 1:1，免得一个点被放大满屏
        v.scale = clamp(Math.min((w - 2 * pad) / bw, (h - 2 * pad) / bh, 1), MIN_SCALE, MAX_SCALE);
        v.x = w / 2 - ((box.x0 + box.x1) / 2) * v.scale;
        v.y = h / 2 - ((box.y0 + box.y1) / 2) * v.scale;
      }
    }
    this.#clampView();
    this.#requestRender();
  }

  zoom(factor) {
    if (!(factor > 0)) return;
    this.#zoomAt(this.#size.w / 2, this.#size.h / 2, factor);
  }

  setMeta(patch) {
    const m = this.#meta;
    if (!m) throw new Error("没有打开的白板");
    if (!this.#caps.meta) {
      console.warn("[inksync-stub] setMeta 需要 caps.meta，已忽略");
      return;
    }
    if (!isObj(patch)) fail("patch 必须是对象");
    const next = { ...m };
    for (const key of Object.keys(patch)) {
      const value = patch[key];
      if (key === "name") next.name = normalizeName(value);
      else if (key === "background") next.background = normalizeBackground(value); // 整体替换
      else if (key === "layers") next.layers = normalizeLayers(value); // 整体替换
      else if (key === "data") {
        // 按键合并：出现的键替换，null 删除，未出现的不变
        if (!isObj(value)) fail("data 必须是对象");
        const data = { ...m.data };
        for (const [k, v] of Object.entries(value)) {
          if (v === null) delete data[k];
          else data[k] = v;
        }
        next.data = normalizeData(data);
      } else fail(`${key} 不能修改（只能修改 name、background、layers、data）`);
    }
    next.updated = nowSec();
    this.#meta = next;
    this.#save();
    this.#emit("meta", clone(next));
    this.#emit("op", { board: next.id, op: { op: "meta", meta: clone(patch) } });
    this.#requestRender();
  }

  /**
   * 导出 PNG。范围：
   *   - fixed：整个画布；
   *   - column 且 layers 为 true：x 为 0 到画布宽，y 从 0 到图片层与笔迹的最下边。
   *     约定只写了「其他为笔迹外框加边距」，没有说 column 带图片层时怎么取，这里按
   *     「整页宽、从页首到内容末尾」处理，这样题图总是完整的；
   *   - 其他：笔迹外框（layers 为 true 时并上图片层）加 32 的边距。空白板导出边距大小的空白。
   * 结果过大时自动降低 scale，保证边长不超过 16384、像素数不超过 6400 万。
   */
  async exportPNG({ layers = false, scale = 1 } = {}) {
    if (!this.#meta) throw new Error("没有打开的白板");
    if (!(scale > 0) || !Number.isFinite(scale)) fail("scale 必须是正数");
    if (layers) await this.#preloadLayers(scale);
    const area = this.#exportArea(layers);
    const aw = Math.max(1, area.x1 - area.x0);
    const ah = Math.max(1, area.y1 - area.y0);
    const s = Math.min(scale, EXPORT_MAX_SIDE / aw, EXPORT_MAX_SIDE / ah, Math.sqrt(EXPORT_MAX_PIXELS / (aw * ah)));
    if (s < scale) await (layers ? this.#preloadLayers(s) : null);
    const canvas = document.createElement("canvas");
    canvas.width = Math.max(1, Math.ceil(aw * s));
    canvas.height = Math.max(1, Math.ceil(ah * s));
    const view = { scale: s, x: -area.x0 * s, y: -area.y0 * s };
    this.#paint(canvas.getContext("2d"), view, canvas.width, canvas.height, 1, { layers, exporting: true });
    return canvas.toDataURL("image/png");
  }

  snapshot() {
    return { meta: clone(this.#meta) ?? null, strokes: clone(this.#strokes) };
  }

  load({ meta, strokes } = {}) {
    if (this.#destroyed) return;
    const id = this.#meta?.id ?? meta?.id;
    if (typeof id !== "string" || !BOARD_ID.test(id)) fail(`board 不合法：${id}`);
    // 替换当前白板的内容；meta.id 与当前白板不同时以当前白板为准
    const next = buildMeta(id, meta || {}, true);
    const list = normalizeStrokes(strokes);
    const sameCanvas = this.#meta && JSON.stringify(this.#meta.canvas) === JSON.stringify(next.canvas);
    this.#switchTo(next, list, this.#readonly);
    if (!sameCanvas) this.#initialView();
    this.#save();
  }

  on(event, listener) {
    if (typeof listener !== "function") throw new TypeError("listener 必须是函数");
    if (!EVENTS.includes(event)) console.warn(`[inksync-stub] 未知事件：${event}`);
    if (!this.#listeners.has(event)) this.#listeners.set(event, new Set());
    this.#listeners.get(event).add(listener);
    return () => this.#listeners.get(event)?.delete(listener);
  }

  destroy() {
    if (this.#destroyed) return;
    this.#cancelInk();
    this.#save();
    this.#destroyed = true;
    if (this.#frame) cancelAnimationFrame(this.#frame);
    this.#ro.disconnect();
    this.#root.remove();
    this.#listeners.clear();
  }

  // ---------------------------------------------------------------- 事件

  #emit(event, detail) {
    for (const fn of this.#listeners.get(event) || []) {
      try {
        fn(detail);
      } catch (err) {
        console.error(`[inksync-stub] ${event} 事件的处理出错`, err);
      }
    }
  }

  #emitHistory() {
    const h = { undo: this.#undo.length > 0, redo: this.#redo.length > 0 };
    const last = this.#lastHistory;
    if (last && last.undo === h.undo && last.redo === h.redo) return;
    this.#lastHistory = h;
    this.#emit("history", { ...h });
  }

  #capsFor(readonly) {
    return { write: !readonly, clear: !readonly, meta: !readonly, unlock: false };
  }

  // ---------------------------------------------------------------- 打开白板

  /** 内容依次取自 initial（只用于构造时的第一块白板）、本地存储、create 新建。 */
  #open(id, { create, readonly }, first) {
    if (typeof id !== "string" || !BOARD_ID.test(id)) return this.#fail("board", `白板 id 不合法：${id}`);
    let meta = null;
    let strokes = [];
    let fresh = false;
    const initial = first ? this.#initial : null;
    if (initial) {
      try {
        meta = buildMeta(id, { ...(isObj(create) ? create : {}), ...(initial.meta || {}) }, true);
        strokes = normalizeStrokes(initial.strokes);
        fresh = true;
      } catch (err) {
        console.warn("[inksync-stub] initial 不合法，已忽略：", err.message);
        meta = null;
      }
    }
    if (!meta) {
      const stored = this.#readStored(id);
      if (stored) {
        try {
          meta = buildMeta(id, stored.meta || {}, true);
          strokes = normalizeStrokes(stored.strokes);
        } catch (err) {
          console.warn("[inksync-stub] 本地存储中的白板已损坏，已忽略：", id, err.message);
          meta = null;
        }
      }
    }
    if (!meta) {
      if (create == null) return this.#fail("board", `白板不存在：${id}`);
      try {
        meta = buildMeta(id, create);
      } catch (err) {
        return this.#fail("create", err.message);
      }
      fresh = true;
    }
    this.#switchTo(meta, strokes, readonly ?? this.#defaultReadonly);
    if (fresh) this.#save();
    return Promise.resolve(clone(meta));
  }

  #fail(reason, detail) {
    this.#emit("error", { reason, detail });
    const err = new Error(detail);
    err.reason = reason;
    return Promise.reject(err);
  }

  /** 换上一块白板（或新内容）：撤销记录清空，视图恢复或重置，发出事件。 */
  #switchTo(meta, strokes, readonly) {
    this.#cancelInk();
    this.#gesture = null;
    const prev = this.#meta;
    if (prev) {
      this.#save();
      this.#views.set(prev.id, { ...this.#view });
    }
    this.#meta = meta;
    this.#strokes = strokes;
    this.#undo = [];
    this.#redo = [];
    this.#readonly = !!readonly;
    const caps = this.#capsFor(this.#readonly);
    const capsChanged = JSON.stringify(caps) !== JSON.stringify(this.#caps);
    this.#caps = caps;
    const saved = prev?.id !== meta.id ? this.#views.get(meta.id) : null;
    if (saved) Object.assign(this.#view, saved);
    else if (prev?.id !== meta.id) this.#initialView();
    this.#emit("meta", clone(meta));
    if (capsChanged) this.#emit("caps", { ...caps });
    this.#emit("change", { board: meta.id });
    this.#emitHistory();
    this.#requestRender();
  }

  /** 首次打开：column / fixed 宽度铺满容器、从顶部开始；infinite 原点在左上角、1:1。 */
  #initialView() {
    const m = this.#meta;
    const { w, h } = this.#size;
    if (!m) return;
    if (!w || !h) {
      this.#needView = true;
      return;
    }
    this.#needView = false;
    const v = this.#view;
    if (m.canvas.mode === "infinite") Object.assign(v, { scale: 1, x: 0, y: 0 });
    else Object.assign(v, { scale: clamp(w / m.canvas.width, MIN_SCALE, MAX_SCALE), x: 0, y: 0 });
    this.#clampView();
    this.#requestRender();
  }

  // ---------------------------------------------------------------- 存储

  #readStored(id) {
    try {
      const raw = localStorage.getItem(this.#prefix + id);
      return raw ? JSON.parse(raw) : null;
    } catch (err) {
      console.warn("[inksync-stub] 读取本地存储失败", err);
      return null;
    }
  }

  #save() {
    if (!this.#meta) return;
    try {
      localStorage.setItem(this.#prefix + this.#meta.id, JSON.stringify({ meta: this.#meta, strokes: this.#strokes }));
    } catch (err) {
      console.warn("[inksync-stub] 写入本地存储失败", err);
    }
  }

  // ---------------------------------------------------------------- 操作与撤销

  #record(action) {
    this.#undo.push(action);
    if (this.#undo.length > this.#undoLimit) this.#undo.shift();
    this.#redo = [];
  }

  /** 一个操作已作用到本地内容：更新时间、写回存储、通知宿主。 */
  #commit(op) {
    const m = this.#meta;
    m.updated = nowSec();
    this.#save();
    this.#emit("op", { board: m.id, op: clone(op) });
    this.#emit("change", { board: m.id });
    this.#emitHistory();
    this.#requestRender();
  }

  /** 执行（reverse 为 false）或撤销（true）一条撤销记录。 */
  #apply(action, reverse) {
    const bringBack = (action.type === "add") === !reverse;
    if (bringBack) {
      this.#strokes.push(...action.strokes);
      this.#strokes.sort((a, b) => a.n - b.n);
      this.#commit({ op: "restore", strokes: action.strokes });
    } else {
      const ids = new Set(action.strokes.map((s) => s.id));
      this.#strokes = this.#strokes.filter((s) => !ids.has(s.id));
      this.#commit(action.clear ? { op: "clear" } : { op: "remove", ids: [...ids] });
    }
  }

  #nextN() {
    let n = 0;
    for (const s of this.#strokes) n = Math.max(n, s.n + 1);
    return n;
  }

  // ---------------------------------------------------------------- 坐标与范围

  #screen(e) {
    const r = this.#root.getBoundingClientRect();
    return [e.clientX - r.left, e.clientY - r.top];
  }

  #toWorld(sx, sy) {
    const v = this.#view;
    return [(sx - v.x) / v.scale, (sy - v.y) / v.scale];
  }

  /** 5.1 节的可书写范围。 */
  #writable(x, y) {
    const c = this.#meta.canvas;
    if (c.mode === "infinite") return true;
    if (x < 0 || x > c.width || y < 0) return false;
    return c.mode !== "fixed" || y <= c.height;
  }

  /** 越界的点截断到可书写范围的边上。 */
  #clampPoint(x, y) {
    const c = this.#meta.canvas;
    if (c.mode === "infinite") return [x, y];
    return [clamp(x, 0, c.width), c.mode === "fixed" ? clamp(y, 0, c.height) : Math.max(0, y)];
  }

  #inkBounds() {
    let box = null;
    for (const s of this.#strokes) box = unionBox(box, strokeBox(s));
    return box;
  }

  /** 图片层在白板坐标里的矩形；height 省略且图片尚未载入时为 null。 */
  #layerRect(layer) {
    let h = layer.height;
    if (h == null) {
      const img = this.#lastImage.get(layer.src);
      if (!img || !img.naturalWidth) return null;
      h = (layer.width * img.naturalHeight) / img.naturalWidth;
    }
    return { x0: layer.x, y0: layer.y, x1: layer.x + layer.width, y1: layer.y + h };
  }

  #layerBounds() {
    let box = null;
    for (const l of this.#meta.layers) box = unionBox(box, this.#layerRect(l));
    return box;
  }

  #exportArea(layers) {
    const c = this.#meta.canvas;
    const M = EXPORT_MARGIN;
    if (c.mode === "fixed") return { x0: 0, y0: 0, x1: c.width, y1: c.height };
    const ink = this.#inkBounds();
    if (c.mode === "column" && layers) {
      const bottom = Math.max(ink?.y1 ?? 0, this.#layerBounds()?.y1 ?? 0);
      return { x0: 0, y0: 0, x1: c.width, y1: bottom > 0 ? bottom : 2 * M };
    }
    const box = layers ? unionBox(ink, this.#layerBounds()) : ink;
    if (!box) return { x0: 0, y0: 0, x1: 2 * M, y1: 2 * M };
    return { x0: box.x0 - M, y0: box.y0 - M, x1: box.x1 + M, y1: box.y1 + M };
  }

  // ---------------------------------------------------------------- 视图

  #zoomAt(sx, sy, factor) {
    const v = this.#view;
    const next = clamp(v.scale * factor, MIN_SCALE, MAX_SCALE);
    const [wx, wy] = this.#toWorld(sx, sy);
    v.scale = next;
    v.x = sx - wx * next;
    v.y = sy - wy * next;
    this.#clampView();
    this.#requestRender();
  }

  /** column / fixed：纸比视口宽（高）时不露出纸外，窄（矮）时不离开视口。infinite 不限制。 */
  #clampView() {
    const m = this.#meta;
    if (!m || m.canvas.mode === "infinite") return;
    const { w, h } = this.#size;
    const v = this.#view;
    const pw = m.canvas.width * v.scale;
    let ph;
    if (m.canvas.mode === "fixed") ph = m.canvas.height * v.scale;
    else {
      // column 向下无限：能滚到内容末尾再往下半屏
      const bottom = Math.max(this.#inkBounds()?.y1 ?? 0, this.#layerBounds()?.y1 ?? 0);
      ph = Math.max(bottom * v.scale + h / 2, h);
    }
    v.x = clamp(v.x, Math.min(w - pw, 0), Math.max(w - pw, 0));
    v.y = clamp(v.y, Math.min(h - ph, 0), Math.max(h - ph, 0));
  }

  #resize() {
    if (this.#destroyed) return;
    const w = this.#root.clientWidth;
    const h = this.#root.clientHeight;
    const dpr = Math.min(window.devicePixelRatio || 1, 3);
    const old = this.#size;
    if (old.w === w && old.h === h && old.dpr === dpr) return;
    const m = this.#meta;
    // 宽度铺满的 column / fixed 画布在容器变宽变窄后继续铺满
    if (m && m.canvas.mode !== "infinite" && old.w > 0) {
      const v = this.#view;
      if (Math.abs(v.scale - old.w / m.canvas.width) < 1e-6 && Math.abs(v.x) < 0.5) {
        v.y *= w / old.w;
        v.scale = clamp(w / m.canvas.width, MIN_SCALE, MAX_SCALE);
      }
    }
    this.#size = { w, h, dpr };
    for (const c of [this.#base, this.#live]) {
      c.width = Math.max(1, Math.round(w * dpr));
      c.height = Math.max(1, Math.round(h * dpr));
    }
    if (this.#needView) this.#initialView();
    this.#clampView();
    this.#dirtyBase = true;
    this.#render();
  }

  // ---------------------------------------------------------------- 绘制

  #requestRender(base = true) {
    if (base) this.#dirtyBase = true;
    if (this.#frame || this.#destroyed) return;
    this.#frame = requestAnimationFrame(() => {
      this.#frame = 0;
      this.#render();
    });
  }

  #render() {
    if (this.#destroyed) return;
    const dpr = Math.min(window.devicePixelRatio || 1, 3);
    if (dpr !== this.#size.dpr) return this.#resize(); // 移到另一块屏幕
    const { w, h } = this.#size;
    if (this.#dirtyBase) {
      this.#dirtyBase = false;
      const ctx = this.#base.getContext("2d");
      ctx.setTransform(1, 0, 0, 1, 0, 0);
      ctx.clearRect(0, 0, this.#base.width, this.#base.height);
      if (this.#meta) this.#paint(ctx, this.#view, w, h, dpr, { layers: true, exporting: false });
      else {
        ctx.fillStyle = OUTSIDE;
        ctx.fillRect(0, 0, this.#base.width, this.#base.height);
      }
    }
    // 正在写的一笔每次整条重画（不缓存路径）
    const lctx = this.#live.getContext("2d");
    lctx.setTransform(1, 0, 0, 1, 0, 0);
    lctx.clearRect(0, 0, this.#live.width, this.#live.height);
    const g = this.#gesture;
    if (g && g.kind === "ink") {
      const v = this.#view;
      lctx.setTransform(v.scale * dpr, 0, 0, v.scale * dpr, v.x * dpr, v.y * dpr);
      drawStroke(lctx, g.stroke, false);
    }
  }

  /**
   * 画一帧：纸外底色、纸、背景图案、下方图片层、笔画、上方图片层。
   * 显示和导出共用；导出时（exporting）整张都是纸色、不画阴影。
   */
  #paint(ctx, v, w, h, dpr, { layers, exporting }) {
    const m = this.#meta;
    const c = m.canvas;
    const bg = m.background;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    let paper;
    if (c.mode === "infinite" || exporting) {
      paper = { x0: 0, y0: 0, x1: w, y1: h };
      ctx.fillStyle = bg.paper;
      ctx.fillRect(0, 0, w, h);
    } else {
      ctx.fillStyle = OUTSIDE;
      ctx.fillRect(0, 0, w, h);
      const top = v.y;
      const bottom = c.mode === "fixed" ? v.y + c.height * v.scale : h + 1;
      paper = { x0: v.x, y0: top, x1: v.x + c.width * v.scale, y1: bottom };
      if (bottom > top) {
        ctx.save();
        ctx.shadowColor = SHADOW;
        ctx.shadowBlur = SHADOW_BLUR * dpr;
        ctx.shadowOffsetY = SHADOW_LIFT * dpr;
        ctx.fillStyle = bg.paper;
        ctx.fillRect(paper.x0, paper.y0, paper.x1 - paper.x0, paper.y1 - paper.y0);
        ctx.restore();
      }
    }
    // 有 sheet 图片层时整块白板不画背景图案（约定 5.1 节）
    const sheet = layers && m.layers.some((l) => l.sheet);
    if (!sheet && bg.pattern !== "blank") {
      const rect = { x0: Math.max(0, paper.x0), y0: Math.max(0, paper.y0), x1: Math.min(w, paper.x1), y1: Math.min(h, paper.y1) };
      if (rect.x1 > rect.x0 && rect.y1 > rect.y0) {
        ctx.save();
        ctx.beginPath();
        ctx.rect(rect.x0, rect.y0, rect.x1 - rect.x0, rect.y1 - rect.y0);
        ctx.clip();
        drawPattern(ctx, bg.pattern, v.scale, v.x, v.y, rect);
        ctx.restore();
      }
    }
    ctx.setTransform(v.scale * dpr, 0, 0, v.scale * dpr, v.x * dpr, v.y * dpr);
    const pixels = v.scale * dpr; // 每个白板单位对应的设备像素
    if (layers) this.#paintLayers(ctx, "below", pixels, dpr, bg.paper);
    // 只画视口里的笔画
    const vx0 = -v.x / v.scale, vy0 = -v.y / v.scale;
    const vx1 = vx0 + w / v.scale, vy1 = vy0 + h / v.scale;
    for (const s of this.#strokes) {
      const b = strokeBox(s);
      if (b.x1 < vx0 || b.x0 > vx1 || b.y1 < vy0 || b.y0 > vy1) continue;
      drawStroke(ctx, s);
    }
    if (layers) this.#paintLayers(ctx, "above", pixels, dpr, bg.paper);
  }

  #paintLayers(ctx, z, pixels, dpr, paperColor) {
    ctx.imageSmoothingEnabled = true;
    ctx.imageSmoothingQuality = "high";
    for (const layer of this.#meta.layers) {
      if ((layer.z || "below") !== z) continue;
      const img = this.#layerImage(layer, layer.width * pixels);
      const r = this.#layerRect(layer);
      if (!r) continue;
      if (layer.sheet) {
        ctx.save();
        ctx.shadowColor = SHADOW;
        ctx.shadowBlur = SHADOW_BLUR * dpr;
        ctx.shadowOffsetY = SHADOW_LIFT * dpr;
        ctx.fillStyle = paperColor;
        ctx.fillRect(r.x0, r.y0, r.x1 - r.x0, r.y1 - r.y0);
        ctx.restore();
      }
      if (img) ctx.drawImage(img, r.x0, r.y0, r.x1 - r.x0, r.y1 - r.y0);
    }
  }

  #loadImage(url) {
    let entry = this.#images.get(url);
    if (entry) return entry;
    const img = new Image();
    entry = { img, ok: false, failed: false };
    entry.promise = new Promise((resolve) => {
      img.onload = () => {
        entry.ok = true;
        resolve(entry);
        this.#requestRender();
      };
      img.onerror = () => {
        entry.failed = true;
        console.warn("[inksync-stub] 图片载入失败：", url);
        resolve(entry);
      };
    });
    img.src = url;
    this.#images.set(url, entry);
    return entry;
  }

  /** 按所需像素宽度取图；需要的档位还没载入时先用同一图层上一次的图。 */
  #layerImage(layer, pixels) {
    const entry = this.#loadImage(resolveSrc(layer.src, pixels));
    if (entry.ok) {
      this.#lastImage.set(layer.src, entry.img);
      return entry.img;
    }
    return this.#lastImage.get(layer.src) || null;
  }

  async #preloadLayers(scale) {
    const entries = this.#meta.layers.map((l) => this.#loadImage(resolveSrc(l.src, l.width * scale)));
    await Promise.all(entries.map((e) => e.promise));
    this.#meta.layers.forEach((l, i) => {
      if (entries[i].ok) this.#lastImage.set(l.src, entries[i].img);
    });
  }

  // ---------------------------------------------------------------- 输入

  // pen、mouse 书写；touch 在 fingerDraw 为 false 时单指平移、双指缩放，为 true 时
  // 单指书写、双指缩放。指针在按下时被捕获，所以一笔只属于起点所在的那块手写板。
  #onDown = (e) => {
    if (this.#destroyed || !this.#meta) return;
    e.preventDefault(); // 只在手写板区域内
    const [sx, sy] = this.#screen(e);
    const g = this.#gesture;
    if (e.pointerType === "touch") {
      this.#touches.set(e.pointerId, [sx, sy]);
      if (g && !g.touch) return; // 笔或鼠标正在工作，手指不打扰
      if (this.#touches.size === 2) {
        if (g?.kind === "ink") this.#cancelInk();
        if (g?.kind === "erase") this.#finishErase(g);
        this.#startPinch();
      } else if (this.#touches.size === 1) {
        if (this.#fingerDraw && this.#caps.write) this.#startInk(e, sx, sy, true);
        else this.#gesture = { kind: "pan", touch: true, id: e.pointerId, last: [sx, sy] };
      }
    } else {
      if (g && !g.touch) return; // 已经有一支笔或鼠标在工作
      if (e.pointerType === "mouse" && e.button !== 0 && e.button !== 1) return;
      if (g?.kind === "ink") this.#cancelInk(); // 笔优先于手指
      if (g?.kind === "erase") this.#finishErase(g);
      if (e.button === 1 || !this.#caps.write) this.#gesture = { kind: "pan", touch: false, id: e.pointerId, last: [sx, sy] };
      else this.#startInk(e, sx, sy, false);
    }
    try {
      this.#root.setPointerCapture(e.pointerId);
    } catch {
      // 合成的指针事件没有可捕获的指针
    }
  };

  #onMove = (e) => {
    if (this.#touches.has(e.pointerId)) this.#touches.set(e.pointerId, this.#screen(e));
    const g = this.#gesture;
    if (!g) return;
    if (g.kind === "pinch") {
      if (g.ids.includes(e.pointerId)) this.#updatePinch(g);
      return;
    }
    if (e.pointerId !== g.id) return;
    const events = e.getCoalescedEvents?.() || [];
    if (g.kind === "ink") {
      for (const ev of events.length ? events : [e]) {
        const [sx, sy] = this.#screen(ev);
        const [x, y] = this.#clampPoint(...this.#toWorld(sx, sy));
        const p = g.stroke.p;
        const rx = round(x), ry = round(y);
        if (p[p.length - 3] === rx && p[p.length - 2] === ry) continue;
        p.push(rx, ry, pressureOf(ev));
      }
      this.#requestRender(false);
    } else if (g.kind === "erase") {
      const [sx, sy] = this.#screen(e);
      const [x, y] = this.#toWorld(sx, sy);
      this.#eraseAlong(g, g.last[0], g.last[1], x, y);
      g.last = [x, y];
    } else if (g.kind === "pan") {
      const [sx, sy] = this.#screen(e);
      this.#view.x += sx - g.last[0];
      this.#view.y += sy - g.last[1];
      g.last = [sx, sy];
      this.#clampView();
      this.#requestRender();
    }
  };

  #onUp = (e) => {
    this.#touches.delete(e.pointerId);
    const g = this.#gesture;
    if (!g) return;
    if (g.kind === "pinch") {
      if (!g.ids.includes(e.pointerId)) return;
      this.#gesture = null;
      // 剩下的一根手指接着平移
      const [id, pos] = [...this.#touches][0] || [];
      if (id !== undefined) this.#gesture = { kind: "pan", touch: true, id, last: pos };
      return;
    }
    if (e.pointerId !== g.id) return;
    if (g.kind === "ink") {
      if (e.type === "pointercancel") this.#cancelInk();
      else this.#finishInk(g);
    } else if (g.kind === "erase") this.#finishErase(g);
    this.#gesture = null;
  };

  // 滚轮平移，按住 Ctrl（触控板捏合）或 ⌘ 时缩放。column 画布滚到头时不拦截，页面接着滚。
  #onWheel = (e) => {
    if (this.#destroyed || !this.#meta) return;
    let dx = e.deltaX, dy = e.deltaY;
    if (e.deltaMode === 1) { dx *= 16; dy *= 16; }
    else if (e.deltaMode === 2) { dx *= this.#size.w; dy *= this.#size.h; }
    const [sx, sy] = this.#screen(e);
    if (e.ctrlKey || e.metaKey) {
      e.preventDefault();
      this.#zoomAt(sx, sy, Math.exp(-dy * 0.01));
      return;
    }
    if (e.shiftKey && !dx) [dx, dy] = [dy, 0];
    const v = this.#view;
    const before = [v.x, v.y];
    v.x -= dx;
    v.y -= dy;
    this.#clampView();
    if (v.x === before[0] && v.y === before[1]) return;
    e.preventDefault();
    this.#requestRender();
  };

  #startInk(e, sx, sy, touch) {
    const [x, y] = this.#toWorld(sx, sy);
    const t = this.#tool;
    if (t.tool === "eraser") {
      // eraserMode "pixel" 替身未实现，一律按 object（碰到即删整笔）处理
      const g = { kind: "erase", touch, id: e.pointerId, last: [x, y], removed: [] };
      this.#gesture = g;
      this.#eraseAlong(g, x, y, x, y);
      return;
    }
    if (!this.#writable(x, y)) {
      // 起点在可书写范围外（纸外的灰色区域）：当作平移
      this.#gesture = { kind: "pan", touch, id: e.pointerId, last: [sx, sy] };
      return;
    }
    const stroke = {
      id: `${this.#idPrefix}-${++this.#seq}`,
      tool: t.tool,
      color: t.color,
      w: t.width,
      p: [round(x), round(y), pressureOf(e)],
      n: 0,
      dev: "web",
    };
    this.#gesture = { kind: "ink", touch, id: e.pointerId, stroke };
    this.#emit("strokestart", clone(stroke));
    this.#requestRender(false);
  }

  #finishInk(g) {
    this.#gesture = null;
    const stroke = g.stroke;
    stroke.n = this.#nextN();
    // 超过 20000 点的笔画切成几段（每段末点也是下一段的首点），和白板项目的 splitLongStroke 一样
    const pieces = [];
    const count = stroke.p.length / 3;
    if (count <= MAX_POINTS) pieces.push(stroke);
    else {
      for (let start = 0; start < count - 1; start += MAX_POINTS - 1) {
        const end = Math.min(start + MAX_POINTS, count);
        pieces.push({
          ...stroke,
          id: pieces.length ? `${this.#idPrefix}-${++this.#seq}` : stroke.id,
          n: stroke.n + pieces.length,
          p: stroke.p.slice(start * 3, end * 3),
        });
      }
    }
    this.#strokes.push(...pieces);
    this.#record({ type: "add", strokes: pieces });
    this.#commit({ op: "add", strokes: pieces });
    this.#emit("strokeend", clone(stroke));
  }

  /** 放弃正在写的一笔（被第二根手指、pointercancel、切换白板打断）。 */
  #cancelInk() {
    const g = this.#gesture;
    if (!g || g.kind !== "ink") return;
    this.#gesture = null;
    this.#emit("strokeend", clone(g.stroke));
    this.#requestRender(false);
  }

  #eraseAlong(g, x0, y0, x1, y1) {
    const r = Math.max(this.#tool.width, ERASER_MIN) / 2 / this.#view.scale;
    const steps = Math.max(1, Math.ceil(Math.hypot(x1 - x0, y1 - y0) / (r / 2)));
    const hit = new Set();
    for (const s of this.#strokes) {
      for (let k = 0; k <= steps; k++) {
        const t = k / steps;
        if (strokeHit(s, x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, r)) {
          hit.add(s);
          break;
        }
      }
    }
    if (!hit.size) return;
    this.#strokes = this.#strokes.filter((s) => !hit.has(s));
    g.removed.push(...hit);
    this.#requestRender();
  }

  /** 一次拖动擦掉的笔画合成一个操作、一条撤销记录。 */
  #finishErase(g) {
    this.#gesture = null;
    if (!g.removed.length) return;
    this.#record({ type: "remove", strokes: g.removed });
    this.#commit({ op: "remove", ids: g.removed.map((s) => s.id) });
  }

  #startPinch() {
    const [[a, pa], [b, pb]] = [...this.#touches];
    const mid = [(pa[0] + pb[0]) / 2, (pa[1] + pb[1]) / 2];
    this.#gesture = {
      kind: "pinch",
      touch: true,
      ids: [a, b],
      dist: Math.max(1, Math.hypot(pa[0] - pb[0], pa[1] - pb[1])),
      scale: this.#view.scale,
      world: this.#toWorld(...mid),
    };
  }

  #updatePinch(g) {
    const pa = this.#touches.get(g.ids[0]);
    const pb = this.#touches.get(g.ids[1]);
    if (!pa || !pb) return;
    const v = this.#view;
    const mid = [(pa[0] + pb[0]) / 2, (pa[1] + pb[1]) / 2];
    v.scale = clamp((g.scale * Math.hypot(pa[0] - pb[0], pa[1] - pb[1])) / g.dist, MIN_SCALE, MAX_SCALE);
    v.x = mid[0] - g.world[0] * v.scale;
    v.y = mid[1] - g.world[1] * v.scale;
    this.#clampView();
    this.#requestRender();
  }
}

/** 压感：只有笔有读数；鼠标和手指记 0.5。 */
function pressureOf(e) {
  return e.pointerType === "pen" && e.pressure > 0 ? round(e.pressure, 1000) : 0.5;
}
