// 题目卷白板(docs/data-manager.md F5):白板应用的书写界面接到一块题目卷白板上。
//
// 书写、橡皮擦、撤销、同步和视口都在 inksync 的 InkPad 里;工具栏、颜色与粗细、
// iPad 上的笔具盘来自白板应用的 ui.js。白板应用里管白板列表、设置、更新的部分
// 这里不用:一个页面只写一块白板,导出批注版在 Mac 的顶栏。
// iPad 只用来书写:没有顶栏与导出,只有画布与笔具盘;在原生外壳里保留「白板设置」,
// 其中的「换一台 Mac」用来选择服务器。

import { InkPad, deviceClientId } from "/inksync/pad.js";
import { isTextField } from "/inksync/util.js";
import { UI } from "./ui.js";
import { icon } from "./icons.js";
import { boardView, loadFingerDraw, saveFingerDraw } from "./boards.js";
import { iconButton } from "./ui-common.js";
import { el } from "/inksync/util.js";
import { inShell } from "/inksync/shell.js";

// /write/<id> opens that board; /ipad (the iPad shell's page) follows the board the Mac opened last.
// /write/<id>?embed=1 is the board inside the data manager's page (#/sets/<set>/board/<id>), which
// draws the header itself: no header here, the current question and page are posted to the parent.
const FOLLOW = location.pathname === "/ipad";
const EMBED = new URLSearchParams(location.search).has("embed");
if (EMBED) document.documentElement.dataset.embed = "1";
const BOARD = FOLLOW ? null : decodeURIComponent(location.pathname.split("/").pop());

function role() {
  return navigator.maxTouchPoints > 1 || /iPad|iPhone/.test(navigator.userAgent) ? "ipad" : "mac";
}

/**
 * 白板应用的界面,去掉右上角那一组(白板列表、设置、导出 PNG);Mac 上保留缩放。
 * iPad 外壳里只留「白板设置」,用于换一台 Mac。
 */
class WriteUI extends UI {
  buildCorner() {
    if (this.role !== "mac") {
      if (inShell()) {
        this.info = { hostname: location.hostname, port: location.port };
        this.root.append(
          el("div", { id: "topright", class: "pill tinted" }, [
            iconButton("settings", "白板设置", () => this.openSettings()),
          ]),
        );
      }
      return;
    }
    this.root.append(
      el("div", { id: "zoombar", class: "pill" }, [
        iconButton("zoomIn", "放大", () => this.actions.onZoom(1.25)),
        iconButton("fit", "适应页面", () => this.actions.onFit()),
        iconButton("zoomOut", "缩小", () => this.actions.onZoom(0.8)),
      ]),
    );
  }

  setPerms(perms) {
    this.perms = perms;
    if (this.clearButton) this.clearButton.hidden = !this.may("clear");
    if (this.pk) this.pk.allowClear = this.may("clear");
  }
}

class Writer extends InkPad {
  constructor() {
    const r = role();
    document.documentElement.dataset.role = r;
    super({
      role: r,
      clientId: deviceClientId(),
      target: FOLLOW ? { space: "", follow: true } : { space: "", board: BOARD, follow: false },
      fingerDraw: loadFingerDraw(),
      stage: document.getElementById("stage"),
      base: document.getElementById("base"),
      live: document.getElementById("live"),
    });
    this.ui = new WriteUI({ role: r, native: false, perms: new Set(["clear"]), actions: this.actions() });
    this.tool = this.ui.toolState();
    this.bindPad();
    this.bindHead();
    this.bindKeys();
    this.start();
  }

  actions() {
    return {
      isNative: () => false,
      onFingerDraw: (enabled) => {
        this.input.setFingerDraw(enabled);
        saveFingerDraw(enabled);
      },
      onToolChange: (tool) => this.setTool(tool),
      onUndo: () => this.undo(),
      onRedo: () => this.redo(),
      onClear: () => this.clearBoard(),
      onZoom: (factor) => this.zoom(factor),
      onFit: () => this.fit(),
      onToggleDebug: () => this.perf.toggle(),
    };
  }

  bindPad() {
    const root = document.documentElement;
    this.on("status", (status) => this.ui.setStatus(status));
    this.on("history", ({ undo, redo }) => {
      this.ui.setUndoEnabled(undo);
      this.ui.setRedoEnabled(redo);
    });
    this.on("meta", (meta) => {
      this.ui.setMeta(boardView(meta));
      this.showMeta(meta);
    });
    this.on("shell", (shell) => {
      root.dataset.shell = shell.active ? "active" : "inactive";
    });
    this.on("strokestart", () => {
      root.dataset.drawing = "1";
      this.ui.strokeStarted();
    });
    this.on("strokeend", () => {
      delete root.dataset.drawing;
    });
    this.on("interrupted", () => {
      this.ui.showNotice(
        "scribble",
        "Apple Pencil 的笔迹多次被系统中断。请在 iPad 的「设置」中进入「Apple Pencil」，关闭「随手写」。",
      );
    });
    this.on("locked", ({ locked, unlock }) => {
      root.toggleAttribute("data-locked", !!locked);
      if (locked) this.ui.showLocked(locked, unlock);
      else this.ui.hideLocked();
    });
    this.on("error", ({ reason }) => this.ui.message(`白板无法打开（${reason}）`, "close", 8000));
    this.on("deleted", () => this.ui.message("白板已删除", "close", 8000));
  }

  bindKeys() {
    addEventListener("keydown", (event) => {
      if (isTextField(event.target)) return;
      const meta = event.metaKey || event.ctrlKey;
      const key = event.key.toLowerCase();
      if (meta && key === "z") {
        event.preventDefault();
        if (event.shiftKey) this.redo();
        else this.undo();
      } else if (meta && key === "y") {
        event.preventDefault();
        this.redo();
      } else if (meta && (key === "0" || key === ")")) {
        event.preventDefault();
        this.fit();
      } else if (meta && (key === "=" || key === "+")) {
        event.preventDefault();
        this.zoom(1.25);
      } else if (meta && key === "-") {
        event.preventDefault();
        this.zoom(0.8);
      }
    });
  }

  // ------------------------------------------------------------ 顶栏

  bindHead() {
    if (role() === "ipad" || EMBED) {
      document.getElementById("wb-head").remove();
      if (EMBED) setInterval(() => this.showPage(), 250);
      return;
    }
    const back = document.getElementById("wb-back");
    back.innerHTML = icon("back");
    if (FOLLOW) back.hidden = true;               // the iPad only writes; the Mac runs the manager
    document.getElementById("wb-export").addEventListener("click", () => this.openExport());
    setInterval(() => this.showPage(), 250);
  }

  showMeta(meta) {
    this.meta = meta;
    const set = meta.data && meta.data.set;
    document.title = meta.name || "白板";
    this.page = -1;
    if (!document.getElementById("wb-head")) {
      if (EMBED) this.showPage();
      return;
    }
    document.getElementById("wb-name").textContent = meta.name || "";
    if (set) document.getElementById("wb-back").href = `/#/sets/${set}`;
    this.showPage();
  }

  /** 视口中央所在的那一页:题号与页码。 */
  showPage() {
    const layers = (this.state && this.state.layers) || [];
    if (!layers.length || !this.renderer) return;
    const v = this.viewport;
    const cy = (this.renderer.viewH / 2 - v.y) / v.scale;
    let n = 0;
    for (let i = 0; i < layers.length; i++) if (cy >= layers[i].y - 12) n = i;
    if (n === this.page) return;
    this.page = n;
    const labels = (this.meta && this.meta.data && this.meta.data.labels) || [];
    if (EMBED) {
      parent.postMessage({ type: "wb-page", label: labels[n] || "", page: n + 1, pages: layers.length }, location.origin);
      return;
    }
    document.getElementById("wb-label").textContent = labels[n] || "";
    document.getElementById("wb-page").textContent = `${n + 1} / ${layers.length}`;
  }

  // ------------------------------------------------------------ 导出

  openExport() {
    if (this.exportDialog) return;
    const name = el("input", { type: "text", value: `${(this.meta && this.meta.name) || "题组"} 批注版`.replace(/\//g, "-") });
    const scheme = el("input", { type: "checkbox" });
    const explain = el("input", { type: "checkbox" });
    const go = el("button", { class: "btn primary", type: "button" }, "导出批注版");
    const sync = () => {
      go.textContent = scheme.checked || explain.checked ? "导出 ZIP" : "导出批注版";
    };
    scheme.addEventListener("change", sync);
    explain.addEventListener("change", sync);
    const close = () => {
      scrim.remove();
      this.exportDialog = null;
    };
    const cancel = el("button", { class: "btn", type: "button", onclick: close }, "取消");
    go.addEventListener("click", async () => {
      go.disabled = true;
      try {
        await this.persist();
        const r = await fetch(`/api/boards/${this.state.id}/export`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ name: name.value, scheme: scheme.checked, explanation: explain.checked }),
        });
        if (!r.ok) throw new Error((await r.text()) || r.statusText);
        const blob = await r.blob();
        const disp = r.headers.get("Content-Disposition") || "";
        const m = disp.match(/filename\*=UTF-8''([^;]+)/);
        const a = el("a", { href: URL.createObjectURL(blob), download: m ? decodeURIComponent(m[1]) : "批注版.pdf" });
        document.body.append(a);
        a.click();
        a.remove();
        setTimeout(() => URL.revokeObjectURL(a.href), 2000);
        close();
        this.ui.toast("check");
      } catch (err) {
        go.disabled = false;
        this.ui.message(`批注版无法导出（${String(err.message || err).slice(0, 80)}）`, "close", 6000);
      }
    });
    const dialog = el("div", { class: "wb-export", role: "dialog" }, [
      el("h2", {}, "导出批注版"),
      el("label", { class: "field" }, ["文件名", el("div", { class: "name" }, [name, el("span", {}, ".pdf")])]),
      el("div", { class: "checks" }, [
        el("label", {}, [scheme, "评分细则"]),
        el("label", {}, [explain, "详解"]),
      ]),
      el("div", { class: "actions" }, [cancel, go]),
    ]);
    const scrim = el("div", { class: "scrim", onclick: (e) => { if (e.target === scrim) close(); } }, [dialog]);
    this.ui.root.append(scrim);
    this.exportDialog = scrim;
    name.focus();
  }
}

window.whiteboard = new Writer();
