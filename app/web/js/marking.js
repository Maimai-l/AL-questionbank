// 判分:按评分细则逐项给分,样子照阅卷人的红笔。
//
//   codes   9709 / 9231:细则每行的 M1 A1 B1 各是一个可点的分码;A 依赖它前面的 M,
//           DM 依赖前面的 *M,前提没给分时后面的锁住。B2,1,0 这类给出几档可选。
//   points  9618:详解里的得分点,每点一个,小问合计不超过它的分值。
//   choice  入学考:选项与答案,选完即判。
//   score   细则没有可点的分码时,直接填分。
import { put, h, icon, esc, tex } from "./core.js";

export function marking(onChange) {
  const body = h("div.mark");
  let q = null, prior = {}, readonly = false;
  let picks = [];           // 每个小问:{ticks: [value|null]} | {choice} | {score}

  function render(question, attempt, ro) {
    q = question;
    prior = attempt?.marks || {};
    readonly = ro;
    picks = q.parts.map((p) => {
      const got = prior[p.label] || {};
      if (p.kind === "codes" || p.kind === "points") {
        return { ticks: p.items.map((_, i) => got.ticks?.[i] ?? null) };
      }
      if (p.kind === "choice") return { choice: got.choice || null };
      return { score: got.score ?? null };
    });
    put(body, ...q.parts.map((p, pi) => part(p, pi)));
    const whole = q.scheme && !q.parts.some((p) => p.ms) && q.parts[0]?.kind !== "choice";
    if (whole) body.append(h("div.part", h("div.part-h", h("span.lab", "评分细则"), schemeToggle(q.scheme))));
    tex(body);
    sync();
  }

  function schemeToggle(text) {
    const box = h("div.scheme", { hidden: true }, text);
    const b = h("button.ib", {
      title: "评分细则原文", "aria-label": "评分细则原文", html: icon("doc"),
      on: { click: () => { box.hidden = !box.hidden; b.classList.toggle("on", !box.hidden); } },
    });
    return [b, box];
  }

  function part(p, pi) {
    const [toggle, box] = p.ms ? schemeToggle(p.ms) : [null, null];
    const head = h("div.part-h",
      h("span.lab", p.label ? `(${p.label})` : `Q${q.q}`),
      h("span.tf", p.kind === "choice" ? "" : `[${p.marks ?? "?"}]`),
      toggle,
      h(`span.sub.num`, { "data-sub": pi }));
    let rows;
    if (p.kind === "codes" || p.kind === "points") {
      rows = p.items.map((it, ii) => itemRow(p, pi, it, ii));
    } else if (p.kind === "choice") {
      rows = [choice(p, pi)];
    } else {
      const input = h("input", {
        type: "number", min: 0, max: p.marks ?? 99, step: 1, inputmode: "numeric",
        value: picks[pi].score ?? "", disabled: readonly,
        on: { input: (e) => { picks[pi].score = e.target.value === "" ? null : Math.min(Number(e.target.value), p.marks ?? 99); sync(); } },
      });
      rows = [h("label.manual", input, h("span.muted", `/ ${p.marks ?? "?"}`))];
    }
    return h("div.part", head, box, rows);
  }

  function itemRow(p, pi, it, ii) {
    const values = [it.value, ...(it.partial || [])].filter((v) => v > 0);
    const chips = values.map((v) => {
      const label = values.length > 1 ? `${it.code.replace(/[\d,].*$/, "")}${v}` : (p.kind === "points" ? `[${it.code}]` : it.code);
      return h("button.chip", {
        "data-p": pi, "data-i": ii, "data-v": v, disabled: readonly,
        title: it.guidance || "",
        html: icon("tick") + esc(label),
        on: { click: () => { picks[pi].ticks[ii] = picks[pi].ticks[ii] === v ? null : v; sync(); } },
      });
    });
    return h("div.mrow", { "data-p": pi, "data-i": ii },
      values.length > 1 ? h("span.chip-vals", chips) : chips[0],
      h("div.ans", { html: esc(it.answer) }),
      it.guidance && p.kind !== "points" ? h("div.gd", it.guidance) : null);
  }

  function choice(p, pi) {
    const letters = p.options ? Object.keys(p.options) : ["A", "B", "C", "D", "E"];
    return h("div.opts", letters.map((l) => h("button.opt", {
      "data-p": pi, "data-c": l, disabled: readonly,
      on: { click: () => { if (!readonly) { picks[pi].choice = l; sync(); } } },
    }, h("b", l), h("span", { html: p.options ? esc(p.options[l]) : "" }))));
  }

  // 依赖、显示与合计
  function sync() {
    let score = 0, max = 0;
    q.parts.forEach((p, pi) => {
      const pk = picks[pi];
      let got = 0;
      if (p.kind === "codes" || p.kind === "points") {
        p.items.forEach((it, ii) => {
          const dep = it.depends;
          const ok = dep == null || pk.ticks[dep] != null;
          if (!ok) pk.ticks[ii] = null;
          const row = body.querySelector(`.mrow[data-p="${pi}"][data-i="${ii}"]`);
          row?.classList.toggle("locked", !ok);
          for (const c of row?.querySelectorAll(".chip") || []) c.classList.toggle("got", Number(c.dataset.v) === pk.ticks[ii]);
        });
        got = Math.min(pk.ticks.reduce((s, v) => s + (v || 0), 0), p.marks ?? Infinity);
      } else if (p.kind === "choice") {
        for (const b of body.querySelectorAll(`.opt[data-p="${pi}"]`)) {
          b.classList.toggle("right", !!pk.choice && b.dataset.c === p.answer);
          b.classList.toggle("wrong", !!pk.choice && b.dataset.c === pk.choice && pk.choice !== p.answer);
        }
        got = pk.choice && pk.choice === p.answer ? 1 : 0;
      } else {
        got = pk.score || 0;
      }
      const m = p.kind === "choice" ? 1 : p.marks ?? 0;
      score += got;
      max += m;
      const sub = body.querySelector(`[data-sub="${pi}"]`);
      if (sub) {
        const touched = p.kind === "choice" ? !!pk.choice : got > 0;
        sub.textContent = p.kind === "choice" ? "" : `${got}/${m}`;
        sub.classList.toggle("got", touched && got > 0);
      }
    });
    onChange({ score, max });
  }

  function collect() {
    const marks = {};
    let score = 0, max = 0;
    q.parts.forEach((p, pi) => {
      const pk = picks[pi];
      if (p.kind === "codes" || p.kind === "points") {
        const s = Math.min(pk.ticks.reduce((a, v) => a + (v || 0), 0), p.marks ?? Infinity);
        marks[p.label] = { ticks: pk.ticks.slice(), score: s };
        score += s; max += p.marks ?? 0;
      } else if (p.kind === "choice") {
        const ok = pk.choice === p.answer;
        marks[p.label] = { choice: pk.choice, score: ok ? 1 : 0 };
        score += ok ? 1 : 0; max += 1;
      } else {
        marks[p.label] = { score: pk.score || 0 };
        score += pk.score || 0; max += p.marks ?? 0;
      }
    });
    return { marks, score, max };
  }

  return { body, render, collect };
}
