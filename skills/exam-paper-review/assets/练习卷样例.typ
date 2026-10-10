#import "@preview/examy:0.2.0": *

// ================= 配置 =================
#let MODE = sys.inputs.at("mode", default: "paper")   // paper | ms
#let CODE = "9231/TP/PF"
#let SUBJECT = "9231 Further Pure Mathematics 1"
#let TITLE_ZH = "部分分式"
#let TITLE_EN = "Partial Fractions"
#let MINUTES = 45
#let SERIF = ("STIX Two Text", "Noto Sans CJK SC")   // 题目正文：拉丁用 STIX，中文回落到思源黑体
#let SANS = ("Noto Sans CJK SC",)                    // 封面、页眉页脚、说明
#let INK = black
#let MUTED = luma(40%)
#let RULE = luma(75%)

// ================= 方法要点（封面） =================
#let METHODS = (
  (head: [三种分母对应的分解形式], body: [
    $ (p x + q)/((a x + b)(c x + d)) = A/(a x + b) + B/(c x + d) $
    $ (p x^2 + q x + s)/((a x + b)(c x + d)^2) = A/(a x + b) + B/(c x + d) + C/(c x + d)^2 $
    $ (p x^2 + q x + s)/((a x + b)(x^2 + c^2)) = A/(a x + b) + (B x + C)/(x^2 + c^2) $
  ]),
  (head: [假分式先做长除], body: [
    分子次数不低于分母次数时，先写成 $display(f(x) = q(x) + (r(x))/(d(x)))$，再对余式部分分解。
  ]),
  (head: [定系数的顺序], body: [
    先代入每个线性因子的零点，直接求出对应系数；剩余系数用比较 $x^2$ 系数或常数项求出。
  ]),
  (head: [验算], body: [
    取一个不是零点的数（例如 $x = 2$），分别代入原式和分解结果，两边数值必须相等。
  ]),
  (head: [两个常见用途], body: [
    $ integral A/(a x + b) dif x = A/a ln|a x + b| + c #h(2em) 1/(r(r+1)) = 1/r - 1/(r+1) $
  ]),
)

// ================= 题目数据 =================
// space: ("lines", n) | ("blank", 长度) | ("fill",)
#let QS = (
  (num: 1, stem: none, parts: (
    (text: [Express $display((5x + 1)/((x + 1)(x - 1)))$ in partial fractions.], marks: 2, space: ("lines", 5),
     ms: (([$display(2/(x+1) + 3/(x-1))$], [M1 A1]),), note: [M1：代入 $x = plus.minus 1$ 或比较系数。]),
    (text: [Express $display((3x^2 + 3x + 4)/((x + 1)(x^2 + 3)))$ in partial fractions.], marks: 4, space: ("lines", 8),
     ms: (([$display(A/(x+1) + (B x + C)/(x^2+3))$ 的形式], [B1]), ([$A = 1$], [M1 A1]), ([$display(1/(x+1) + (2x+1)/(x^2+3))$], [A1])), note: [B1：二次因子对应分子必须是 $B x + C$。]),
  )),
  (num: 2, newpage: true, stem: none, parts: (
    (text: [Express $display((3x^2 + 3x + 3)/((x + 2)(x - 1)^2))$ in partial fractions.], marks: 5, space: ("lines", 10), single: true,
     ms: (([$display(A/(x+2) + B/(x-1) + C/(x-1)^2)$ 的形式], [B1]), ([$A = 1$，$C = 3$（代入零点）], [M1 A1]), ([$B = 2$（比较 $x^2$ 系数）], [M1 A1])), note: [重复因子漏写 $B/(x-1)$ 项，本题最多得 2 分。]),
  )),
  (num: 3, newpage: true, stem: none, parts: (
    (text: [Express $display((2x^3 + x^2 - 7x + 1)/(x^2 + x - 2))$ in the form $display(p x + q + A/(x + 2) + B/(x - 1))$.], marks: 5, space: ("lines", 9), single: true,
     ms: (([长除得商 $2x - 1$，余式 $-2x - 1$], [M1 A1]), ([对 $display((-2x-1)/((x+2)(x-1)))$ 分解], [M1]), ([$display(2x - 1 - 1/(x+2) - 1/(x-1))$], [A1 A1])), note: [两个分式系数各 A1。]),
  )),
  (num: 4, newpage: true, stem: none, parts: (
    (text: [Express $display(2/(r(r + 1)(r + 2)))$ in partial fractions.], marks: 3, space: ("lines", 6),
     ms: (([$display(1/r - 2/(r+1) + 1/(r+2))$], [M1 A1 A1]),), note: []),
    (text: [Hence show that $display(sum_(r=1)^n 2/(r(r + 1)(r + 2)) = (n(n + 3))/(2(n + 1)(n + 2)))$.], marks: 4, space: ("lines", 10), pagebreak: true,
     ms: (([写出首尾足够多的项并体现抵消], [M1]), ([$display(1/2 - 1/(n+1) + 1/(n+2))$], [A1]), ([通分得到给定结果], [M1 A1])), note: [AG：必须写出通分过程。]),
    (text: [State the value of $display(sum_(r=1)^infinity 2/(r(r + 1)(r + 2)))$.], marks: 1, space: ("lines", 2),
     ms: (([$display(1/2)$], [B1]),), note: []),
  )),
  (num: 5, newpage: true, stem: none, parts: (
    (text: [Show that $display(integral_2^3 (x + 5)/((x - 1)(x + 2)) dif x = ln 16/5)$.], marks: 5, space: ("lines", 11), single: true,
     ms: (([$display(2/(x-1) - 1/(x+2))$], [M1 A1]), ([$[2 ln|x-1| - ln|x+2|]_2^3$], [A1]), ([$2 ln 2 - ln 5 + ln 4$], [M1]), ([$display(= ln 16/5)$], [A1])), note: [AG：最后一步须合并对数。]),
  )),
)

#let TOTAL = QS.map(q => q.parts.map(p => p.marks).sum()).sum()
#let letters = "abcdefgh"

// ================= 页面 =================
#set page(
  paper: "a4",
  margin: (x: 20mm, top: 20mm, bottom: 22mm),
  header: none,
  footer: none,
)
#set text(font: SERIF, size: 11pt, lang: "zh")
#show math.equation: set text(font: "STIX Two Math")
#set par(leading: 0.72em)
#show: e.prepare()

#let mk(n) = box(width: 1fr)[#h(1fr)*\[#n\]*]
#let dots(n, gap: 11mm) = block(breakable: false, width: 100%, {
  for i in range(n) {
    v(gap, weak: false)
    line(length: 100%, stroke: (paint: INK, thickness: 0.5pt, dash: (0.4pt, 2.2pt)))
  }
})
#let space(s) = if s.at(0) == "lines" { dots(s.at(1)) } else if s.at(0) == "blank" {
  block(breakable: false, width: 100%, height: s.at(1))
} else { v(1fr) }

// ================= 封面 =================
#let cover(kind) = {
  set text(font: SANS)
  v(6mm)
  let stat(num, unit) = [#text(size: 17pt, weight: "medium")[#num]#h(1.2mm)#text(size: 9.5pt, fill: MUTED)[#unit]]
  text(size: 9.5pt, fill: MUTED)[#SUBJECT]
  v(4mm)
  grid(columns: (1fr, auto), align: (left + bottom, right + bottom),
    [#text(size: 26pt, weight: "bold")[#TITLE_ZH]#h(4mm)#text(size: 13pt, fill: MUTED)[#if kind == "评分方案" [评分方案] else [#TITLE_EN]]],
    grid(columns: 3, column-gutter: 8mm, stat(QS.len(), "题"), stat(TOTAL, "分"), stat(MINUTES, "分钟")),
  )
  v(5mm)
  line(length: 100%, stroke: 1.2pt + INK)
  v(8mm)

  if kind == "专题练习" {
    text(size: 11pt, weight: "bold")[方法要点]
    v(4mm)
    for (i, m) in METHODS.enumerate() {
      block(width: 100%, breakable: false, inset: (y: 3.5mm), stroke: (bottom: 0.5pt + RULE), grid(
        columns: (8mm, 1fr),
        text(size: 10.5pt, weight: "bold", fill: MUTED)[#(i + 1)],
        {
          text(size: 10.5pt, weight: "bold")[#m.head]
          v(2mm)
          set text(size: 10.5pt, weight: "regular")
          show math.equation.where(block: true): set align(left)
          m.body
        },
      ))
    }


  } else {
    set text(size: 10.5pt)
    [判分符号：M 方法分，A 答案分（依赖对应 M 分），B 独立结论分，AG 答案已给出须完整推导，FT 允许沿用前面的错误结果。]
  }

  pagebreak()
}

// ================= 题目册 =================
#if MODE == "paper" {
  cover("专题练习")
  exam(questions: {
    for q in QS {
      if q.at("newpage", default: false) { pagebreak() }
      if q.parts.len() == 1 and q.parts.first().at("single", default: false) {
        let p = q.parts.first()
        question(number: [*#q.num*])[#p.text #mk(p.marks) #space(p.space)]
      } else {
        question(number: [*#q.num*])[
          #if q.stem != none [#q.stem]
          #for p in q.parts {
            if p.at("pagebreak", default: false) { pagebreak() }
            part[#p.text #mk(p.marks) #space(p.space)]
          }
        ]
      }
    }
  })
}

// ================= 评分方案 =================
#if MODE == "ms" {
  cover("评分方案")
  set text(size: 10pt)
  table(
    columns: (16mm, 1fr, 22mm, 48mm),
    stroke: 0.5pt + luma(60%),
    inset: (x: 6pt, y: 8pt),
    align: (x, y) => if x == 2 { center + horizon } else { left + horizon },
    table.header(..("题号", "答案", "分值", "说明").map(h => text(font: SANS, weight: "bold", size: 9pt, h))),
    ..QS.map(q => q.parts.enumerate().map(((i, p)) => {
      let n = p.ms.len()
      let label = if q.parts.len() == 1 and p.at("single", default: false) [#q.num] else [#q.num\(#letters.at(i))]
      p.ms.enumerate().map(((j, row)) => {
        let cells = ()
        if j == 0 { cells.push(table.cell(rowspan: n, align: top, label)) }
        cells.push(row.at(0))
        cells.push(row.at(1))
        if j == 0 { cells.push(table.cell(rowspan: n, align: top, text(font: SANS, size: 8.5pt, p.note))) }
        cells
      })
    })).flatten(),
  )
}
