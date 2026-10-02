// 详解:逐个小问的解题思路、得分点、常见失分、参考答案与关键术语。
import { h, icon, esc, tex } from "./core.js";

// 参考答案是 Markdown:代码块、表格、加粗、行内代码、列表
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

export function explain(q) {
  const ex = q.explanation;
  const body = h("div.ex");
  if (!ex) return body;
  for (const p of ex.parts) {
    const marks = q.parts.find((x) => x.label === p.label)?.marks;
    body.append(h("div.part",
      h("div.part-h", h("span.lab", p.label ? `(${p.label})` : `Q${q.q}`), marks ? h("span.tf", `[${marks}]`) : null),
      h("p", { html: inline(p.approach) }),
      (p.points || []).length ? h("ul.pts", p.points.map((x) => h("li",
        h("span.mk", `[${x.mark}]`),
        h("span", { html: inline(x.point) }, h("span.why", { html: inline(x.why) }))))) : null,
      (p.pitfalls || []).map((x) => h("div.pit", { html: icon("alert") + `<span>${inline(x)}</span>` })),
      p.answer ? h("div.answer", { html: md(p.answer) }) : null,
      (p.terms || []).length ? h("div.terms", p.terms.map((t) => h("span", { title: t.wording || "" }, t.term))) : null));
  }
  tex(body);
  return body;
}
