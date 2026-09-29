#!/usr/bin/env python3
"""Tag every admissions question with its official taxonomy.

    python3 tag_admissions.py

TMUA — content topic MM1..MM8 from the official Content Specification
(April 2025), scored by the same TF-IDF method as the CAIE bank
(qb/topic_model.py): one document per spec topic (title tripled + all
subsection outcomes), n-grams to 3, IDF within the TMUA spec, question
scored on distinct-term hits. The worked answer is scored with the
question text — the official explanation names the method used, which
is exactly the evidence a topic needs. Paper 2 questions additionally
get a reasoning subtopic (Arg / Prf / Err) when the stem uses the
spec's own reasoning vocabulary.

TSA / BMAT — Critical Thinking vs Problem Solving, with the CT subtype
from the official TARA Question Guide's seven types, detected by their
formulaic stems. Invariants: TSA papers are exactly 25 PS + 25 CT;
BMAT 2020-23 are 16 PS + 16 CT. Earlier BMAT (PS 13 / CT 10 / data 12)
is reported but not asserted, since Data Analysis & Inference is folded
into PS/CT by stem.
"""
import json, math, re, sys
from collections import Counter, defaultdict

import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))          # qb/ —— 直接跑脚本时也 import 得到包
from pipeline.tags.topic_model import terms  # n-grams with stopword trimming

MM_NAMES = {
    "MM1": "Algebra and functions", "MM2": "Sequences and series",
    "MM3": "Coordinate geometry", "MM4": "Trigonometry",
    "MM5": "Exponentials and logarithms", "MM6": "Differentiation",
    "MM7": "Integration", "MM8": "Graphs of functions",
    # the spec's Part 2: background knowledge, examined in its own right
    # (polygons, primes, ratio...) — without these, every such question
    # would be forced into the nearest MM topic
    "M1": "Units", "M2": "Number", "M3": "Ratio and proportion",
    "M4": "Algebra (background)", "M5": "Geometry",
    "M6": "Statistics", "M7": "Probability",
}
REASONING = {
    "Arg": "The logic of arguments", "Prf": "Mathematical proof",
    "Err": "Identifying errors in proofs",
}

# ------------------------------------------------------------------ TMUA

def spec_topics():
    """{code: text} — each MM topic's own wording from the spec."""
    import fitz
    d = fitz.open("bank/TMUA/docs/TMUA_Content_Specification_April2025.pdf")
    full = "\n".join(p.get_text() for p in d)
    # cut at SECTION 2: reasoning content would blur the content topics
    body = full[:full.index("SECTION 2")]
    marks = [(m.group(1), m.start()) for m in
             re.finditer(r"^(M?M\d)\.\s", body, re.M)]
    docs = {}
    for i, (code, s) in enumerate(marks):
        end = marks[i + 1][1] if i + 1 < len(marks) else len(body)
        chunk = re.sub(r"^M?M\d(\.\d+)?\s*", "", body[s:end], flags=re.M)
        docs[code] = " . ".join([MM_NAMES[code].replace(" (background)", "")] * 3
                                + [chunk])
    assert sorted(docs) == sorted(MM_NAMES), sorted(docs)
    return docs


def build_vectors(docs):
    tsets = {c: terms(t) for c, t in docs.items()}
    df = Counter(t for s in tsets.values() for t in s)
    n = len(tsets)
    vecs = {}
    for c, s in tsets.items():
        w = {t: math.log(n / df[t]) for t in s if df[t] < n}
        norm = math.sqrt(sum(x * x for x in w.values())) or 1.0
        vecs[c] = {t: x / norm for t, x in w.items()}
    return vecs


def score(text, vecs):
    ts = terms(text)
    out = []
    for c, v in vecs.items():
        out.append((sum(w for t, w in v.items() if t in ts), c))
    out.sort(reverse=True)
    return out


ARG_RE = re.compile(r"necessary|sufficient|if and only if|converse|"
                    r"contrapositive|negation|for all|for some|there exists|"
                    r"only if|statements?", re.I)
PRF_RE = re.compile(r"proof|prove|conjecture|counterexample|deduce|"
                    r"deduction|justif|argument", re.I)
ERR_RE = re.compile(r"error|flaw|mistake|incorrect step|wrong", re.I)


def reasoning_subtopic(text):
    if ERR_RE.search(text) and PRF_RE.search(text):
        return "Err"
    if ARG_RE.search(text):
        return "Arg"
    if PRF_RE.search(text):
        return "Prf"
    return None


# ------------------------------------------------------------ TSA / BMAT

# The TARA Question Guide's seven CT types, by their formulaic stems.
CT_TYPES = [
    ("CT-main", "Identifying the Main Conclusion",
     r"main conclusion"),
    ("CT-draw", "Drawing a Conclusion",
     r"conclusion (?:can|which can|that can|most|best)|"
     r"(?:can|cannot|could) (?:reliably |safely )?be "
     r"(?:drawn|concluded|inferred)|"
     r"best supported by the (?:above )?(?:passage|information|argument|"
     r"data|evidence|results)|"
     r"which of the following (?:conclusions|is a conclusion)|"
     r"follows? from the (?:above|passage|argument|information)"),
    ("CT-assm", "Identifying an Assumption",
     r"assumption|assumes|assumed|taken for granted"),
    ("CT-evid", "Assessing the Impact of Additional Evidence",
     r"if true.{0,40}(strengthen|weaken)|(strengthen|weaken)s? the (?:above )?argument|"
     r"additional evidence"),
    ("CT-flaw", "Detecting Reasoning Errors",
     r"flaw|error of reasoning|reasoning error|"
     r"criticism of the (?:above )?argument|weakness (?:in|of) the argument"),
    ("CT-match", "Matching Arguments",
     r"most similar in (?:its )?(?:structure|reasoning|pattern)|"
     r"parallels? the (?:above )?(?:argument|reasoning)|"
     r"same (?:kind|pattern|structure) of (?:argument|reasoning)|"
     r"same structure as|similar (?:pattern of reasoning|reasoning) to|"
     r"argument (?:above|below) (?:most closely )?resembles"),
    ("CT-prin", "Applying Principles",
     r"principle|best illustrates|best expresses the point"),
]
CT_RES = [(code, name, re.compile(rx, re.I)) for code, name, rx in CT_TYPES]


def tag_ct_ps(text):
    """(topic, topic_name) for a TSA/BMAT question."""
    # only the stem matters: strip option lines so option wording can't vote
    stem = "\n".join(l for l in text.split("\n")
                     if not re.match(r"^(?:\*\*)?[A-H](?:\*\*)?[\s.):]", l))
    for code, name, rx in CT_RES:
        if rx.search(stem):
            return code, f"Critical Thinking: {name}"
    return "PS", "Problem Solving"


# ---------------------------------------------------------------- main

def main():
    qs = json.load(open("questions_adm.json"))
    ms = json.load(open("ms_tmua.json"))
    vecs = build_vectors(spec_topics())
    retag = {k: v for k, v in
             json.load(open("retag_tmua.json")).items() if k != "_"}
    retag_tara = {k: v for k, v in
                  json.load(open("retag_tara.json")).items() if k != "_"}

    dist = defaultdict(Counter)
    low = []
    for q in qs:
        if q["exam"] == "TMUA":
            evid = q["text"] + "\n" + ms.get(f"{q['year']}-{q['paper']}", {}
                                            ).get(str(q["q"]), "")
            ranked = score(evid, vecs)
            # GCSE algebra is the same practice bucket as MM1: the M4 doc
            # exists so those questions don't leak into MM2/MM6, but the
            # label users see is one algebra topic, not two
            ranked = [(s, "MM1" if c == "M4" else c) for s, c in ranked]
            seen, dedup = set(), []
            for s, c in ranked:
                if c not in seen:
                    seen.add(c)
                    dedup.append((s, c))
            ranked = dedup
            (s1, top), (s2, _) = ranked[0], ranked[1]
            q["topic"], q["topic_name"] = top, MM_NAMES[top]
            q["topic_all"] = [c for _s, c in ranked[:3]]
            q["topic_confident"] = int(s1 > 0 and (s1 - s2) / (s1 or 1) > 0.15)
            q["topic_source"] = "keyword"
            qid = f"{q['year']}-{q['paper']}-{q['q']}"
            if not q["topic_confident"]:
                # every low-confidence tag was read by the model; listed ones
                # were re-judged, the rest confirmed as scored
                q["topic"] = retag.get(qid, q["topic"])
                q["topic_name"] = MM_NAMES[q["topic"]]
                q["topic_source"] = "model"
            if s1 == 0:
                low.append(f"TMUA {q['year']} P{q['paper']} q{q['q']}: 零证据")
            q["subtopic"] = (reasoning_subtopic(q["text"])
                             if q["paper"] == "2" else None)
            q["subtopic_name"] = REASONING.get(q["subtopic"])
            dist[f"TMUA P{q['paper']}"][q["topic"]] += 1
        else:
            code, name = tag_ct_ps(q["text"])
            q["topic_source"] = "keyword"
            qid = f"{q['exam']}-{q['year']}-{q['q']}"
            if qid in retag_tara:
                code = retag_tara[qid]
                name = ("Problem Solving" if code == "PS" else
                        "Critical Thinking: " + dict(
                            (c, n) for c, n, _ in CT_RES)[code])
                q["topic_source"] = "model"
            q["topic"], q["topic_name"] = code, name
            kind = "CT" if code.startswith("CT") else "PS"
            dist[f"{q['exam']} {q['year']}"][kind] += 1

    json.dump(qs, open("questions_adm.json", "w"), ensure_ascii=False, indent=1)

    print("== TMUA 内容主题分布")
    for p in ("TMUA P1", "TMUA P2"):
        d = dist[p]
        print(f"  {p}: " + "  ".join(f"{c}:{d[c]}" for c in sorted(MM_NAMES)))
    if low:
        print(f"⚠️  {len(low)} 题零证据:", *low[:5])

    print("== TSA / BMAT  PS/CT")
    bad = []
    for label in sorted(dist):
        if label.startswith("TMUA"):
            continue
        d = dist[label]
        exam, year = label.split()
        want = None
        if exam == "TSA":
            want = (25, 25)
        elif exam == "BMAT" and int(year) >= 2020:
            want = (16, 16)
        note = ""
        if want and (d["PS"], d["CT"]) != want:
            note = f"  ⚠️ 应为 PS{want[0]}/CT{want[1]}"
            bad.append(label)
        print(f"  {label}: PS {d['PS']:>2}  CT {d['CT']:>2}{note}")
    print(f"\n{len(bad)} 份卷 PS/CT 配比不符" if bad else "\n配比全部符合官方结构")


if __name__ == "__main__":
    main()
