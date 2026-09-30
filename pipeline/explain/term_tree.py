#!/usr/bin/env python3
"""Key terms to memorise, chosen and ranked by counting, as an Obsidian vault.

    python3 pipeline/explain/term_tree.py [--syllabus 9618] [--out DIR]

The explanations (explain_batches.py) list "key terms" per part, but the
subagents that wrote them cannot tell a concept to be learnt by heart from
a word the question happens to use (function, array, record). Here their
lists, together with the syllabus' own "use the terms ..." lists, are only
the pool of candidates; whether a candidate is kept, how important it is and
what it means are all taken from the bank itself:

- occurrences   a candidate occurs in a part when it appears, as a word, in
                the part's question text or its rows of the mark scheme.
                Parts are split by the task of split_parts.py: explain
                ("describe", "state", "explain") against code (write_code,
                complete_code, trace, sql, assembly).
- kept          it occurs in at least 2 explain parts, of at least 2 papers,
                and no more than half of its occurrences are in code parts
                (those are programming vocabulary, not definitions).
- level         by the number of papers with an explain part on it:
                ★★★ 必背 (top fifth), ★★ 常考 (next two fifths), ★ 了解.
- definition    the scheme row that names it and shares the most words with
                the other rows that name it (the medoid): the examiners' own
                wording, not a paraphrase. Key words: the content words that
                occur in at least 40% of those rows.
- subsection    the syllabus subsection the explanations tag it with most
                often, within the section most of its parts belong to.
- parent        the candidate or shared head word it ends with ("foreign
                key" -> "key"); a head word shared by 3 or more kept terms
                becomes a hub note of its own.
- confusable    two kept terms named together in the question text of at
                least one part that asks for a difference ("difference",
                "compare", "distinguish", "why ... rather than"), or with
                the same head and opposed modifiers (lossy / lossless,
                static / dynamic). Each note links the other and quotes the
                scheme rows of those parts as the difference.

Writes an Obsidian vault to exports/<syllabus>_terms/ (paths.EXPORTS):
    00 索引.md                    sections and subsections, terms by level
    <section code> <name>.md      one note per subsection, its terms
    terms/<term>.md               frontmatter (level, subsection, counts),
                                  definition, key words, [[parent]],
                                  [[children]], [[confusable]] with the
                                  difference, example question ids
and terms.json with the same data.
"""
import argparse, json, os, re, shutil, sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))
from lib import db, paths  # noqa: E402

CODE_TASKS = {"write_code", "complete_code", "trace", "sql", "assembly"}
CONTRAST = re.compile(r"difference|differ|distinguish|compare|contrast|rather than|instead of"
                      r"|advantages? of .* over", re.I)
STOP = set("""a an the of to and or in on for by with is are be as it its this that
these those from at which can one each any all not no more than into when used use
using will may must e.g eg i.e ie etc per only also has have so such their there data
mark marks one two""".split())
OPPOSED = [("lossy", "lossless"), ("static", "dynamic"), ("primary", "secondary"),
           ("serial", "parallel"), ("simplex", "duplex"), ("half-duplex", "full-duplex"),
           ("public", "private"), ("symmetric", "asymmetric"), ("internal", "external"),
           ("volatile", "non-volatile"), ("local", "global"), ("black-box", "white-box"),
           ("input", "output"), ("logical", "arithmetic"), ("compiler", "interpreter"),
           ("sram", "dram"), ("ram", "rom"), ("cisc", "risc"), ("lan", "wan"),
           ("bitmap", "vector"), ("analogue", "digital"), ("high-level", "low-level"),
           ("absolute", "relative"), ("direct", "indirect"), ("stack", "queue"),
           ("inner", "outer"), ("by value", "by reference"), ("verification", "validation")]
LEVELS = [("★★★", "必背"), ("★★", "常考"), ("★", "了解")]


def norm(term):
    t = re.sub(r"[^a-z0-9+#/ -]", "", term.lower().replace("’", "'").replace("'", ""))
    t = re.sub(r"\s+", " ", t).strip()
    if len(t) > 4 and t.endswith("ies"):
        t = t[:-3] + "y"
    elif len(t) > 3 and t.endswith("s") and not t.endswith(("ss", "us", "is", "os")):
        t = t[:-1]
    return t


def pattern(term):
    """Word-boundary regex for a normalised term, plural and hyphen/space tolerant."""
    words = [re.escape(w) for w in re.split(r"[ -]", term)]
    body = r"[\s-]+".join(words)
    return re.compile(rf"(?<![a-z0-9]){body}(?:s|es)?(?![a-z0-9])", re.I)


def words(text):
    return {w for w in re.findall(r"[a-z][a-z0-9'-]+", text.lower()) if w not in STOP}


def rows_of(ms):
    """Scheme rows: bullets and table cells, stripped of marks and codes."""
    out = []
    for line in re.split(r"\n|•", ms or ""):
        line = re.sub(r"\|\s*\d+\s*$|\|\s*[BMA]\d\s*", "", line)
        line = re.sub(r"^\s*\d+(\([a-z]+\))*\s*", "", line).strip(" |-–")
        if len(line) >= 12 and not re.fullmatch(r"(One|1) marks? .*", line, re.I):
            out.append(line)
    return out


def candidates(con, syllabus, spec):
    """{normalised term: {display names, subsection votes}} from the explanations
    and the syllabus' term lists; nothing about importance is taken from them."""
    cand = defaultdict(lambda: {"names": Counter(), "subs": Counter()})
    for (raw,) in con.execute("SELECT explanation FROM questions WHERE syllabus=? "
                              "AND explanation IS NOT NULL", (syllabus,)):
        for part in json.loads(raw)["parts"]:
            for t in part.get("terms") or []:
                k = norm(t.get("term") or "")
                if 2 < len(k) < 50:
                    cand[k]["names"][t["term"].strip()] += 1
                    cand[k]["subs"][t.get("topic")] += 1
    for code, v in spec.items():
        for note in v.get("notes", []) + v.get("outcomes", []):
            m = re.search(r"\bthe terms?\s*:?\s*(.+)", note, re.I)
            if m:
                for t in re.split(r",|;|\band\b|/", m.group(1)):
                    k = norm(t.strip(" .()"))
                    if 2 < len(k) < 50:
                        cand[k]["names"][t.strip(" .()")] += 1
                        cand[k]["subs"][code] += 3
    return cand


def count(con, syllabus, cand):
    parts = []
    for qid, series, pd in con.execute(
            "SELECT id, series || '_' || component || variant, part_data FROM questions "
            "WHERE syllabus=? AND part_data IS NOT NULL ORDER BY id", (syllabus,)):
        for p in json.loads(pd)["parts"] or []:
            kind = "code" if p.get("task") in CODE_TASKS else (
                "explain" if p.get("task") == "explain" else "other")
            parts.append({"qid": qid, "paper": series, "label": p["label"], "kind": kind,
                          "section": str(p.get("topic") or "").split(".")[0],
                          "q": p.get("text") or "", "ms": p.get("ms") or ""})
    stats = {}
    for k in cand:
        rx = pattern(k)
        st = {"explain": [], "code": 0, "other": 0, "rows": [], "sections": Counter()}
        for i, p in enumerate(parts):
            in_q, in_ms = bool(rx.search(p["q"])), bool(rx.search(p["ms"]))
            if not (in_q or in_ms):
                continue
            if p["kind"] == "code":
                st["code"] += 1
            elif p["kind"] == "explain":
                st["explain"].append(i)
                st["sections"][p["section"]] += 1
                st["rows"] += [r for r in rows_of(p["ms"]) if rx.search(r)]
            else:
                st["other"] += 1
        stats[k] = st
    return parts, stats


def medoid(rows):
    if not rows:
        return "", []
    ws = [words(r) for r in rows]
    def score(i):
        return sum(len(ws[i] & w) / (len(ws[i] | w) or 1) for j, w in enumerate(ws) if j != i)
    best = max(range(len(rows)), key=lambda i: (score(i), -len(rows[i])))
    freq = Counter(w for s in ws for w in s)
    keys = [w for w, n in freq.most_common(12) if n >= max(2, 0.4 * len(rows))][:6]
    return rows[best], keys


def build(con, syllabus, spec):
    cand = candidates(con, syllabus, spec)
    parts, stats = count(con, syllabus, cand)
    kept = {}
    for k, st in stats.items():
        papers = {parts[i]["paper"] for i in st["explain"]}
        n_exp = len(st["explain"])
        if n_exp < 2 or len(papers) < 2 or st["code"] > n_exp:
            continue
        section = st["sections"].most_common(1)[0][0] if st["sections"] else ""
        subs = [s for s, _ in cand[k]["subs"].most_common() if s and s.split(".")[0] == section]
        sub = subs[0] if subs else (cand[k]["subs"].most_common(1)[0][0] or section)
        definition, keys = medoid(st["rows"])
        kept[k] = {"term": cand[k]["names"].most_common(1)[0][0], "key": k,
                   "papers": len(papers), "explain_parts": n_exp, "code_parts": st["code"],
                   "subsection": sub, "definition": definition,
                   "keywords": [w for w in keys if w not in k.split()],
                   "examples": sorted({parts[i]["qid"] for i in st["explain"]})[:5]}
    # levels by the spread over papers: top fifth, next two fifths, the rest
    ranked = sorted(kept.values(), key=lambda t: -t["papers"])
    for i, t in enumerate(ranked):
        t["level"] = 0 if i < len(ranked) / 5 else (1 if i < 3 * len(ranked) / 5 else 2)
    # parents: the longest kept term or shared head word the term ends with
    heads = Counter(k.split()[-1] for k in kept if " " in k)
    for k, t in kept.items():
        ws = k.split()
        parent = next((" ".join(ws[i:]) for i in range(1, len(ws)) if " ".join(ws[i:]) in kept), None)
        if not parent and len(ws) > 1 and heads[ws[-1]] >= 3:
            parent = ws[-1]
        t["parent"] = parent
    hubs = {t["parent"] for t in kept.values() if t["parent"] and t["parent"] not in kept}
    # confusable pairs
    pairs = defaultdict(list)
    keys = list(kept)
    rx = {k: pattern(k) for k in keys}
    for i, p in enumerate(parts):
        if not CONTRAST.search(p["q"]):
            continue
        named = [k for k in keys if rx[k].search(p["q"])]
        named = [k for k in named if not any(k != o and k in o for o in named)]
        for a in named:
            for b in named:
                if a < b:
                    pairs[(a, b)].append(i)
    for a in keys:
        for x, y in OPPOSED:
            b = re.sub(rf"(^| ){re.escape(x)}( |$)", rf"\g<1>{y}\2", a)
            if b != a and b in kept and (a, b) not in pairs and (b, a) not in pairs:
                pairs[tuple(sorted((a, b)))] = []
    for (a, b), idx in pairs.items():
        diff = []
        for i in idx:
            diff += [r for r in rows_of(parts[i]["ms"]) if rx[a].search(r) or rx[b].search(r)]
        diff = list(dict.fromkeys(diff))[:4]
        src = sorted({f"{parts[i]['qid']} ({parts[i]['label']})" for i in idx})[:3]
        for x, y in ((a, b), (b, a)):
            kept[x].setdefault("confusable", []).append(
                {"with": y, "difference": diff, "from": src})
    return kept, hubs


def fname(term):
    return re.sub(r'[\\/:*?"<>|#^\[\]]', "-", term)


def write_vault(out, syllabus, spec, kept, hubs):
    if os.path.isdir(out):
        shutil.rmtree(out)
    os.makedirs(os.path.join(out, "terms"))
    title = {k: kept[k]["term"] for k in kept}
    link = lambda k: f"[[{fname(title.get(k, k))}]]"
    children = defaultdict(list)
    for k, t in kept.items():
        if t["parent"]:
            children[t["parent"]].append(k)
    for k, t in kept.items():
        star, word = LEVELS[t["level"]]
        sub = t["subsection"]
        sub_name = spec.get(sub, {}).get("name", "")
        lines = ["---", f"level: {star}", f"tags: [级别/{word}, 小节/{sub}]",
                 f"subsection: \"{sub} {sub_name}\"", f"papers: {t['papers']}",
                 f"explain_parts: {t['explain_parts']}", "---", "",
                 f"# {t['term']}  {star}", "",
                 f"小节:[[{fname(sub + ' ' + sub_name)}]]", ""]
        if t["parent"]:
            lines.append(f"上级:{link(t['parent'])}")
        if children.get(k):
            lines.append("下级:" + ",".join(link(c) for c in sorted(children[k])))
        lines += ["", "## 评分细则中的表述", "", f"> {t['definition'] or '(细则中没有单独解释这个词的行)'}", ""]
        if t["keywords"]:
            lines += ["得分关键词:" + ", ".join(f"`{w}`" for w in t["keywords"]), ""]
        for c in t.get("confusable", []):
            lines += [f"## 易混:{link(c['with'])}", ""]
            if c["difference"]:
                lines += ["评分细则中的区别:", ""] + [f"- {d}" for d in c["difference"]]
                lines += ["", f"出处:{', '.join(c['from'])}", ""]
            else:
                other = kept[c["with"]]
                lines += [f"- **{t['term']}**:{t['definition']}",
                          f"- **{other['term']}**:{other['definition']}", ""]
        lines += ["## 例题", "", ", ".join(t["examples"]), ""]
        open(os.path.join(out, "terms", fname(t["term"]) + ".md"), "w").write("\n".join(lines))
    for h in hubs:
        kids = sorted(children[h])
        open(os.path.join(out, "terms", fname(h) + ".md"), "w").write(
            f"# {h}\n\n共用中心词的术语:\n\n" + "\n".join(f"- {link(c)}" for c in kids) + "\n")
    by_sub = defaultdict(list)
    for k, t in kept.items():
        by_sub[t["subsection"]].append(t)
    order = lambda c: [int(x) for x in c.split(".") if x.isdigit()]
    index = [f"# {syllabus} 关键术语", "",
             "术语与级别由题库统计得出:级别按在多少份试卷的解释类小问中出现分档,"
             "★★★ 必背为前五分之一,★★ 常考为其后五分之二,★ 了解为其余。", ""]
    for sub in sorted(by_sub, key=order):
        name = spec.get(sub, {}).get("name", "")
        items = sorted(by_sub[sub], key=lambda t: (t["level"], -t["papers"], t["term"]))
        note = [f"# {sub} {name}", ""]
        for lvl, (star, word) in enumerate(LEVELS):
            group = [t for t in items if t["level"] == lvl]
            if group:
                note += [f"## {star} {word}", ""] + [f"- [[{fname(t['term'])}]]" for t in group] + [""]
        open(os.path.join(out, fname(f"{sub} {name}") + ".md"), "w").write("\n".join(note))
        index.append(f"- [[{fname(sub + ' ' + name)}]]:"
                     + " ".join(f"{LEVELS[l][0]}×{sum(1 for t in items if t['level'] == l)}"
                                for l in range(3)))
    open(os.path.join(out, "00 索引.md"), "w").write("\n".join(index) + "\n")
    json.dump(sorted(kept.values(), key=lambda t: (t["subsection"], t["level"])),
              open(os.path.join(out, "terms.json"), "w"), ensure_ascii=False, indent=1)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--syllabus", default="9618")
    ap.add_argument("--out")
    a = ap.parse_args()
    spec = json.load(open(paths.SYLLABUS))[a.syllabus]["topics"]
    con = db.connect()
    kept, hubs = build(con, a.syllabus, spec)
    out = a.out or os.path.join(paths.EXPORTS, f"{a.syllabus}_terms")
    write_vault(out, a.syllabus, spec, kept, hubs)
    lv = Counter(t["level"] for t in kept.values())
    conf = sum(len(t.get("confusable", [])) for t in kept.values()) // 2
    print(f"候选 {len(candidates(con, a.syllabus, spec))},保留 {len(kept)} 个术语"
          f"(" + ",".join(f"{LEVELS[l][1]} {lv[l]}" for l in range(3)) + f"),"
          f"中心词汇总 {len(hubs)},易混 {conf} 对 -> {out}")


if __name__ == "__main__":
    main()
