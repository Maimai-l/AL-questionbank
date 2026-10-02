#!/usr/bin/env python3
"""Find formulas that KaTeX cannot render, as the pages render them.

    python3 pipeline/text/check_latex.py [--json OUT] [ID ...]

Each unit is checked the way it is shown: a CAIE mark scheme cell by cell
(manager/bank.scheme_rows), any other text whole. Within a unit, `$$...$$` and
`$...$` are typeset with the KaTeX in assets/vendor (needs node). Prints the
count per exam and column; --json writes {id: [{column, error, tex}]}.
"""
import argparse
import collections
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from lib import db, paths  # noqa: E402
from manager import bank  # noqa: E402

JS = r"""
const katex = require(process.argv[1]);
const units = JSON.parse(require('fs').readFileSync(0, 'utf8'));
const bad = [];
for (const [id, column, text] of units) {
  const re = /\$\$([\s\S]+?)\$\$|\$([^$]+?)\$/g; let m;
  while ((m = re.exec(text))) {
    const tex = m[1] || m[2];
    try { katex.renderToString(tex, { displayMode: !!m[1], throwOnError: true, strict: 'ignore' }); }
    catch (e) { bad.push([id, column, e.message.replace(/^KaTeX parse error: /, ''), tex]); }
  }
}
process.stdout.write(JSON.stringify(bad));
"""


def units(ids=None, texts=None):
    """Renderable units; `texts` {(id, column): text} stands in for the database."""
    con = db.connect()
    rows = con.execute("SELECT id, syllabus, ms_latex, question_latex FROM questions").fetchall()
    for r in rows:
        if ids and r["id"] not in ids:
            continue
        r = dict(r)
        for (i, col), t in (texts or {}).items():
            if i == r["id"]:
                r[col] = t
        if r["ms_latex"]:
            if r["syllabus"] in bank.CIE:
                for x in bank.scheme_rows(r["ms_latex"]):
                    yield [r["id"], "ms_latex", x["answer"]]
                    yield [r["id"], "ms_latex", x["guide"]]
            else:
                yield [r["id"], "ms_latex", r["ms_latex"].replace("<br>", "\n")]
        if r["question_latex"]:
            yield [r["id"], "question_latex", r["question_latex"].replace("<br>", "\n")]


def check(ids=None, texts=None):
    """{id: [{column, error, tex}]} for every formula KaTeX rejects."""
    katex = os.path.join(paths.ASSETS, "vendor", "katex", "katex.min.js")
    out = subprocess.run(["node", "-e", JS, katex], input=json.dumps(list(units(ids, texts))),
                         capture_output=True, text=True, check=True).stdout
    bad = collections.defaultdict(list)
    for i, col, err, tex in json.loads(out):
        bad[i].append({"column": col, "error": err, "tex": tex})
    return dict(bad)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("ids", nargs="*")
    ap.add_argument("--json")
    a = ap.parse_args()
    bad = check(set(a.ids) or None)
    per = collections.Counter()
    for i, errs in bad.items():
        for col in {e["column"] for e in errs}:
            per[(i.split("_")[0].split("-")[0], col)] += 1
    for (exam, col), n in sorted(per.items()):
        print(f"{exam:6} {col:15} {n} 题")
    print(f"共 {len(bad)} 题有公式无法渲染")
    if a.json:
        with open(a.json, "w", encoding="utf-8") as f:
            json.dump(bad, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
