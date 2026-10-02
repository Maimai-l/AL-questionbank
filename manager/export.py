"""Export a set as a ZIP (docs/data-manager.md, F7) by a template's settings (F8, section 7).

Every file is listed first as (path in the ZIP, bytes or a file on disk), so the
preview and the ZIP come from the same list. Entries carry a fixed timestamp and
come in a fixed order: the same set, settings and answer file give the same ZIP.
"""
import io
import json
import os
import re
import zipfile

from lib import paths, scheme
from manager import bank, docs, paper

ANSWERS = os.path.join(paths.WORK, "answers")      # F5 writes <set id>.pdf here
STAMP = (1980, 1, 1, 0, 0, 0)
STORED = (".png", ".pdf")


def answer_pdf(s):
    p = os.path.join(ANSWERS, s["id"] + ".pdf")
    return p if os.path.isfile(p) else None


def file_code(r):
    """9709/12/M/J/23 as 9709-12-MJ-23, for file names."""
    return re.sub(r"/([A-Z])/([A-Z])/", r"-\1\2-", bank.paper_code(r)).replace("/", "-")


def fill_name(pattern, i, r):
    def one(m):
        key, pad = m.group(1), m.group(2)
        v = {"index": i, "paper_code": file_code(r), "q": r["q"], "id": r["id"]}.get(key)
        if v is None:
            return m.group(0)
        return f"{v:0{int(pad)}d}" if pad and isinstance(v, int) else str(v)
    return re.sub(r"\{(\w+)(?::0?(\d+))?\}", one, pattern)


def _cell(t):
    return (t or "").replace("|", "\\|").replace("\n", "<br>")


def scheme_md(r):
    head = f"# {bank.paper_code(r)} Q{r['q']} mark scheme\n\n"
    ms = r["ms_latex"] or r["ms_text"]
    if not ms:
        return None
    if r["syllabus"] not in bank.CIE:
        return head + ms.replace("<br>", "\n").strip() + "\n"
    lines = ["| Answer | Mark | Guidance |", "|---|---|---|"]
    for x in bank.scheme_rows(ms):
        if x["part"]:
            lines.append(f"| **{x['part']}** | | |")
        lines.append(f"| {_cell(x['answer'])} | {_cell(x['code'])} | {_cell(x['guide'])} |")
    return head + "\n".join(lines) + "\n"


def question_md(r):
    text = (r["question_latex"] or r["question_text"] or "").strip()
    if not text:
        return None
    marks = f" ({r['marks']} marks)" if r["marks"] else ""
    return f"# {bank.paper_code(r)} Q{r['q']}{marks}\n\n{text}\n"


def explanation_md(r):
    if not r["explanation"]:
        return None
    ex = json.loads(r["explanation"])
    out = [f"# {bank.paper_code(r)} Q{r['q']} explanation", ""]
    for p in ex.get("parts", []):
        out += [f"## {p.get('label') or 'Solution'}", ""]
        if p.get("approach"):
            out += [p["approach"], ""]
        if p.get("points"):
            out += ["| Mark | Point | Why |", "|---|---|---|"]
            out += [f"| {_cell(str(pt.get('mark', '')))} | {_cell(pt.get('point'))} | {_cell(pt.get('why'))} |"
                    for pt in p["points"]]
            out.append("")
        if p.get("pitfalls"):
            out += [f"- {x}" for x in p["pitfalls"]] + [""]
    return "\n".join(out).rstrip() + "\n"


def _image(r, with_space):
    p = paths.answer_space(r["image"]) if with_space else None
    return p or paths.resolve(r["image"])


def _parts(r):
    try:
        return [{"label": p["label"], "marks": p.get("marks")}
                for p in json.loads(r["part_data"] or "{}").get("parts", [])]
    except ValueError:
        return []


def plan(s, settings, body):
    """(files, readme, manifest): files are [(path, bytes | file path)] in ZIP order."""
    rows = paper._rows(s["items"])
    per, folder = settings["per_question"], settings["layout"] == "folder_per_question"
    papers = list(dict.fromkeys(bank.paper_code(r) for r in rows))
    qfiles, entries = [], []
    for i, r in enumerate(rows, 1):
        name = fill_name(settings["filename"], i, r)
        mine = []

        def put(fname, content):
            if content is None:
                return
            path = f"{name}/{fname}" if folder else f"{name}_{fname}"
            mine.append(path)
            qfiles.append((path, content.encode() if isinstance(content, str) else content))
        for kind in per:
            if kind in ("image", "image_with_space"):
                img = _image(r, kind == "image_with_space")
                put("question.png", img and ("file", img))
            elif kind == "text":
                put("question.md", question_md(r))
            elif kind == "mark_scheme":
                put("mark_scheme.md", scheme_md(r))
            elif kind == "explanation":
                put("explanation.md", explanation_md(r))
        entries.append({"index": i, "id": r["id"], "paper_code": bank.paper_code(r), "q": r["q"],
                        "marks": r["marks"], "parts": _parts(r), "topic": r["topic"],
                        "topic_name": r["topic_name"], "files": mine})
    qfiles = [(p, c[1] if isinstance(c, tuple) else c) for p, c in qfiles]

    top = []
    ans = answer_pdf(s) if settings["answers"] == "written_pdf" else None
    if ans:
        top.append((settings["answer_filename"] + ".pdf", ans))
    for d in settings["documents"]:
        if d == "mark_scheme":
            top.append(("mark_scheme.html", docs.scheme(s).encode()))
        elif d == "explanation":
            top.append(("explanation.html", docs.explanation(s).encode()))
        elif d == "question_paper":
            top.append(("question_paper.pdf", paper.build(s)))

    marks = sum(r["marks"] or 0 for r in rows)
    manifest = {"schema": "alevel-export/v1", "title": s["name"], "date": s["created"][:10],
                "count": len(rows), "total_marks": marks, "papers": papers,
                "answers": settings["answer_filename"] + ".pdf" if ans else None, "questions": entries}
    meta = []
    if settings["manifest"]:
        meta.append(("manifest.json", (json.dumps(manifest, ensure_ascii=False, indent=1) + "\n").encode()))
    table = ["| 序号 | 试卷代码 | 题号 | 分值 | 主题 |", "|---|---|---|---|---|"]
    table += [f"| {e['index']:02d} | {e['paper_code']} | Q{e['q']} | {e['marks'] or ''} | "
              f"{e['topic_name'] or e['topic'] or ''} |" for e in entries]
    if settings["summary"]:
        meta.append(("summary.md", (f"# {s['name']}\n\n" + "\n".join(table) + "\n").encode()))

    names = ([settings["prompt_file"]] if settings["prompt_file"] else []) \
        + [p for p, _ in meta + top + qfiles]
    values = {"title": s["name"], "count": str(len(rows)), "total_marks": str(marks),
              "papers": "、".join(papers), "date": s["created"][:10],
              "question_table": "\n".join(table), "file_tree": "```\n" + "\n".join(names) + "\n```"}
    readme = re.sub(r"\{(title|count|total_marks|papers|date|question_table|file_tree)\}",
                    lambda m: values[m.group(1)], body)
    files = ([(settings["prompt_file"], readme.encode())] if settings["prompt_file"] else []) \
        + meta + top + qfiles
    return files, readme, manifest


def _size(c):
    return os.path.getsize(c) if isinstance(c, str) else len(c)


def preview(s, settings, body):
    files, readme, manifest = plan(s, settings, body)
    return {"files": [{"path": p, "size": _size(c)} for p, c in files],
            "size": sum(_size(c) for _, c in files), "readme": readme,
            "manifest": json.dumps(manifest, ensure_ascii=False, indent=1)}


def zip_bytes(s, settings, body):
    files, _, _ = plan(s, settings, body)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for path, c in files:
            info = zipfile.ZipInfo(path, STAMP)
            info.compress_type = zipfile.ZIP_STORED if path.endswith(STORED) else zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            if isinstance(c, str):
                with open(c, "rb") as f:
                    c = f.read()
            z.writestr(info, c)
    return buf.getvalue()


def zip_name(s):
    return re.sub(r"[/\\:]", "-", s["name"]) + ".zip"
