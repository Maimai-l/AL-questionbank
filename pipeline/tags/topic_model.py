#!/usr/bin/env python3
"""Score a question against every topic, using the syllabus as the evidence.

Replaces the hand-written keyword tables in `tag.py` / `topics_9231.py` /
`topics_9618.py`. Those were my guesses at what each topic's questions look
like; this is Cambridge's own wording for what each topic *is*, which is also
the wording the question setters reach for.

Method, deliberately boring:

* one document per syllabus sub-topic = its title + learning outcomes + notes;
* n-grams up to 3 words, so "stationary point" and "sum to infinity" survive
  as units instead of dissolving into "point" and "sum";
* IDF computed **within the component**, because that is the only scope in
  which topics compete. "differentiate" is useless for telling 1.7 from 3.4,
  but those two never appear on the same paper, so globally down-weighting it
  would throw away the one term that identifies P1's differentiation topic;
* a topic vector is L2-normalised, and a question scores by the weight of the
  distinct terms it hits. Term frequency in the *question* is ignored on
  purpose — a word repeated six times is not six times the evidence, and
  mark schemes repeat method words constantly.

Nothing here is learned from the question bank, so scoring the bank with it is
an honest test rather than a memory check.
"""
import json, math, os, re, sys
from collections import Counter, defaultdict

import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))          # 项目根目录
from lib import paths
MAXN = 3

# Words that carry no topic information in this domain. IDF removes most of
# them by itself; these are listed because they are frequent enough to add
# noise to the n-grams built around them.
STOP = set("""a an the and or of to in on for with by from as at is are be been
being this that these those it its their there here which who whom whose what
when where how why not no nor if then than so such other others any all both
each few more most some own same can will just should now candidates able
understand understanding show shown showing knowledge use used using include
including included e g eg ie i.e. e.g. etc appropriate given give gives given
find finding found determine determined solve solving solved problem problems
value values simple simply case cases form forms may might must only also
required require requires expected expect state stated states following follow
number numbers one two three first second general specific involving involve
involves related relating relate""".split())

WORD = re.compile(r"[a-z][a-z\-']*|\d+")


def terms(text, maxn=MAXN):
    """Distinct 1..maxn-grams, stopword-trimmed at the edges."""
    toks = WORD.findall((text or "").lower())
    out = set()
    for n in range(1, maxn + 1):
        for i in range(len(toks) - n + 1):
            g = toks[i:i + n]
            if g[0] in STOP or g[-1] in STOP:
                continue
            # Maths comes out of the text layer as loose symbols, so without
            # this every question grows terms like "x 3", "2 3", "d y" that
            # match by coincidence and drown the real ones.
            if any(len(w) < 2 or w.isdigit() for w in g):
                continue
            out.add(" ".join(g))
    return out


def topic_text(t):
    """The syllabus's own description of a topic, with the title weighted.

    The title is the single most reliable phrase — "Circular measure",
    "Hyperbolic functions" — so it is repeated to count as several outcomes
    without needing a separate weighting scheme downstream.
    """
    return " . ".join([t["name"]] * 3 + t["outcomes"] + t["notes"])


# 9618 numbers its topics by syllabus *section* (1-20), and each paper draws
# from a range of sections rather than from one. The maths syllabuses need no
# such map: there, component number and topic prefix are the same thing.
PAPER_SECTIONS = {
    "9618": {"1": [str(i) for i in range(1, 9)],
             "2": [str(i) for i in range(9, 13)],
             "3": [str(i) for i in range(13, 21)],
             "4": ["19", "20"]},
}


class Model:
    """One scorer per syllabus. Topics compete only inside their component."""

    def __init__(self, spec):
        self.code = spec.get("code")
        self.topics = spec["topics"]
        self.by_component = defaultdict(list)
        for code, t in self.topics.items():
            self.by_component[t["component"]].append(code)

        self.doc_terms = {c: terms(topic_text(t)) for c, t in self.topics.items()}
        self.weights = {}
        for comp, codes in self.by_component.items():
            df = Counter()
            for c in codes:
                df.update(self.doc_terms[c])
            n = len(codes)
            for c in codes:
                w = {}
                for term in self.doc_terms[c]:
                    idf = math.log((n + 1) / (df[term] + 0.5))
                    if idf <= 0:
                        continue
                    # a longer phrase that matches is stronger evidence than a
                    # bare word, and far less likely to match by accident
                    w[term] = idf * (1 + 0.5 * (term.count(" ")))
                norm = math.sqrt(sum(v * v for v in w.values())) or 1.0
                self.weights[c] = {k: v / norm for k, v in w.items()}

    def candidates(self, component):
        """Topic codes a question on this paper is allowed to be."""
        if component is None:
            return list(self.topics)
        comp = str(component)
        sections = PAPER_SECTIONS.get(self.code, {}).get(comp)
        if sections:
            return [c for s in sections for c in self.by_component.get(s, [])]
        return self.by_component.get(comp) or list(self.topics)

    def score(self, text, component=None, extra=""):
        """Ranked (score, topic_code, hits) for one question."""
        seen = terms(text + " . " + (extra or ""))
        codes = self.candidates(component)
        out = []
        for c in codes:
            w = self.weights[c]
            hits = [t for t in seen if t in w]
            if not hits:
                continue
            s = sum(w[t] for t in hits)
            out.append((s, c, sorted(hits, key=lambda t: -w[t])[:6]))
        out.sort(key=lambda r: (-r[0], r[1]))
        return out


def load(path=None):
    spec = json.load(open(path or paths.SYLLABUS))
    for code, s in spec.items():
        s["code"] = code
    return {code: Model(s) for code, s in spec.items()}


if __name__ == "__main__":
    models = load()
    demo = [
        ("9709", "1", "Find the coefficient of x^3 in the expansion of (2 + 3x)^7"),
        ("9709", "1", "The curve has a stationary point at x = 2. Find the second derivative."),
        ("9709", "4", "A particle is projected with speed 20 m s-1 at an angle of 30 degrees"),
        ("9231", "3", "A smooth sphere of mass m moving with speed u collides directly"),
        ("9618", "3", "Complete the truth table for the logic circuit and simplify using a Karnaugh map"),
        ("9618", "2", "The stack is implemented as a 1D array. Write pseudocode for the push operation."),
    ]
    for syl, comp, q in demo:
        r = models[syl].score(q, comp)[:3]
        print(f"\n{syl}/P{comp}  {q[:66]}")
        for s, c, hits in r:
            print(f"   {s:6.3f}  {c:<5} {models[syl].topics[c]['name'][:34]:<36} "
                  f"{', '.join(hits[:4])}")
