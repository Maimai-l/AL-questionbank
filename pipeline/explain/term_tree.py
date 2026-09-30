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
- kept          it occurs in at least 2 explain parts, of at least 2 papers;
                no more than half of its occurrences are in code parts
                (those are programming vocabulary, not definitions); the
                other subjects' questions (TSA / BMAT passages, 9709 / 9231)
                do not name it nearly as often (a word they use is general
                English); and a single word is not spread over the syllabus
                (its commonest section holds at least 30% of its parts:
                file, design, update, date are not).
- level         by the number of papers with an explain part on it:
                ★★★ 必背 (top fifth), ★★ 常考 (next two fifths), ★ 了解.
- definition    the scheme rows filed under it as a heading ("Pixel:" and its
                bullets, "RAM – ..."), the rows that open with it ("A pixel
                is ..."), and all scheme rows of the parts whose question asks
                what it is ("what is meant by", "define", "what is a" in the
                sentence that names it); table rows are left out. The row sharing the most words with the others (the
                medoid) is the examiners' own wording, not a paraphrase. Key
                words: the content words in at least 40% of those rows.
- subsection    the syllabus subsection the explanations tag it with most
                often, within the section most of its parts belong to.
- merged        an acronym and its expansion (sram / static ram, lan / local
                area network) are one note, the acronym as an alias.
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

ASK = re.compile(r"meant by|meaning of|\bdefin|what is (?:a|an)\b|what are\b", re.I)
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
        line = re.sub(r"^(MP|P)\d+\s*", "", line)
        if line.count("|") >= 2:                 # a row of a table, not a sentence
            continue
        if len(line) >= 12 and not re.fullmatch(r"(One|1) marks? .*", line, re.I):
            out.append(line)
    return out


def blocks(ms, rx):
    """Rows the scheme files under the term as a heading: "Pixel:" or "Pixel"
    on its own line, then its bullets up to the next short heading; and the
    text after "Pixel:" / "Pixel –" on the same line."""
    out, take = [], 0
    for line in re.split(r"\n", ms or ""):
        raw = re.sub(r"^\s*\d+(\([a-z]+\))*\s*", "", line).strip(" |")
        head = re.match(rf"^(?:an?|the)?\s*{rx.pattern}\s*(?:\([^)]*\))?\s*[:–-]?\s*(.*)$", raw, re.I)
        if head:
            rest = head.group(1).strip(" •|")
            if len(rest) >= 12:
                out.append(rest)
            take = 3
            continue
        if take and raw and len(raw) < 30 and raw.rstrip().endswith(":"):
            take = 0                              # the next heading
            continue
        if take and len(raw) >= 12:
            out += rows_of(raw)
            take -= 1
    return out


def defining(rows, term):
    """Rows that say something about the term: three content words besides it."""
    own = set(re.split(r"[ -]", term))
    return [r for r in rows if len(words(r) - own) >= 3]


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


def background(con, syllabus, cand):
    """{term: share of the other subjects' questions (text and scheme) naming it}.
    TSA and BMAT passages are general English, 9709 / 9231 general mathematics:
    a word they use as often as this subject does is not a term of it."""
    docs = [((a or "") + " " + (b or "")).lower() for a, b in con.execute(
        "SELECT COALESCE(question_latex, question_text), COALESCE(ms_text, ms_latex) "
        "FROM questions WHERE syllabus != ?", (syllabus,))]
    out = {}
    for k in cand:
        rx, first = pattern(k), re.split(r"[ -]", k)[0]
        out[k] = sum(1 for d in docs if first in d and rx.search(d)) / len(docs)
    return out


def count(con, syllabus, cand):
    parts = []
    for qid, series, pd in con.execute(
            "SELECT id, series || '_' || component || variant, part_data FROM questions "
            "WHERE syllabus=? AND part_data IS NOT NULL ORDER BY id", (syllabus,)):
        for p in json.loads(pd)["parts"] or []:
            kind = "code" if p.get("task") in CODE_TASKS else (
                "explain" if p.get("task") == "explain" else "other")
            parts.append({"qid": qid, "paper": series, "label": p["label"], "kind": kind,
                          "all": ((p.get("text") or "") + " " + (p.get("ms") or "")).lower(),
                          "section": str(p.get("topic") or "").split(".")[0],
                          "q": p.get("text") or "", "ms": p.get("ms") or ""})
    stats = {}
    for k in cand:
        rx, first = pattern(k), re.split(r"[ -]", k)[0]
        st = {"explain": [], "code": 0, "other": 0, "rows": [], "sections": Counter(),
              "any": 0}
        for i, p in enumerate(parts):
            if first not in p["all"]:
                continue
            in_q, in_ms = bool(rx.search(p["q"])), bool(rx.search(p["ms"]))
            if not (in_q or in_ms):
                continue
            st["any"] += 1
            if p["kind"] != "code" and in_ms:
                st.setdefault("block_rows", []).extend(blocks(p["ms"], rx))
            if p["kind"] == "code":
                st["code"] += 1
            elif p["kind"] == "explain":
                st["explain"].append(i)
                st["sections"][p["section"]] += 1
                lead = re.compile(rf"^(?:an?|the)?\s*{rx.pattern}\s*(?:\(\w+\)\s*)?(?:is|are|means|:|–|-)\s", re.I)
                st["rows"] += [r for r in rows_of(p["ms"]) if lead.search(r)]
                st.setdefault("mention", []).extend(r for r in rows_of(p["ms"]) if rx.search(r))
                # a part that asks about the term: its scheme rows define it,
                # whether or not they repeat its name
                if any(rx.search(sn) and ASK.search(sn)
                       for sn in re.split(r"(?<=[.?!])\s+|\n", p["q"])):
                    st.setdefault("asked", []).append(i)
                    st.setdefault("asked_rows", []).extend(rows_of(p["ms"]))
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


def top_rows(rows, n=2):
    """The n rows sharing the most words with the others, for a term the scheme
    never defines: how the examiners use it."""
    rows = list(dict.fromkeys(rows))
    ws = [words(r) for r in rows]
    score = lambda i: sum(len(ws[i] & w) / (len(ws[i] | w) or 1) for j, w in enumerate(ws) if j != i)
    return [rows[i] for i in sorted(range(len(rows)), key=lambda i: -score(i))[:n]]


def build(con, syllabus, spec):
    cand = candidates(con, syllabus, spec)
    parts, stats = count(con, syllabus, cand)
    bg = background(con, syllabus, cand)
    kept, dropped = {}, Counter()
    for k, st in stats.items():
        papers = {parts[i]["paper"] for i in st["explain"]}
        n_exp = len(st["explain"])
        rate = st["any"] / len(parts)
        if n_exp < 2 or len(papers) < 2:
            dropped["少于 2 份卷的解释类小问"] += 1
            continue
        if st["code"] > n_exp:
            dropped["多出现在写代码的小问(编程词汇)"] += 1
            continue
        if bg[k] >= 0.01 and rate < 3 * bg[k]:
            dropped["在其他科目中同样常见(通用词)"] += 1
            continue
        conc = st["sections"].most_common(1)[0][1] / n_exp
        if " " not in k and "-" not in k and conc < 0.3:
            dropped["单词且分散在多个大节(泛用词)"] += 1
            continue
        section = st["sections"].most_common(1)[0][0] if st["sections"] else ""
        subs = [s for s, _ in cand[k]["subs"].most_common() if s and s.split(".")[0] == section]
        sub = subs[0] if subs else (cand[k]["subs"].most_common(1)[0][0] or section)
        definition, keys = medoid(defining(
            st.get("block_rows", []) + st["rows"] + st.get("asked_rows", []), k))
        kept[k] = {"term": cand[k]["names"].most_common(1)[0][0], "key": k,
                   "papers": len(papers), "explain_parts": n_exp, "code_parts": st["code"],
                   "subsection": sub, "definition": definition,
                   "context": [] if definition else top_rows(defining(st.get("mention", []), k)),
                   "keywords": [w for w in keys if w not in k.split()],
                   "examples": sorted({parts[i]["qid"] for i in st["explain"]})[:5]}
    # an acronym and its expansion are one term: "sram" / "static ram",
    # "lan" / "local area network"; the expansion keeps the counts of both
    def acronyms(k):
        ws = re.split(r"[ -]", k)
        out = {"".join(w[0] for w in ws)}
        if len(ws) > 1 and len(ws[-1]) <= 4:
            out.add("".join(w[0] for w in ws[:-1]) + ws[-1])
        return out
    for k in [k for k in kept if " " in k]:
        for ac in acronyms(k):
            if ac in kept and ac != k and len(ac) >= 2:
                a, t = kept.pop(ac), kept[k]
                t["aliases"] = t.get("aliases", []) + [a["term"]]
                t["papers"] = max(t["papers"], a["papers"])
                t["explain_parts"] += a["explain_parts"]
                t["examples"] = sorted(set(t["examples"]) | set(a["examples"]))[:5]
                t["definition"] = t["definition"] or a["definition"]
                t["term"] = f"{a['term'].upper()} ({t['term']})"
    # levels by the spread over papers: top fifth, next two fifths, the rest
    ranked = sorted(kept.values(), key=lambda t: -t["papers"])
    for i, t in enumerate(ranked):
        t["level"] = 0 if i < len(ranked) / 5 else (1 if i < 3 * len(ranked) / 5 else 2)
    # parents: the longest kept term or shared head word the term ends with
    # (a shared head word gets a hub note per section: the keys of databases
    # and of cryptography are different families)
    sec = lambda t: t["subsection"].split(".")[0]
    heads = Counter((k.split()[-1], sec(t)) for k, t in kept.items() if " " in k)
    for k, t in kept.items():
        ws = k.split()
        parent = next((" ".join(ws[i:]) for i in range(1, len(ws)) if " ".join(ws[i:]) in kept), None)
        if not parent and len(ws) > 1 and heads[(ws[-1], sec(t))] >= 3:
            n = sum(1 for h, _ in heads if h == ws[-1] and heads[(h, _)] >= 3)
            parent = ws[-1] if n == 1 else f"{ws[-1]} ({sec(t)})"
        t["parent"] = parent
    hubs = {t["parent"] for t in kept.values() if t["parent"] and t["parent"] not in kept}
    # confusable pairs
    pairs = defaultdict(list)
    keys = list(kept)
    rx = {k: pattern(k) for k in keys}
    for i, p in enumerate(parts):
        for sent in re.split(r"(?<=[.?!])\s+|\n", p["q"]):
            if not CONTRAST.search(sent):
                continue
            named = [k for k in keys if rx[k].search(sent)]
            named = [k for k in named if not any(k != o and k in o for o in named)]
            for a in named:
                for b in named:
                    if a < b and i not in pairs[(a, b)]:
                        pairs[(a, b)].append(i)
    opposed = set()
    alias = {norm(al): k for k in keys for al in kept[k].get("aliases", [])}
    alias.update({k: k for k in keys})
    for name, a in alias.items():
        for x, y in OPPOSED:
            other = re.sub(rf"(^| ){re.escape(x)}( |$)", rf"\g<1>{y}\2", name)
            b = alias.get(other)
            if other != name and b and b != a:
                opposed.add(tuple(sorted((a, b))))
    for (a, b), idx in list(pairs.items()) + [(o, []) for o in opposed if o not in pairs]:
        if (a, b) not in opposed and len(idx) < 2:
            continue
        diff = []
        for i in idx:
            diff += [r for r in rows_of(parts[i]["ms"]) if rx[a].search(r) or rx[b].search(r)]
        diff = list(dict.fromkeys(diff))[:4]
        src = sorted({f"{parts[i]['qid']} ({parts[i]['label']})" for i in idx})[:3]
        for x, y in ((a, b), (b, a)):
            kept[x].setdefault("confusable", []).append(
                {"with": y, "difference": diff, "from": src})
    return kept, hubs, dropped


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
                 f"aliases: [{', '.join(t.get('aliases', []))}]",
                 f"subsection: \"{sub} {sub_name}\"", f"papers: {t['papers']}",
                 f"explain_parts: {t['explain_parts']}", "---", "",
                 f"# {t['term']}  {star}", "",
                 f"小节:[[{fname(sub + ' ' + sub_name)}]]", ""]
        if t["parent"]:
            lines.append(f"上级:{link(t['parent'])}")
        if children.get(k):
            lines.append("下级:" + ",".join(link(c) for c in sorted(children[k])))
        if t["definition"]:
            lines += ["", "## 评分细则中的表述", "", f"> {t['definition']}", ""]
        else:
            lines += ["", "## 评分细则中的用法(细则没有单独解释这个词)", ""]
            lines += [f"> {r}" for r in t.get("context", [])] + [""]
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
    kept, hubs, dropped = build(con, a.syllabus, spec)
    out = a.out or os.path.join(paths.EXPORTS, f"{a.syllabus}_terms")
    write_vault(out, a.syllabus, spec, kept, hubs)
    lv = Counter(t["level"] for t in kept.values())
    conf = sum(len(t.get("confusable", [])) for t in kept.values()) // 2
    print(f"候选 {len(candidates(con, a.syllabus, spec))},保留 {len(kept)} 个术语"
          f"(" + ",".join(f"{LEVELS[l][1]} {lv[l]}" for l in range(3)) + f"),"
          f"中心词汇总 {len(hubs)},易混 {conf} 对 -> {out}")
    for why, n in dropped.most_common():
        print(f"  去掉 {n}:{why}")


if __name__ == "__main__":
    main()
