// inksync 替身的自动测试。
//
// 运行：node app/web/inksync-stub/test.mjs
// 在仓库根目录临时起一个 python3 -m http.server，用 Playwright 驱动 Chromium 打开 test.html。
// 需要 data/ 下的题图（先 python3 sync.py pull）。

import { execSync, spawn } from "node:child_process";
import { createRequire } from "node:module";
import net from "node:net";
import path from "node:path";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, "../../..");
const CHROMIUM = "/opt/pw-browsers/chromium";
const require = createRequire(import.meta.url);
const { chromium } = require(path.join(execSync("npm root -g").toString().trim(), "playwright"));

// ------------------------------------------------------------------ 服务器

function freePort() {
  return new Promise((resolve, reject) => {
    const srv = net.createServer();
    srv.listen(0, "127.0.0.1", () => {
      const { port } = srv.address();
      srv.close(() => resolve(port));
    });
    srv.on("error", reject);
  });
}

async function startServer() {
  const port = await freePort();
  const proc = spawn("python3", ["-m", "http.server", String(port), "--bind", "127.0.0.1"], {
    cwd: ROOT,
    stdio: "ignore",
  });
  const base = `http://127.0.0.1:${port}`;
  for (let i = 0; i < 100; i++) {
    try {
      const res = await fetch(`${base}/app/web/inksync-stub/test.html`);
      if (res.ok) return { proc, base };
    } catch {
      // 还没起来
    }
    await new Promise((r) => setTimeout(r, 100));
  }
  proc.kill();
  throw new Error("http.server 没有起来");
}

// ------------------------------------------------------------------ 断言与辅助

function assert(cond, message) {
  if (!cond) throw new Error(message);
}

function eq(actual, expected, message) {
  const a = JSON.stringify(actual);
  const e = JSON.stringify(expected);
  if (a !== e) throw new Error(`${message}：期望 ${e}，实际 ${a}`);
}

let page;
let BASE;

const count = (pad) => page.evaluate((p) => window.pads[p].snapshot().strokes.length, pad);
const strokes = (pad) => page.evaluate((p) => window.pads[p].snapshot().strokes, pad);
const events = (pad, event) =>
  page.evaluate(([p, e]) => window.log.filter((x) => x.pad === p && x.event === e).map((x) => x.detail), [pad, event]);
const clearLog = () => page.evaluate(() => (window.log.length = 0));
const frames = () => page.evaluate(() => new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r))));

/** 在 selector 元素内（相对其左上角的 CSS 像素）用鼠标画一条线。 */
async function mouseLine(selector, from, to, steps = 12) {
  const box = await page.locator(selector).boundingBox();
  const at = (p) => [box.x + 1 + p[0], box.y + 1 + p[1]]; // +1：容器的边框
  await page.mouse.move(...at(from));
  await page.mouse.down();
  for (let i = 1; i <= steps; i++) {
    const t = i / steps;
    await page.mouse.move(...at([from[0] + (to[0] - from[0]) * t, from[1] + (to[1] - from[1]) * t]));
  }
  await page.mouse.up();
}

/** 合成触摸指针事件。tracks：每根手指一组相对坐标，逐步同时移动。 */
async function touch(selector, tracks) {
  await page.evaluate(
    ([sel, tracks]) => {
      const target = document.querySelector(`${sel} canvas`);
      const box = document.querySelector(sel).getBoundingClientRect();
      const fire = (type, id, [x, y]) =>
        target.dispatchEvent(
          new PointerEvent(type, {
            pointerId: 100 + id, pointerType: "touch", isPrimary: id === 0,
            clientX: box.left + 1 + x, clientY: box.top + 1 + y,
            pressure: type === "pointerup" ? 0 : 0.5, bubbles: true, cancelable: true,
          })
        );
      tracks.forEach((t, id) => fire("pointerdown", id, t[0]));
      const steps = Math.max(...tracks.map((t) => t.length));
      for (let k = 1; k < steps; k++) tracks.forEach((t, id) => fire("pointermove", id, t[Math.min(k, t.length - 1)]));
      tracks.forEach((t, id) => fire("pointerup", id, t[t.length - 1]));
    },
    [selector, tracks]
  );
}

async function waitLoaded() {
  await page.waitForFunction(() => window.pads && ["a", "b", "c"].every((k) => window.pads[k].board));
  await frames();
}

// ------------------------------------------------------------------ 用例

const tests = [];
const test = (name, fn) => tests.push({ name, fn });

test("载入：只读属性、元数据、全局对象", async () => {
  const info = await page.evaluate(() => {
    const a = window.pads.a;
    return {
      status: a.status, version: a.version, caps: a.caps, locked: a.locked, shell: a.shell, info: a.info,
      tool: a.tool, board: a.board, shellGlobal: typeof window.whiteboardShell,
      events: window.log.filter((x) => x.pad === "a").map((x) => x.event),
    };
  });
  eq(info.status, "local", "status");
  eq(info.version, "2.0.0-stub", "version");
  eq(info.caps, { write: true, clear: true, meta: true, unlock: false }, "caps");
  eq(info.locked, null, "locked");
  eq(info.shell, { active: false, version: "", bridge: false }, "shell");
  eq(info.info, {}, "info");
  eq(info.tool, { tool: "pen", color: "#1b1b1f", width: 3, eraserMode: "object" }, "默认工具");
  eq(info.shellGlobal, "object", "window.whiteboardShell");
  const b = info.board;
  eq([b.id, b.name], ["test-a", "9618 s21 P11 Q1"], "id、name");
  eq(b.canvas, { mode: "column", width: 800 }, "canvas");
  eq(b.background, { pattern: "lines", paper: "#ffffff" }, "background（paper 取默认）");
  eq(b.layers, [{ src: "/data/img9618/9618_s21_11_q01.png", x: 0, y: 0, width: 800 }], "layers");
  eq(b.data, { paper: "9618_s21_11", question: 1 }, "data");
  assert(typeof b.created === "number" && typeof b.updated === "number", "created、updated 是数");
  for (const e of ["status", "meta", "change", "history"]) assert(info.events.includes(e), `收到 ${e} 事件`);
  const cb = await page.evaluate(() => window.pads.c.board);
  eq(cb.canvas, { mode: "infinite" }, "canvas 默认 infinite");
});

test("高 DPI：画布按 devicePixelRatio 分配像素", async () => {
  const r = await page.evaluate(() => {
    const c = document.querySelector("#padA canvas");
    return { dpr: devicePixelRatio, w: c.width, cw: c.clientWidth, h: c.height, ch: c.clientHeight };
  });
  eq(r.dpr, 2, "devicePixelRatio");
  eq([r.w, r.h], [r.cw * 2, r.ch * 2], "画布像素");
});

test("两块手写板各自接收笔画；起点在 A 的一笔不进 B", async () => {
  await mouseLine("#padA", [50, 60], [200, 120]);
  eq([await count("a"), await count("b")], [1, 0], "A 画一笔");
  await mouseLine("#padB", [40, 40], [260, 160]);
  eq([await count("a"), await count("b")], [1, 1], "B 画一笔");
  // 从 A 拖进 B：只属于 A，越过 A 右边（白板 x=800）的点被截断
  await mouseLine("#padA", [300, 300], [560, 300], 20);
  eq([await count("a"), await count("b")], [2, 1], "跨板的一笔");
  const last = (await strokes("a"))[1];
  const xs = last.p.filter((_, i) => i % 3 === 0);
  assert(Math.max(...xs) <= 800, `越界的点被截断，最大 x=${Math.max(...xs)}`);
  eq(Math.max(...xs), 800, "截断到画布右边");
  await page.evaluate(() => window.pads.a.undo());
  const s = (await strokes("a"))[0];
  assert(typeof s.id === "string" && s.id.length > 0, "id");
  eq([s.tool, s.color, s.w, s.dev, s.n], ["pen", "#1b1b1f", 3, "web", 0], "笔画字段");
  assert(s.p.length % 3 === 0 && s.p.length >= 6, "p 为 [x, y, 压感, …]");
  // A 为 800 宽的 column，容器 400 宽：比例 0.5
  assert(Math.abs(s.p[0] - 100) < 1 && Math.abs(s.p[1] - 120) < 1, `坐标换算 (${s.p[0]}, ${s.p[1]})`);
  const ops = await events("a", "op");
  eq(ops[0].op.op, "add", "op 事件");
  eq(ops[0].board, "test-a", "op.board");
});

test("column 画布：一笔、撤销、重做", async () => {
  await page.evaluate(() =>
    window.pads.a.open("test-col", { create: { name: "col", canvas: { mode: "column", width: 800 } } })
  );
  eq(await count("a"), 0, "新白板为空");
  await clearLog();
  await mouseLine("#padA", [60, 60], [180, 90]);
  eq(await count("a"), 1, "画一笔后 1 笔");
  await page.evaluate(() => window.pads.a.undo());
  eq(await count("a"), 0, "undo 后 0 笔");
  await page.evaluate(() => window.pads.a.redo());
  eq(await count("a"), 1, "redo 后 1 笔");
  eq(await events("a", "history"), [{ undo: true, redo: false }, { undo: false, redo: true }, { undo: true, redo: false }], "history 事件");
  eq((await events("a", "op")).map((x) => x.op.op), ["add", "remove", "restore"], "op 序列");
  eq((await events("a", "strokestart")).length, 1, "strokestart");
  eq((await events("a", "strokeend")).length, 1, "strokeend");
});

test("fit、zoom：视图换算", async () => {
  // 放大后 fit 回到宽度铺满：屏幕 (100, 50) 对应白板 (200, 100)
  await page.evaluate(() => { window.pads.a.zoom(2); window.pads.a.fit(); });
  await mouseLine("#padA", [100, 50], [100, 50], 1);
  let s = (await strokes("a")).at(-1);
  assert(Math.abs(s.p[0] - 200) < 1 && Math.abs(s.p[1] - 100) < 1, `column fit 后 (${s.p[0]}, ${s.p[1]})`);
  await page.evaluate(() => window.pads.a.undo());
  // B：fixed 600×400，容器 300×200，首次打开宽度铺满，比例 0.5。
  // zoom(2) 以中心为基准：中心 (150, 100) 对应白板 (300, 200) 不动，(100, 50) 对应 (250, 150)
  await page.evaluate(() => window.pads.b.zoom(2));
  await mouseLine("#padB", [100, 50], [100, 50], 1);
  s = (await strokes("b")).at(-1);
  assert(Math.abs(s.p[0] - 250) < 1 && Math.abs(s.p[1] - 150) < 1, `zoom 后 (${s.p[0]}, ${s.p[1]})`);
  await page.evaluate(() => { window.pads.b.undo(); window.pads.b.fit(); });
  await mouseLine("#padB", [100, 50], [100, 50], 1);
  s = (await strokes("b")).at(-1);
  assert(Math.abs(s.p[0] - 200) < 1 && Math.abs(s.p[1] - 100) < 1, `fixed fit 后 (${s.p[0]}, ${s.p[1]})`);
  await page.evaluate(() => window.pads.b.undo());
});

test("橡皮擦：碰到即删整笔；pixel 退化为 object", async () => {
  eq(await count("b"), 1, "B 原有 1 笔");
  await clearLog();
  await page.evaluate(() => window.pads.b.setTool({ tool: "eraser" }));
  await mouseLine("#padB", [150, 20], [150, 190]);
  eq(await count("b"), 0, "擦掉");
  const ops = await events("b", "op");
  eq(ops.map((x) => x.op.op), ["remove"], "一次拖动一个 remove 操作");
  await page.evaluate(() => window.pads.b.undo());
  eq(await count("b"), 1, "undo 恢复");
  await page.evaluate(() => window.pads.b.setTool({ eraserMode: "pixel" }));
  await mouseLine("#padB", [150, 20], [150, 190]);
  eq(await count("b"), 0, "pixel 模式也整笔擦除");
  await page.evaluate(() => window.pads.b.undo());
  eq(await count("b"), 1, "再次恢复");
  await page.evaluate(() => window.pads.b.setTool({ tool: "pen", eraserMode: "object" }));
  // 没碰到的笔画不删
  await page.evaluate(() => window.pads.b.setTool({ tool: "eraser" }));
  await mouseLine("#padB", [290, 10], [290, 20]);
  eq(await count("b"), 1, "没碰到不删");
  await page.evaluate(() => window.pads.b.setTool({ tool: "pen" }));
});

test("open 切换白板再切回，原笔画还在（localStorage）；刷新后仍在", async () => {
  await clearLog();
  const meta = await page.evaluate(() => window.pads.a.open("test-a"));
  eq(meta.id, "test-a", "open 返回元数据");
  eq(await count("a"), 1, "切回后原笔画还在");
  eq(await events("a", "history"), [{ undo: false, redo: false }], "撤销记录清空");
  const stored = await page.evaluate(() => JSON.parse(localStorage.getItem("stubtest:test-a")));
  eq(stored.strokes.length, 1, "localStorage 中有 1 笔");
  eq(stored.meta.id, "test-a", "localStorage 中的元数据");
  await page.goto(`${BASE}/app/web/inksync-stub/test.html`); // 不带 ?reset
  await waitLoaded();
  eq([await count("a"), await count("b")], [1, 1], "刷新后从 localStorage 取回");
  await page.evaluate(() => window.pads.a.open("test-col"));
  eq(await count("a"), 1, "另一块白板的内容也在");
  await page.evaluate(() => window.pads.a.open("test-a"));
});

test("exportPNG：图片层与范围", async () => {
  const r = await page.evaluate(async () => {
    const size = (url) => new Promise((res) => {
      const img = new Image();
      img.onload = () => res([img.naturalWidth, img.naturalHeight]);
      img.src = url;
    });
    const a = window.pads.a, b = window.pads.b;
    const withLayers = await a.exportPNG({ layers: true });
    const plain = await a.exportPNG();
    const fixed = await b.exportPNG();
    const fixed2 = await b.exportPNG({ scale: 2 });
    return {
      prefix: withLayers.slice(0, 22),
      withLayers: await size(withLayers),
      plain: await size(plain),
      fixed: await size(fixed),
      fixed2: await size(fixed2),
    };
  });
  eq(r.prefix, "data:image/png;base64,", "PNG data URL");
  const layerHeight = (800 * 3348) / 1166; // height 省略时按比例
  eq(r.withLayers[0], 800, "column 带图片层：宽度为画布宽");
  assert(r.withLayers[1] >= Math.floor(layerHeight), `高度 ${r.withLayers[1]} 不小于图片层 ${layerHeight}`);
  assert(r.plain[1] < 400 && r.plain[0] < 800, `不带图片层：笔迹外框加边距 ${r.plain}`);
  eq(r.fixed, [600, 400], "fixed 为整个画布");
  eq(r.fixed2, [1200, 800], "scale 2");
});

test("页面输入框、按钮、滚动不受影响", async () => {
  await page.click("#name");
  await page.keyboard.type("hello 123");
  eq(await page.inputValue("#name"), "hello 123", "输入框");
  await page.click("#btn");
  eq(await page.textContent("#clicks"), "1", "按钮");
  // 在手写板上画一笔后回到输入框继续输入
  await mouseLine("#padC", [30, 30], [60, 40]);
  await page.click("#name");
  await page.keyboard.type("!");
  eq(await page.inputValue("#name"), "hello 123!", "画完后继续输入");
  // 滚轮在 column 手写板上平移手写板，页面不动；在手写板外滚动页面
  const box = await page.locator("#padA").boundingBox();
  await page.mouse.move(box.x + 200, box.y + 250);
  await page.mouse.wheel(0, 200);
  await page.waitForTimeout(300);
  eq(await page.evaluate(() => scrollY), 0, "手写板上的滚轮不滚动页面");
  const spacer = await page.locator("#spacer").boundingBox();
  await page.mouse.move(spacer.x + 100, spacer.y + 50);
  await page.mouse.wheel(0, 300);
  await page.waitForFunction(() => scrollY > 0, null, { timeout: 3000 });
  await page.evaluate(() => scrollTo(0, 0));
  await page.evaluate(() => window.pads.a.fit());
  await page.evaluate(() => window.pads.c.undo());
});

test("setMeta：data 按键合并、null 删除；layers、background 整体替换；canvas 不可改", async () => {
  await clearLog();
  const r = await page.evaluate(() => {
    const a = window.pads.a;
    const layers = a.board.layers;
    a.setMeta({ data: { x: 1, y: 2 } });
    const d1 = a.board.data;
    a.setMeta({ data: { y: null, question: 5, z: { k: [1] } } });
    const d2 = a.board.data;
    a.setMeta({ name: "改名", background: { pattern: "dots" } });
    const bg = a.board.background;
    a.setMeta({ layers: [{ src: "/x.png", x: 1, y: 2, width: 3, z: "above" }] });
    const l2 = a.board.layers;
    a.setMeta({ layers });
    let canvasError = null;
    try { a.setMeta({ canvas: { mode: "fixed", width: 1, height: 1 } }); } catch (e) { canvasError = e.message; }
    let badError = null;
    try { a.setMeta({ background: { pattern: "stripes" } }); } catch (e) { badError = e.message; }
    return { d1, d2, bg, l2, name: a.board.name, canvas: a.board.canvas, canvasError, badError,
      stored: JSON.parse(localStorage.getItem("stubtest:test-a")).meta.data };
  });
  eq(r.d1, { paper: "9618_s21_11", question: 1, x: 1, y: 2 }, "合并新键");
  eq(r.d2, { paper: "9618_s21_11", question: 5, x: 1, z: { k: [1] } }, "替换、删除、保留");
  eq(r.bg, { pattern: "dots", paper: "#ffffff" }, "background 整体替换");
  eq(r.l2, [{ src: "/x.png", x: 1, y: 2, width: 3, z: "above" }], "layers 整体替换");
  eq(r.name, "改名", "name");
  eq(r.canvas, { mode: "column", width: 800 }, "canvas 不变");
  assert(r.canvasError, "修改 canvas 抛错");
  assert(r.badError, "不合法的 background 抛错");
  eq(r.stored, r.d2, "写回 localStorage");
  const metaEvents = await events("a", "meta");
  eq(metaEvents.length, 5, "每次成功的 setMeta 一个 meta 事件");
  eq((await events("a", "op")).map((x) => x.op.op), Array(5).fill("meta"), "op 事件");
});

test("非法 board 抛错；不存在或 create 不合法时触发 error", async () => {
  await clearLog();
  const r = await page.evaluate(async () => {
    const out = {};
    const host = document.getElementById("spare");
    try { window.createInkPad(host, { board: "bad id!" }); } catch (e) { out.ctor = e.message; }
    try { window.createInkPad(host, { board: "x".repeat(65) }); } catch (e) { out.long = e.message; }
    const b = window.pads.b;
    out.reasons = [];
    for (const [id, opts] of [["bad/id", {}], ["no-such-board", {}], ["bad-create", { create: { canvas: { mode: "column" } } }],
      ["bad-name", { create: { name: "n".repeat(65) } }], ["bad-data", { create: { data: { s: "x".repeat(17000) } } }]]) {
      try { await b.open(id, opts); out.reasons.push("resolved"); } catch (e) { out.reasons.push(e.reason); }
    }
    out.still = b.board.id;
    // 构造时白板不存在且没有 create：error 事件
    const div = document.createElement("div");
    div.style.height = "50px";
    host.append(div);
    const pad = window.createInkPad(div, { board: "never-created", storage: "stubtest:" });
    out.ctorError = await new Promise((res) => pad.on("error", res));
    out.ctorBoard = pad.board;
    pad.destroy();
    out.stored = localStorage.getItem("stubtest:never-created");
    return out;
  });
  assert(r.ctor && r.long, "createInkPad 对非法 board 抛错");
  eq(r.reasons, ["board", "board", "create", "create", "create"], "open 失败的 reason");
  eq((await events("b", "error")).map((x) => x.reason), ["board", "board", "create", "create", "create"], "error 事件");
  eq(r.still, "test-b", "失败时保留原白板");
  eq(r.ctorError.reason, "board", "构造时白板不存在");
  eq(r.ctorBoard, null, "没有白板");
  eq(r.stored, null, "不会在本地存储中新建");
});

test("readonly：caps 为 false，不能书写、清空、改元数据", async () => {
  await clearLog();
  await page.evaluate(() => window.pads.b.open("test-b", { readonly: true }));
  eq(await page.evaluate(() => window.pads.b.caps), { write: false, clear: false, meta: false, unlock: false }, "caps");
  eq(await events("b", "caps"), [{ write: false, clear: false, meta: false, unlock: false }], "caps 事件");
  await mouseLine("#padB", [40, 150], [200, 150]);
  eq(await count("b"), 1, "不能书写");
  await page.evaluate(() => { window.pads.b.clear(); window.pads.b.setMeta({ name: "x" }); });
  eq(await count("b"), 1, "不能清空");
  eq(await page.evaluate(() => window.pads.b.board.name), "B", "不能改元数据");
  await page.evaluate(() => window.pads.b.open("test-b"));
  eq((await page.evaluate(() => window.pads.b.caps)).write, true, "重新以可写方式打开");
});

test("触摸：fingerDraw 为 false 时平移、双指缩放；为 true 时书写", async () => {
  // B：fixed 600×400，容器 300×200，比例 0.5
  const before = await count("b");
  await touch("#padB", [[[50, 50], [80, 60], [120, 80]]]);
  eq(await count("b"), before, "单指不书写");
  await page.evaluate(() => window.pads.b.fit());
  // 以 (150, 100) 为中心双指张开一倍：比例 0.5 -> 1，中心对应的白板点 (300, 200) 不动
  await touch("#padB", [
    [[125, 100], [112, 100], [100, 100]],
    [[175, 100], [188, 100], [200, 100]],
  ]);
  await mouseLine("#padB", [200, 100], [200, 100], 1);
  let s = (await strokes("b")).at(-1);
  assert(Math.abs(s.p[0] - 350) < 1 && Math.abs(s.p[1] - 200) < 1, `捏合放大后 (${s.p[0]}, ${s.p[1]})`);
  await page.evaluate(() => { window.pads.b.undo(); window.pads.b.fit(); });
  await mouseLine("#padB", [200, 100], [200, 100], 1);
  s = (await strokes("b")).at(-1);
  assert(Math.abs(s.p[0] - 400) < 1 && Math.abs(s.p[1] - 200) < 1, `fit 后 (${s.p[0]}, ${s.p[1]})`);
  await page.evaluate(() => window.pads.b.undo());
  // C：fingerDraw
  const c0 = await count("c");
  await touch("#padC", [[[40, 120], [80, 130], [120, 140]]]);
  eq(await count("c"), c0 + 1, "fingerDraw 单指书写");
});

test("工具：马克笔、荧光笔半透明；清空可撤销", async () => {
  const c = "#padC";
  await page.evaluate(() => window.pads.c.clear());
  eq(await count("c"), 0, "清空");
  await page.evaluate(() => window.pads.c.undo());
  assert((await count("c")) > 0, "撤销清空");
  await page.evaluate(() => window.pads.c.clear());
  await page.evaluate(() => window.pads.c.setTool({ tool: "pen", color: "#ff0000", width: 20 }));
  await mouseLine(c, [30, 50], [130, 50]);
  await page.evaluate(() => window.pads.c.setTool({ tool: "highlighter" }));
  await mouseLine(c, [30, 150], [130, 150]);
  await page.evaluate(() => window.pads.c.setTool({ tool: "marker", color: "#0000ff" }));
  await mouseLine(c, [170, 100], [270, 100]);
  eq((await strokes("c")).map((s) => s.tool), ["pen", "highlighter", "marker"], "tool 字段");
  await frames();
  const px = await page.evaluate(() => {
    const canvas = document.querySelector("#padC canvas");
    const ctx = canvas.getContext("2d");
    const at = (x, y) => Array.from(ctx.getImageData(x * devicePixelRatio, y * devicePixelRatio, 1, 1).data);
    return { pen: at(83, 53), hl: at(83, 153), marker: at(223, 103), empty: at(283, 23) };
  });
  assert(px.pen[0] > 240 && px.pen[1] < 20 && px.pen[2] < 20, `钢笔为不透明红色 ${px.pen}`);
  assert(px.hl[0] > 240 && px.hl[1] > 150 && px.hl[1] < 210, `荧光笔半透明 ${px.hl}`);
  assert(px.marker[2] > 240 && px.marker[0] < 20, `马克笔蓝色 ${px.marker}`);
  assert(px.empty[0] > 240 && px.empty[1] > 240 && px.empty[2] > 240, `空白处为纸色 ${px.empty}`);
});

test("容器尺寸变化：column 画布保持宽度铺满", async () => {
  await page.evaluate(() => (document.getElementById("padA").style.width = "600px"));
  await page.waitForFunction(() => document.querySelector("#padA canvas").width === 600 * devicePixelRatio);
  await frames();
  await mouseLine("#padA", [150, 75], [150, 75], 1);
  const s = (await strokes("a")).at(-1);
  // 比例 600/800：屏幕 (150, 75) 对应白板 (200, 100)
  assert(Math.abs(s.p[0] - 200) < 1 && Math.abs(s.p[1] - 100) < 1, `(${s.p[0]}, ${s.p[1]})`);
  await page.evaluate(() => { window.pads.a.undo(); document.getElementById("padA").style.width = "400px"; });
});

test("load、snapshot、initial、on 的取消、destroy", async () => {
  const r = await page.evaluate(async () => {
    const out = {};
    const c = window.pads.c;
    const stroke = { id: "s1", tool: "pen", color: "#123456", w: 2, p: [1, 2, 0.5, 3, 4, 0.5], n: 7, dev: "ipad" };
    c.load({ meta: { name: "L", canvas: { mode: "infinite" }, data: { k: 1 } }, strokes: [stroke] });
    const snap = c.snapshot();
    out.snap = structuredClone({ id: snap.meta.id, name: snap.meta.name, data: snap.meta.data, strokes: snap.strokes });
    snap.strokes[0].color = "#000000";
    out.copy = c.snapshot().strokes[0].color;
    let n = 0;
    const off = c.on("change", () => n++);
    c.undo(); // 撤销记录已清空，不应触发
    await c.exportPNG();
    off();
    c.clear();
    out.changes = n;
    // initial 优先于本地存储和 create
    const div = document.createElement("div");
    div.style.cssText = "width:200px;height:100px";
    document.getElementById("spare").append(div);
    const pad = window.createInkPad(div, {
      board: "test-c", storage: "stubtest:", initial: { meta: { name: "I" }, strokes: [stroke, { ...stroke, id: "s2", n: 8 }] },
    });
    await new Promise((res) => pad.on("meta", res));
    out.initial = [pad.board.name, pad.snapshot().strokes.length];
    pad.destroy();
    out.removed = div.childElementCount;
    out.stored = JSON.parse(localStorage.getItem("stubtest:test-c")).strokes.length;
    return out;
  });
  eq(r.snap, { id: "test-c", name: "L", data: { k: 1 }, strokes: [{ id: "s1", tool: "pen", color: "#123456", w: 2, p: [1, 2, 0.5, 3, 4, 0.5], n: 7, dev: "ipad" }] }, "load 后 snapshot");
  eq(r.copy, "#123456", "snapshot 是副本");
  eq(r.changes, 0, "取消订阅后不再收到");
  eq(r.initial, ["I", 2], "initial");
  eq(r.removed, 0, "destroy 移除 DOM");
  eq(r.stored, 2, "destroy 写回本地存储");
});

// ------------------------------------------------------------------ 运行

const { proc, base } = await startServer();
BASE = base;
const browser = await chromium.launch({ executablePath: CHROMIUM });
let failed = 0;
try {
  const context = await browser.newContext({ viewport: { width: 1200, height: 800 }, deviceScaleFactor: 2 });
  page = await context.newPage();
  const pageErrors = [];
  page.on("pageerror", (err) => pageErrors.push(err.message));
  await page.goto(`${base}/app/web/inksync-stub/test.html?reset`);
  await waitLoaded();
  for (const { name, fn } of tests) {
    try {
      await fn();
      console.log(`ok    ${name}`);
    } catch (err) {
      failed++;
      console.log(`FAIL  ${name}\n      ${err.message.split("\n")[0]}`);
    }
  }
  if (pageErrors.length) {
    failed++;
    console.log(`FAIL  页面报错：\n      ${pageErrors.join("\n      ")}`);
  }
} finally {
  await browser.close();
  proc.kill();
}
console.log(failed ? `\n${failed} 项失败` : `\n全部 ${tests.length} 项通过`);
process.exit(failed ? 1 : 0);
