// 书写工具栏:按 white-board 的 ui.js 移植(提交 373432a),外观与手感和白板一致。
//
// 普通工具栏是一排图标:钢笔、马克笔、荧光笔、橡皮擦,颜色与粗细在一个弹层里,
// 每件工具各记一套。iPad 上换成笔具盘(wb/pkpicker.js),普通那条收起来。
// 工具状态的格式与 inksync 的 pad.setTool 相同:{ tool, color, width, eraserMode }。

import { icon } from "./wb/icons.js";
import { loadPicker } from "./wb/pkpicker.js";
import { el, clamp } from "./wb/util.js";

export const COLORS = [
  "#1b1b1f", "#5f6368", "#e53935", "#fb8c00", "#fdd835",
  "#43a047", "#00acc1", "#1e88e5", "#8e24aa", "#6d4c41",
];
export const WIDTHS = [1.5, 3, 5, 8, 13];
const ERASER_MODES = [
  { key: "object", title: "对象橡皮擦" },
  { key: "pixel", title: "像素橡皮擦" },
];
const INK_TOOLS = ["pen", "marker", "highlighter"];
const ALL_TOOLS = [...INK_TOOLS, "eraser"];
const TOOL_TITLES = { pen: "钢笔", marker: "马克笔", highlighter: "荧光笔", eraser: "橡皮擦" };
const TOOL_KEY = "qb.tool";
const DOCK_KEY = "qb.toolbar";
const HEX = /^#[0-9a-fA-F]{6}$/;

function defaultTool() {
  return {
    tool: "pen",
    pen: { color: COLORS[0], widthIndex: 1 },
    marker: { color: COLORS[2], widthIndex: 2 },
    highlighter: { color: COLORS[4], widthIndex: 3 },
    eraser: { color: COLORS[0], widthIndex: 0 },
    eraserMode: "object",
  };
}

function loadTool() {
  const state = defaultTool();
  try {
    const saved = JSON.parse(localStorage.getItem(TOOL_KEY) || "null");
    if (!saved) return state;
    if (ALL_TOOLS.includes(saved.tool)) state.tool = saved.tool;
    if (ERASER_MODES.some((m) => m.key === saved.eraserMode)) state.eraserMode = saved.eraserMode;
    for (const key of ALL_TOOLS) {
      const raw = saved[key];
      if (raw && HEX.test(raw.color)) state[key].color = raw.color;
      if (raw && raw.widthIndex >= 0 && raw.widthIndex < WIDTHS.length) state[key].widthIndex = raw.widthIndex;
    }
  } catch {}
  return state;
}

/** iPad(含桌面版 UA 的 iPadOS)用笔具盘,其余设备用普通工具栏。 */
function isIPad() {
  const ua = navigator.userAgent || "";
  return /iPad/.test(ua) || (/Macintosh/.test(ua) && navigator.maxTouchPoints > 1);
}

export function iconButton(name, title, onClick, extraClass = "") {
  return el("button", {
    class: `icon-btn ${extraClass}`.trim(),
    title,
    "aria-label": title,
    html: icon(name),
    onclick: onClick,
  });
}

export class Tools {
  /**
   * @param root   放工具栏和弹层的容器
   * @param actions { onToolChange(tool), onUndo(), onRedo() }
   */
  constructor(root, actions) {
    this.root = root;
    this.actions = actions;
    this.tool = loadTool();
    this.picker = isIPad();
    this.popover = null;
    this.undoEnabled = false;
    this.redoEnabled = false;
    this.bar = el("div", { id: "toolbar", class: "pill" });
    root.append(this.bar);
    this.applyDock(this.loadDock());
    this.fill();
  }

  get ink() {
    return this.tool[this.tool.tool] || this.tool.pen;
  }

  toolState() {
    return { tool: this.tool.tool, color: this.ink.color, width: WIDTHS[this.ink.widthIndex],
             eraserMode: this.tool.eraserMode };
  }

  fill() {
    const bar = this.bar;
    this.buttons = {};
    for (const key of ALL_TOOLS) {
      const b = iconButton(key, TOOL_TITLES[key], () => this.select(key));
      this.buttons[key] = b;
      bar.append(b);
    }
    bar.append(el("div", { class: "sep" }));
    this.dockButton = iconButton("dockTop", "工具栏换个位置", () => this.toggleDock());
    bar.append(this.dockButton, el("div", { class: "sep" }));
    this.colorButton = el("button", { class: "icon-btn", title: "颜色与粗细", "aria-label": "颜色与粗细",
                                      onclick: (e) => this.togglePalette(e.currentTarget) });
    this.colorDot = el("i", { class: "color-dot" });
    this.colorButton.append(this.colorDot);
    bar.append(this.colorButton, el("div", { class: "sep" }));
    this.undoButton = iconButton("undo", "撤销", () => this.actions.onUndo());
    this.redoButton = iconButton("redo", "重做", () => this.actions.onRedo());
    bar.append(this.undoButton, this.redoButton);
    this.syncDockButton();
    this.setHistory(false, false);
    this.select(this.tool.tool);
    if (this.picker) this.mountPicker();
  }

  select(tool) {
    this.tool.tool = ALL_TOOLS.includes(tool) ? tool : "pen";
    this.remember();
    for (const [key, b] of Object.entries(this.buttons)) {
      b.classList.toggle("active", key === this.tool.tool);
      b.setAttribute("aria-pressed", String(key === this.tool.tool));
    }
    this.colorDot.style.background = this.ink.color;
    this.actions.onToolChange(this.toolState());
  }

  /** 笔具盘模式下只改当前这支,普通工具栏一改全改(与白板相同)。 */
  setInk(patch) {
    for (const key of this.picker ? [this.tool.tool] : ALL_TOOLS) Object.assign(this.tool[key], patch);
    this.remember();
    this.colorDot.style.background = this.ink.color;
    this.actions.onToolChange(this.toolState());
  }

  remember() {
    try { localStorage.setItem(TOOL_KEY, JSON.stringify(this.tool)); } catch {}
  }

  setHistory(undo, redo) {
    this.undoEnabled = !!undo;
    this.redoEnabled = !!redo;
    this.undoButton.toggleAttribute("disabled", !undo);
    this.redoButton.toggleAttribute("disabled", !redo);
    if (this.pk) this.pk.setHistory(this.undoEnabled, this.redoEnabled);
  }

  /** 以前的作答只能看:工具栏收起来。 */
  setReadonly(ro) {
    this.bar.hidden = ro || !!this.pk;
    if (this.pkHost) this.pkHost.hidden = ro;
  }

  // ---------------------------------------------------------------- 位置

  loadDock() {
    try { return localStorage.getItem(DOCK_KEY) === "top" ? "top" : "bottom"; } catch { return "bottom"; }
  }

  applyDock(dock) {
    this.dock = dock;
    document.documentElement.dataset.toolbar = dock;
    try { localStorage.setItem(DOCK_KEY, dock); } catch {}
  }

  toggleDock() {
    this.closePopover();
    this.applyDock(this.dock === "top" ? "bottom" : "top");
    this.syncDockButton();
  }

  syncDockButton() {
    this.dockButton.innerHTML = icon(this.dock === "top" ? "dockBottom" : "dockTop");
  }

  // ---------------------------------------------------------------- 笔具盘

  async mountPicker() {
    try {
      const Picker = await loadPicker();
      this.pkHost = el("div", { id: "pk-host" });
      this.root.append(this.pkHost);
      const pk = new Picker(this.pkHost, { theme: "auto" });
      pk.onChange = (s) => {
        const entry = this.tool[s.tool];
        if (entry) {
          entry.color = s.color;
          entry.widthIndex = clamp(s.sizeIndex, 0, WIDTHS.length - 1);
        }
        if (s.eraserMode) this.tool.eraserMode = s.eraserMode;
        this.select(s.tool);
      };
      pk.onUndo = () => this.actions.onUndo();
      pk.onRedo = () => this.actions.onRedo();
      pk.allowClear = false;
      pk.applyState({ tool: this.tool.tool, color: this.ink.color, sizeIndex: this.ink.widthIndex,
                      fingerDraws: false, eraserMode: this.tool.eraserMode });
      pk.setHistory(this.undoEnabled, this.redoEnabled);
      this.pk = pk;
      this.bar.hidden = true;
    } catch {
      this.picker = false;
    }
  }

  strokeStarted() {
    if (this.pk) this.pk.strokeStarted();
  }

  // ---------------------------------------------------------------- 弹层

  closePopover() {
    if (!this.popover) return;
    this.popover.remove();
    this.popover = null;
    removeEventListener("pointerdown", this.closer, true);
  }

  showPopover(anchor, content) {
    this.closePopover();
    const pop = el("div", { class: "popover" }, content);
    this.root.append(pop);
    const r = anchor.getBoundingClientRect();
    const w = pop.offsetWidth, h = pop.offsetHeight;
    pop.style.left = `${clamp(r.left + r.width / 2 - w / 2, 12, innerWidth - w - 12)}px`;
    const above = r.top - h - 12;
    pop.style.top = above >= 12 ? `${above}px` : `${clamp(r.bottom + 12, 12, Math.max(12, innerHeight - h - 12))}px`;
    this.popover = pop;
    this.closer = (e) => { if (!pop.contains(e.target) && !anchor.contains(e.target)) this.closePopover(); };
    setTimeout(() => addEventListener("pointerdown", this.closer, true), 0);
    return pop;
  }

  togglePalette(anchor) {
    if (this.popover) { this.closePopover(); return; }
    this.showPopover(anchor, this.tool.tool === "eraser" ? [this.eraserModes()]
                                                         : [this.swatches(), this.widths()]);
  }

  swatches() {
    const box = el("div", { class: "swatches" });
    for (const color of COLORS) {
      const b = el("button", {
        class: `swatch${color === this.ink.color ? " active" : ""}`, style: { background: color }, title: color,
        onclick: () => {
          this.setInk({ color });
          for (const n of box.children) n.classList.remove("active");
          b.classList.add("active");
        },
      });
      box.append(b);
    }
    return box;
  }

  widths() {
    const box = el("div", { class: "widths" });
    WIDTHS.forEach((width, i) => {
      const size = 4 + i * 4;
      const b = el("button", {
        class: `width-opt${i === this.ink.widthIndex ? " active" : ""}`, title: `${width}`,
        onclick: () => {
          this.setInk({ widthIndex: i });
          for (const n of box.children) n.classList.remove("active");
          b.classList.add("active");
        },
      }, [el("i", { style: { width: `${size}px`, height: `${size}px` } })]);
      box.append(b);
    });
    return box;
  }

  eraserModes() {
    const row = el("div", { class: "seg", role: "radiogroup", "aria-label": "橡皮擦类型" });
    for (const mode of ERASER_MODES) {
      const b = el("button", {
        class: this.tool.eraserMode === mode.key ? "is-on" : "", role: "radio",
        "aria-checked": String(this.tool.eraserMode === mode.key), text: mode.title,
        onclick: () => {
          this.tool.eraserMode = mode.key;
          this.remember();
          for (const n of row.children) {
            n.classList.toggle("is-on", n === b);
            n.setAttribute("aria-checked", String(n === b));
          }
          this.actions.onToolChange(this.toolState());
          if (this.pk) this.pk.setEraserMode(mode.key);
        },
      });
      row.append(b);
    }
    return row;
  }
}
