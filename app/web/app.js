// AL Question Bank:总览、练习、复盘三个视图,和顶栏的考试切换与跳转。
// 手写板按 inksync 的接口使用;服务端没装 inksync 时提供同接口的替身。
// 静态预览(app/preview.py)在载入本文件之前设置 window.QB_API 和 window.QB_INKPAD。
import { put, h, $, icon, api, saved, remember, EXAMS, isCaie } from "./js/core.js";
import { overview } from "./js/overview.js";
import { workspace } from "./js/workspace.js";
import { review } from "./js/review.js";
import { palette } from "./js/palette.js";

const { createInkPad } = await import(window.QB_INKPAD || "/inksync/inkpad.js");

const app = {
  exam: null, filters: {}, lists: {}, question: null, view: null, saved, remember,

  async setExam(exam) {
    if (!app.filters[exam]) return;
    app.exam = exam;
    remember({ exam });
    drawExams();
    await app.refreshList();
    if (app.view === "work") {
      const rows = app.lists[exam];
      const last = rows.find((r) => r.id === saved.qidBy?.[exam]) || rows.find((r) => r.avail !== false);
      if (last) await work.open(last.id, { kind: "paper" });
    }
    show(app.view);
  },

  async refreshList() {
    app.lists[app.exam] = await api(`/api/questions?syllabus=${encodeURIComponent(app.exam)}`);
    if (app.view === "work") work.refresh();
  },

  async open(qid, opts = {}) {
    show("work");
    await work.open(qid, opts);
    remember({ qidBy: { ...(saved.qidBy || {}), [app.exam]: qid } });
  },

  practiseTopic(code) {
    const first = app.lists[app.exam].filter((r) => r.topic === code && r.avail !== false)
      .sort((a, b) => b.year - a.year || a.q - b.q)[0];
    if (first) app.open(first.id, { kind: "topic" });
  },

  sync(status) { $("#sync").className = `sync ${status || ""}`; },
};

const views = {
  overview: overview(app),
  work: workspace(app, createInkPad),
  review: review(app),
};
const work = views.work;
$("#v-overview").append(views.overview.root);
$("#v-work").append(views.work.root);
$("#v-review").append(views.review.root);

const VIEW_TABS = [["overview", "wall", "总览"], ["work", "pen", "练习"], ["review", "ledger", "复盘"]];

function show(view) {
  const run = () => {
    app.view = view;
    remember({ view });
    for (const [v] of VIEW_TABS) $(`#v-${v}`).hidden = v !== view;
    for (const b of $("#views").children) b.classList.toggle("on", b.dataset.v === view);
    if (view === "overview") views.overview.render();
    if (view === "review") views.review.render();
  };
  if (document.startViewTransition && app.view && app.view !== view) document.startViewTransition(run);
  else run();
}

function drawExams() {
  const nav = $("#exams");
  put(nav, ...EXAMS.filter((e) => app.filters[e]).flatMap((e, i, all) => [
    i && isCaie(all[i - 1]) && !isCaie(e) ? h("span.gap") : null,
    h(`button${e === app.exam ? ".on" : ""}`, { title: app.filters[e].name, on: { click: () => app.setExam(e) } }, e),
  ]));
}

function drawChrome() {
  put($("#views"), ...VIEW_TABS.map(([v, ic, label]) => h("button", {
    "data-v": v, html: icon(ic), on: { click: async () => {
      if (v === "work" && !work.question) {
        const rows = app.lists[app.exam];
        const first = rows.find((r) => r.id === saved.qidBy?.[app.exam]) || rows.find((r) => r.avail !== false);
        if (first) return app.open(first.id, { kind: "paper" });
      }
      show(v);
    } },
  }, h("span", label))));
  const pal = palette(app);
  put($("#find"), h("span", { html: icon("search"), style: { display: "contents" } }), h("span", "跳到题目"), h("kbd", "⌘K"));
  $("#find").addEventListener("click", () => pal.open());
  $(".brand").addEventListener("click", (e) => { e.preventDefault(); show("overview"); });
}

(async () => {
  app.filters = await api("/api/filters");
  app.exam = app.filters[saved.exam] ? saved.exam : "9709";
  drawChrome();
  drawExams();
  await app.refreshList();
  const view = saved.view || "overview";
  if (view === "work") {
    const rows = app.lists[app.exam];
    const last = rows.find((r) => r.id === (saved.qidBy?.[app.exam] || saved.qid)) || rows.find((r) => r.avail !== false);
    if (last) return app.open(last.id, { kind: "paper" });
  }
  show(view === "work" ? "overview" : view);
})();
