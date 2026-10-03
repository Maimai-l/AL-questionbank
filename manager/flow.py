"""Batch generation (docs/data-manager.md, F9): a node graph over the bank, run on the server.

A graph is {id, name, created, nodes: [{id, type, x, y, params}], links: [{from: [node, port],
to: [node, port]}]}. Data comes in two shapes: a list of records, or groups (named lists).
Records are questions ("q"), chapters ("c") or files ("f", the chapter PDFs). A node that
works on a list, fed with groups, works on each group and keeps the groups.

evaluate() works out every node's outputs without side effects (the counts by the ports and
the details beside the canvas); run() also makes what the output nodes make: ZIPs, question
practice papers (files under paths.FLOWS/out/<graph id>/) and question sets. Random order is seeded:
the same graph, bank and seed give the same result.
"""
import hashlib
import json
import os
import random
import re
import time
import uuid
import zipfile

import pymupdf

from lib import db, paths
from manager import bank, export, paper, sets, templates

BUILTIN = os.path.join(os.path.dirname(os.path.abspath(__file__)), "flows")
OUT = os.path.join(paths.FLOWS, "out")
EXAMS = ["9709", "9231", "9618", "TMUA", "TSA", "BMAT"]
BOOKS = {
    "9709_p1": "9709 Pure Mathematics 1", "9709_p23": "9709 Pure Mathematics 2 & 3",
    "9709_p4": "9709 Mechanics", "9709_p5": "9709 Probability & Statistics 1",
    "9231": "9231 Further Mathematics", "9618": "9618 Computer Science",
}

# fields: key, label, kind (num | text | bool)
QFIELDS = [("exam", "考试", "text"), ("component", "试卷", "num"), ("paper", "卷号", "text"),
           ("year", "年份", "num"), ("season", "考季", "num"), ("q", "题号", "num"),
           ("position", "卷内位置", "num"), ("marks", "分值", "num"), ("parts", "小问数", "num"),
           ("topic", "主题", "text"), ("subtopic", "子主题", "text"),
           ("diagram", "含图", "bool"), ("explained", "有详解", "bool")]
CFIELDS = [("book", "教材", "text"), ("chapter", "章号", "num"), ("title", "标题", "text"), ("topic", "主题", "text")]
FFIELDS = [("name", "文件名", "text")]
FIELDS = {"q": QFIELDS, "c": CFIELDS, "f": FFIELDS}
OPS = ["=", "≠", "≥", "≤", "包含"]

# node types: category, label, inputs [(label, accepted record types or None for any)], outputs
# [(label, record type or "same")], shapes: "list" (round port) or "group" (square port)
NODES = {
    "bank": {"cat": "来源", "label": "题库", "ins": [], "outs": [("题目", "q", "list")]},
    "book": {"cat": "来源", "label": "教材", "ins": [], "outs": [("章节", "c", "list"), ("章节 PDF", "f", "list")]},
    "set": {"cat": "来源", "label": "题组", "ins": [], "outs": [("题目", "q", "list")]},
    "filter": {"cat": "处理", "label": "筛选", "ins": [("列表", None)], "outs": [("列表", "same", "same")]},
    "sort": {"cat": "处理", "label": "排序", "ins": [("列表", None)], "outs": [("列表", "same", "same")]},
    "take": {"cat": "处理", "label": "限制数量", "ins": [("列表", None)], "outs": [("列表", "same", "same")]},
    "group": {"cat": "处理", "label": "分组", "ins": [("列表", None)], "outs": [("分组", "same", "group")]},
    "merge": {"cat": "处理", "label": "合并", "ins": [("分组", None)], "outs": [("列表", "same", "list")]},
    "join": {"cat": "处理", "label": "连接", "ins": [("左", None), ("右", None)], "outs": [("分组", "right", "group")]},
    "export": {"cat": "输出", "label": "导出", "ins": [("题目", ("q",)), ("附件", ("f",))], "outs": []},
    "newset": {"cat": "输出", "label": "新建题组", "ins": [("题目", ("q",))], "outs": []},
    "paper": {"cat": "输出", "label": "练习卷", "ins": [("题目", ("q",))], "outs": []},
    "chapters": {"cat": "输出", "label": "章节包", "ins": [("分组", ("q",))], "outs": []},
}


class FlowError(ValueError):
    pass


# ------------------------------------------------------------------ records

def _topic_names(exam):
    con = db.connect()
    return {r[0]: r[1] for r in con.execute(
        "SELECT DISTINCT topic, topic_name FROM questions WHERE syllabus = ? AND topic IS NOT NULL", (exam,))}


def question_records(exam):
    out = []
    names = _topic_names(exam)
    for r in bank.rows(exam):
        out.append({"id": r["id"], "label": f"{r['code']} Q{r['q']}", "exam": exam,
                    "component": int(r["component"]) if str(r["component"]).isdigit() else r["component"],
                    "paper": str(r["paper"]), "year": r["year"], "season": r["month"], "q": r["q"],
                    "position": r["position"], "marks": r["marks"] or 0, "parts": r["parts"] or 0,
                    "topic": r["topic"] or "", "topic_name": names.get(r["topic"]) or "", "subtopic": r["subtopic"] or "",
                    "diagram": bool(r["diagram"]), "explained": bool(r["explanation"]),
                    "topics": r["topics"]})
    return out


def _records_by_id(ids):
    exams = {q[:4] if re.match(r"\d{4}_", q) else q.split("-")[0] for q in ids}
    by = {}
    for e in exams:
        for r in question_records(e):
            by[r["id"]] = r
    return [by[q] for q in ids if q in by]


def textbook_pdf(book):
    p = os.path.join(paths.TEXTBOOKS, book + ".pdf")
    return p if os.path.isfile(p) else None


def chapter_records(book):
    con = db.connect()
    pdf = textbook_pdf(book)
    out, files = [], []
    for r in con.execute("SELECT id, book, chapter_no, title, topic, page_from, page_to FROM chapters "
                         "WHERE book = ? ORDER BY chapter_no", (book,)):
        title = re.sub(r"^\d+\s+", "", r["title"])
        label = f'第 {r["chapter_no"]} 章 {title}'      # 第 9 章 Integration
        out.append({"id": r["id"], "label": label, "book": book, "chapter": r["chapter_no"],
                    "title": r["title"], "topic": r["topic"] or ""})
        files.append({"id": r["id"], "label": f"{label}.pdf", "name": f"{label}.pdf",
                      "chapter": r["id"], "pdf": pdf, "pages": [r["page_from"], r["page_to"]]})
    return out, files


# ------------------------------------------------------------------ values

def lst(t, items):
    return {"shape": "list", "type": t, "items": items}


def grp(t, groups):
    return {"shape": "group", "type": t, "groups": groups}


def per_list(v, fn):
    """Apply a list operation to a list, or to every group of a grouping."""
    if v["shape"] == "list":
        return lst(v["type"], fn(v["items"], ""))
    return grp(v["type"], [dict(g, items=fn(g["items"], g["name"])) for g in v["groups"]])


def _field(t, key):
    for k, label, kind in FIELDS[t]:
        if k == key:
            return kind
    raise FlowError(f"字段 {key} 不存在")


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _test(rec, kind, key, op, value):
    have = rec.get(key)
    if kind == "bool":
        want = str(value).strip() in ("是", "1", "true", "True")
        return (have == want) if op == "=" else (have != want) if op == "≠" else False
    if kind == "num":
        a, b = _num(have), _num(value)
        if a is None or b is None:
            return False
        return {"=": a == b, "≠": a != b, "≥": a >= b, "≤": a <= b, "包含": str(value) in str(have)}[op]
    a, b = str(have or "").lower(), str(value).strip().lower()
    return {"=": a == b, "≠": a != b, "≥": a >= b, "≤": a <= b, "包含": b in a}[op]


def _sort_key(kind):
    if kind == "num":
        return lambda r, k: (_num(r.get(k)) is None, _num(r.get(k)) or 0)
    return lambda r, k: str(r.get(k) or "")


# ------------------------------------------------------------------ nodes

def node_bank(p, ins):
    exam = p.get("exam") or "9709"
    if exam not in EXAMS:
        raise FlowError("考试不存在")
    return [lst("q", question_records(exam))]


def node_book(p, ins):
    book = p.get("book") or "9709_p1"
    if book not in BOOKS:
        raise FlowError("教材不存在")
    chapters, files = chapter_records(book)
    return [lst("c", chapters), lst("f", files)]


def node_set(p, ins):
    try:
        s = sets.get(p.get("set") or "")
    except (KeyError, FileNotFoundError):
        raise FlowError("未选择题组")
    return [lst("q", _records_by_id(s["items"]))]


def node_filter(p, ins):
    v = ins[0]
    conds = [c for c in p.get("conds") or [] if c.get("field") and c.get("op") in OPS and str(c.get("value", "")).strip() != ""]
    kinds = [_field(v["type"], c["field"]) for c in conds]
    return [per_list(v, lambda items, _: [r for r in items
                                          if all(_test(r, k, c["field"], c["op"], c["value"]) for c, k in zip(conds, kinds))])]


def node_sort(p, ins):
    v = ins[0]
    if p.get("by") == "random":
        seed = str(p.get("seed", 1))

        def shuffle(items, name):
            out = list(items)
            random.Random(f"{seed}/{name}").shuffle(out)
            return out
        return [per_list(v, shuffle)]
    key = p.get("field") or ("marks" if v["type"] == "q" else "chapter" if v["type"] == "c" else "name")
    sk = _sort_key(_field(v["type"], key))
    return [per_list(v, lambda items, _: sorted(items, key=lambda r: sk(r, key), reverse=bool(p.get("desc"))))]


def node_take(p, ins):
    try:
        n = max(0, int(p.get("n", 10)))
    except (TypeError, ValueError):
        raise FlowError("条数须为整数")
    return [per_list(ins[0], lambda items, _: items[:n])]


def _group_name(value):
    if isinstance(value, bool):
        return "是" if value else "否"
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    return str(value) if value not in (None, "") else "无"


def node_group(p, ins):
    v = ins[0]
    if v["shape"] != "list":
        raise FlowError("分组节点的输入须为列表")
    key = p.get("field") or ("topic" if v["type"] != "f" else "name")
    kind = _field(v["type"], key)
    by, label = {}, {}
    for r in v["items"]:
        k = _group_name(r.get(key))
        by.setdefault(k, []).append(r)
        if key == "topic" and r.get("topic_name"):
            label[k] = f"{k} {r['topic_name']}"
    names = sorted(by, key=(lambda n: (_num(n) is None, _num(n) or 0, n)) if kind == "num" else str)
    return [grp(v["type"], [{"name": label.get(n, n), "key": n, "items": by[n]} for n in names])]


def node_merge(p, ins):
    v = ins[0]
    if v["shape"] != "group":
        raise FlowError("合并节点的输入须为分组")
    seen, out = set(), []
    for g in v["groups"]:
        for r in g["items"]:
            if r["id"] not in seen:
                seen.add(r["id"])
                out.append(r)
    return [lst(v["type"], out)]


def node_join(p, ins):
    left, right = ins
    if left["shape"] != "list" or right["shape"] != "list":
        raise FlowError("连接节点的两个输入须为列表")
    lf = p.get("left") or "topic"
    rf = p.get("right") or "topic"
    _field(left["type"], lf)
    _field(right["type"], rf)
    by = {}
    for r in right["items"]:
        # by topic, a question goes with every topic one of its parts is on (as the
        # chapter export does), not only its main topic
        for k in (r.get("topics") or [r.get(rf)]) if rf == "topic" else [r.get(rf)]:
            by.setdefault(str(k), []).append(r)
    return [grp(right["type"], [{"name": l["label"], "key": l["id"], "items": by.get(str(l.get(lf)), [])}
                                for l in left["items"]])]


# ------------------------------------------------------------------ outputs

def _pseudo_set(g, name, ids, extra=""):
    sid = hashlib.sha1(f"{g['id']}/{extra}".encode()).hexdigest()[:12]
    return {"id": sid, "name": name, "created": g.get("created") or time.strftime("%Y-%m-%d %H:%M"), "items": ids}


def _safe(name):
    return re.sub(r'[/\\:*?"<>|]', "-", name).strip() or "未命名"


def chapter_pdf(f):
    """The pages of one chapter cut from its textbook PDF, or None when the PDF is not there."""
    if not f.get("pdf") or not all(f["pages"]):
        return None
    src = pymupdf.open(f["pdf"])
    out = pymupdf.open()
    a, b = f["pages"]
    out.insert_pdf(src, from_page=max(0, a - 1), to_page=min(src.page_count, b) - 1)
    data = out.tobytes(garbage=3, deflate=True)
    out.close()
    src.close()
    return data


def _write_zip(path, files):
    with zipfile.ZipFile(path, "w") as z:
        for name, c in files:
            info = zipfile.ZipInfo(name, export.STAMP)
            info.compress_type = zipfile.ZIP_STORED if name.endswith(export.STORED) else zipfile.ZIP_DEFLATED
            if isinstance(c, str):
                with open(c, "rb") as fh:
                    c = fh.read()
            z.writestr(info, c)


def out_export(g, node, ins, outdir):
    v, att = ins[0], ins[1] if len(ins) > 1 else None
    try:
        t = templates.get(node["params"].get("template") or "default")
    except KeyError:
        raise FlowError("导出模板不存在")
    st, body = t["settings"], t["body"]
    attach = att["items"] if att and att["shape"] == "list" else []
    files, missing, count = [], 0, 0
    if v["shape"] == "list":
        s = _pseudo_set(g, g["name"], [r["id"] for r in v["items"]], node["id"])
        files += export.plan(s, st, body)[0]
        count = len(v["items"])
        for f in attach:
            data = chapter_pdf(f)
            missing += data is None
            if data:
                files.append((_safe(f["name"]), data))
        folders = 0
    else:
        for i, grp_ in enumerate(v["groups"], 1):
            folder = f"{i:02d}_{_safe(grp_['name'])}"
            s = _pseudo_set(g, grp_["name"], [r["id"] for r in grp_["items"]], f"{node['id']}/{i}")
            files += [(f"{folder}/{p}", c) for p, c in export.plan(s, st, body)[0]]
            count += len(grp_["items"])
            for f in attach:
                if f.get("chapter") == grp_["key"]:
                    data = chapter_pdf(f)
                    missing += data is None
                    if data:
                        files.append((f"{folder}/{_safe(f['name'])}", data))
        folders = len(v["groups"])
    name = _safe(g["name"]) + ".zip"
    path = os.path.join(outdir, f"{node['id']}.zip")
    _write_zip(path, files)
    meta = ([f"{folders} 个文件夹"] if folders else []) + [f"{count} 题", _size(path)]
    if missing:
        meta.append(f"缺少 {missing} 份章节 PDF")
    return [{"node": node["id"], "kind": "zip", "name": name, "file": os.path.basename(path), "meta": meta}]


def out_newset(g, node, ins, outdir):
    v = ins[0]
    base = g["name"].strip()
    parts = [(base, v["items"])] if v["shape"] == "list" else [(f"{base} {x['name']}", x["items"]) for x in v["groups"]]
    out = []
    for name, items in parts:
        ids = list(dict.fromkeys(r["id"] for r in items))
        old = next((s for s in sets.all_sets() if s["name"] == name and s.get("source") == "flow"), None)
        s = sets.update(old["id"], items=ids) if old else sets.create(name, ids, "flow")
        out.append({"node": node["id"], "kind": "set", "name": s["name"], "set": s["id"], "meta": ["题组", f"{len(ids)} 题"]})
    return out


def out_paper(g, node, ins, outdir):
    v = ins[0]
    parts = [(g["name"], v["items"], "")] if v["shape"] == "list" else \
        [(x["name"], x["items"], str(i)) for i, x in enumerate(v["groups"], 1)]
    out = []
    for name, items, extra in parts:
        if not items:
            continue
        s = _pseudo_set(g, name, list(dict.fromkeys(r["id"] for r in items)), f"{node['id']}/{extra}")
        try:
            src = paper.build(s)
        except paper.EmptyPaper as e:
            raise FlowError(str(e))
        fname = f"{node['id']}{('-' + extra) if extra else ''}.pdf"
        with open(src, "rb") as fh, open(os.path.join(outdir, fname), "wb") as w:
            w.write(fh.read())
        out.append({"node": node["id"], "kind": "pdf", "name": _safe(name) + ".pdf", "file": fname,
                    "meta": ["练习卷", f"{len(s['items'])} 题", f"{paper.page_count(src)} 页", _size(src)]})
    return out


RUN = {"bank": node_bank, "book": node_book, "set": node_set, "filter": node_filter, "sort": node_sort,
       "take": node_take, "group": node_group, "merge": node_merge, "join": node_join}
def out_chapters(g, node, ins, outdir):
    """Chapter packages, as pipeline/export/export_all_chapters.py writes them, for the
    groups of a join with a textbook's chapters: one ZIP per chapter, in
    exports/chapters/<book>/, replacing the archive of the same name."""
    from pipeline.export import export_all_chapters as chap
    v = ins[0]
    if v["shape"] != "group":
        raise FlowError("章节包节点的输入须为按章节的分组")
    con = db.connect()
    by = {c["id"]: c for c in chap.chapters_of(con)}
    if any(x["key"] not in by for x in v["groups"]):
        raise FlowError("章节包节点的输入须为教材章节的分组")
    out, books = [], {}
    for x in v["groups"]:
        c = by[x["key"]]
        path = chap.chapter_path(c)
        chap.write_chapter(con, c, path, ids=[r["id"] for r in x["items"]])
        b = books.setdefault(path.parent, {"files": 0, "questions": 0, "size": 0})
        b["files"] += 1
        b["questions"] += len(x["items"])
        b["size"] += path.stat().st_size
    for folder, b in books.items():
        size = f"{b['size'] / 1048576:.1f} MB" if b["size"] >= 1048576 else f"{max(1, round(b['size'] / 1024))} KB"
        out.append({"node": node["id"], "kind": "folder", "name": os.path.relpath(folder, os.path.dirname(paths.EXPORTS)),
                    "meta": [f"{b['files']} 个文件", f"{b['questions']} 题", size]})
    return out


MAKE = {"export": out_export, "newset": out_newset, "paper": out_paper, "chapters": out_chapters}


# ------------------------------------------------------------------ graph

def _order(nodes, links):
    deps = {n["id"]: {l["from"][0] for l in links if l["to"][0] == n["id"]} for n in nodes}
    done, order = set(), []
    while len(order) < len(nodes):
        ready = [n for n in nodes if n["id"] not in done and deps[n["id"]] <= done]
        if not ready:
            raise FlowError("连线构成环路")
        for n in ready:
            done.add(n["id"])
            order.append(n)
    return order


def _accepts(spec, value):
    return spec is None or value["type"] in spec


def evaluate(g, make=False):
    """{values: {node: [output values]}, errors: {node: message}, outputs: [...]}."""
    nodes = [n for n in g.get("nodes", []) if n.get("type") in NODES]
    ids = {n["id"] for n in nodes}
    links = [l for l in g.get("links", []) if l["from"][0] in ids and l["to"][0] in ids]
    values, errors, outputs = {}, {}, []
    order = _order(nodes, links)             # a cycle fails here, before the last run is cleared
    outdir = out_dir(g["id"]) if make else None
    if make:
        os.makedirs(outdir, exist_ok=True)
        for f in os.listdir(outdir):
            os.remove(os.path.join(outdir, f))
    for n in order:
        spec = NODES[n["type"]]
        ins = []
        if any(l["to"][0] == n["id"] and l["from"][0] in errors for l in links):
            continue                         # fed by a node that failed: that node shows the error
        for i, (label, accept) in enumerate(spec["ins"]):
            src = next((l["from"] for l in links if l["to"] == [n["id"], i]), None)
            out = values.get(src[0]) or [] if src else []
            v = out[src[1]] if src and isinstance(src[1], int) and 0 <= src[1] < len(out) else None
            if v is not None and not _accepts(accept, v):
                v = None
            ins.append(v)
        n.setdefault("params", {})
        try:
            if spec["ins"] and ins[0] is None:
                raise FlowError(f"{'左侧' if spec['ins'][0][0] == '左' else spec['ins'][0][0]}输入未连接")
            if n["type"] == "join" and ins[1] is None:
                raise FlowError("右侧输入未连接")
            if n["type"] in RUN:
                values[n["id"]] = RUN[n["type"]](n["params"], ins)
            elif make:
                outputs += MAKE[n["type"]](g, n, ins, outdir)
        except FlowError as e:
            errors[n["id"]] = str(e)
    return {"values": values, "errors": errors, "outputs": outputs}


def _summary(v, limit=40):
    """What the page shows for one value: counts and the first rows."""
    if v is None:
        return None
    marks = lambda items: sum(r.get("marks") or 0 for r in items)
    if v["shape"] == "list":
        rows = [[r["label"], r.get("marks") if v["type"] == "q" else ""] for r in v["items"][:limit]]
        return {"shape": "list", "type": v["type"], "count": len(v["items"]),
                "marks": marks(v["items"]) if v["type"] == "q" else None, "rows": rows}
    total = sum(len(x["items"]) for x in v["groups"])
    return {"shape": "group", "type": v["type"], "count": len(v["groups"]), "items": total,
            "rows": [[x["name"], len(x["items"])] for x in v["groups"][:limit]]}


def _size(path):
    n = os.path.getsize(path)
    return f"{n / 1048576:.1f} MB" if n >= 1048576 else f"{max(1, round(n / 1024))} KB"


def view(g, make=False):
    """evaluate() as JSON for the page: per node, a summary of each output. A run is also
    kept as OUT/<graph id>/run.json, the overview's 上次输出."""
    r = evaluate(g, make)
    out = {"ports": {k: [_summary(x) for x in v] for k, v in r["values"].items()},
           "errors": r["errors"], "outputs": r["outputs"],
           "ran": time.strftime("%Y-%m-%d %H:%M") if make else None}
    if make:
        with open(os.path.join(out_dir(g["id"]), "run.json"), "w", encoding="utf-8") as f:
            json.dump({k: out[k] for k in ("ran", "errors", "outputs")}, f, ensure_ascii=False)
    return out


def last_run(fid):
    """The last run of a flow: {ran, errors, outputs}, or None."""
    try:
        with open(os.path.join(out_dir(fid), "run.json"), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError, KeyError):
        return None


# ------------------------------------------------------------------ storage

def _path(fid):
    if not re.fullmatch(r"[0-9a-z_-]{1,40}", fid or ""):
        raise KeyError(fid)
    return os.path.join(paths.FLOWS, fid + ".json")


def _read(path, builtin):
    with open(path, encoding="utf-8") as f:
        g = json.load(f)
    g["builtin"] = builtin
    return g


def summary(g):
    """One line for the flow list and the overview: the book, the conditions and the limit,
    joined by ，(试卷 = 1，年份 ≥ 2021，每组 2 题)."""
    labels = {k: label for f in FIELDS.values() for k, label, _ in f}
    parts, grouped = [], False
    for n in g.get("nodes", []):
        p = n.get("params") or {}
        if n["type"] == "book":
            parts.append("教材：" + BOOKS.get(p.get("book"), p.get("book", "")))
        elif n["type"] == "filter":
            parts += [f"{labels.get(c['field'], c['field'])} {c['op']} {c['value']}" for c in p.get("conds", [])
                      if c.get("field") and str(c.get("value", "")).strip()]
        elif n["type"] in ("group", "join"):
            grouped = True
        elif n["type"] == "take":
            parts.append(f"{'每组' if grouped else '前'} {p.get('n', 10)} 题")
    return "，".join(dict.fromkeys(x for x in parts if x))


def all_flows():
    out = []
    if os.path.isdir(BUILTIN):
        out += [_read(os.path.join(BUILTIN, f), True) for f in sorted(os.listdir(BUILTIN)) if f.endswith(".json")]
    if os.path.isdir(paths.FLOWS):
        user = [_read(os.path.join(paths.FLOWS, f), False) for f in os.listdir(paths.FLOWS) if f.endswith(".json")]
        out += sorted(user, key=lambda g: g["name"])
    return out


def get(fid):
    for g in all_flows():
        if g["id"] == fid:
            return g
    raise KeyError(fid)


def save(g, new=False):
    """Save a user graph (a built-in one is saved as a copy)."""
    taken = {x["name"] for x in all_flows() if x["id"] != g.get("id")}
    name = (g.get("name") or "未命名流程").strip()
    if new or g.get("builtin") or not g.get("id"):
        g = dict(g, id=uuid.uuid4().hex[:12], created=time.strftime("%Y-%m-%d %H:%M"))
        base, n = name, 2
        while name in taken:
            name, n = f"{base} {n}", n + 1
    keep = {"id": g["id"], "name": name, "created": g.get("created") or time.strftime("%Y-%m-%d %H:%M"),
            "nodes": [{k: n.get(k) for k in ("id", "type", "x", "y", "params")} for n in g.get("nodes", [])
                      if n.get("type") in NODES],
            "links": [{"from": l["from"], "to": l["to"]} for l in g.get("links", [])]}
    os.makedirs(paths.FLOWS, exist_ok=True)
    with open(_path(keep["id"]) + ".tmp", "w", encoding="utf-8") as f:
        json.dump(keep, f, ensure_ascii=False, indent=1)
    os.replace(_path(keep["id"]) + ".tmp", _path(keep["id"]))
    return dict(keep, builtin=False)


def delete(fid):
    g = get(fid)
    if g["builtin"]:
        raise PermissionError(fid)
    os.remove(_path(fid))


def out_dir(fid):
    """OUT/<flow id>; an id that is not a flow id (a path, ..) is refused with KeyError."""
    _path(fid)
    return os.path.join(OUT, fid)


def output_file(fid, name):
    try:
        p = os.path.join(out_dir(fid), os.path.basename(name))
    except KeyError:
        return None
    return p if os.path.isfile(p) else None


def catalog():
    """Node types, fields and choices for the page."""
    return {"nodes": {k: {"cat": v["cat"], "label": v["label"], "ins": [x[0] for x in v["ins"]],
                          "outs": [[x[0], x[2]] for x in v["outs"]]} for k, v in NODES.items()},
            "fields": {t: [[k, label, kind] for k, label, kind in f] for t, f in FIELDS.items()},
            "ops": OPS, "exams": EXAMS,
            "books": [{"value": k, "label": v, "pdf": bool(textbook_pdf(k))} for k, v in BOOKS.items()]}
