"""Question sets (docs/data-manager.md, F3): one JSON file each in paths.SETS.

    {"id", "name", "source": "query" | "paper" | "import" | "manual",
     "created": "YYYY-MM-DD HH:MM", "items": [question ids, in order]}

Exchange format with the model is `alevel-question-set/v1` (docs/INTEGRATION.md).
"""
import json
import os
import re
import time
import uuid

from lib import paths

SCHEMA = "alevel-question-set/v1"


def _path(sid):
    if not re.fullmatch(r"[0-9a-f]{12}", sid or ""):
        raise KeyError(sid)
    return os.path.join(paths.SETS, sid + ".json")


def _now():
    return time.strftime("%Y-%m-%d %H:%M")


def all_sets():
    if not os.path.isdir(paths.SETS):
        return []
    out = []
    for f in os.listdir(paths.SETS):
        if f.endswith(".json"):
            with open(os.path.join(paths.SETS, f), encoding="utf-8") as fh:
                out.append(json.load(fh))
    return sorted(out, key=lambda s: s["created"], reverse=True)


def get(sid):
    with open(_path(sid), encoding="utf-8") as f:
        return json.load(f)


def save(s):
    os.makedirs(paths.SETS, exist_ok=True)
    tmp = _path(s["id"]) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(s, f, ensure_ascii=False, indent=1)
    os.replace(tmp, _path(s["id"]))
    return s


def unique_name(name):
    taken = {s["name"] for s in all_sets()}
    if name not in taken:
        return name
    n = 2
    while f"{name} {n}" in taken:
        n += 1
    return f"{name} {n}"


def create(name, items, source="manual"):
    seen, ordered = set(), []
    for q in items:
        if q not in seen:
            seen.add(q)
            ordered.append(q)
    return save({"id": uuid.uuid4().hex[:12], "name": unique_name(name.strip() or "题组"),
                 "source": source, "created": _now(), "items": ordered})


def update(sid, name=None, items=None, add=None):
    s = get(sid)
    if name is not None and name.strip():
        s["name"] = name.strip()
    if items is not None:
        s["items"] = list(dict.fromkeys(items))
    if add:
        s["items"] += [q for q in dict.fromkeys(add) if q not in s["items"]]
    return save(s)


def delete(sid):
    os.remove(_path(sid))


def export(s):
    return {"schema": SCHEMA, "title": s["name"],
            "items": [{"archive_id": "data-manager", "question_ids": s["items"]}]}


def parse_import(data):
    """Question ids from an alevel-question-set/v1 document (or a bare list)."""
    if isinstance(data, list):
        return [str(q) for q in data], None
    if data.get("schema") != SCHEMA:
        raise ValueError("文件不是 alevel-question-set/v1 格式")
    ids = []
    for item in data.get("items", []):
        ids += [str(q) for q in item.get("question_ids", [])]
    return ids, data.get("title")


def import_name():
    return unique_name("导入 " + time.strftime("%Y-%m-%d"))
