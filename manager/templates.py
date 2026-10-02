"""Export templates (docs/data-manager.md, F8 and section 7): a Markdown file whose YAML
front matter holds the export options and whose body is the README text.

Built-in templates live in manager/templates/ and cannot be changed; the user's are
in paths.WORK/templates/, one file each, named by id.
"""
import os
import re
import uuid

import yaml

from lib import paths

BUILTIN = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
USER = os.path.join(paths.WORK, "templates")

DEFAULTS = {
    "per_question": ["image"],
    "documents": [],
    "answers": "none",
    "layout": "folder_per_question",
    "filename": "{index:02}_{paper_code}_Q{q}",
    "answer_filename": "answers",
    "manifest": True,
    "summary": False,
    "prompt_file": "README.md",
}
CHOICES = {
    "per_question": {"image", "image_with_space", "text", "mark_scheme", "explanation"},
    "documents": {"mark_scheme", "explanation", "question_paper"},
    "answers": {"none", "written_pdf"},
    "layout": {"folder_per_question", "flat"},
}


def clean(settings):
    """Settings with unknown keys dropped and bad values replaced by the defaults."""
    out = dict(DEFAULTS)
    for k, v in (settings or {}).items():
        if k not in DEFAULTS:
            continue
        if k in ("per_question", "documents"):
            if isinstance(v, list) and all(x in CHOICES[k] for x in v):
                out[k] = list(dict.fromkeys(v))
        elif k in CHOICES:
            if v in CHOICES[k]:
                out[k] = v
        elif isinstance(v, type(DEFAULTS[k])):
            out[k] = v.strip() if isinstance(v, str) else v
    if not any(x in out["per_question"] for x in ("image", "image_with_space", "text")):
        out["per_question"] = ["image"] + out["per_question"]
    if not re.fullmatch(r"[^/\\]+", out["answer_filename"]):
        out["answer_filename"] = DEFAULTS["answer_filename"]
    if out["prompt_file"] and not re.fullmatch(r"[^/\\]+", out["prompt_file"]):
        out["prompt_file"] = DEFAULTS["prompt_file"]
    return out


def parse(text):
    """(name, settings, body) of a template file."""
    m = re.match(r"---\n(.*?)\n---\n?(.*)", text, re.S)
    meta, body = (yaml.safe_load(m.group(1)) or {}, m.group(2)) if m else ({}, text)
    name = str(meta.pop("name", "") or "").strip()
    return name, clean(meta), body.strip("\n") + "\n"


def dump(name, settings, body):
    head = yaml.safe_dump({"name": name, **clean(settings)}, allow_unicode=True,
                          sort_keys=False, default_flow_style=None).strip()
    return f"---\n{head}\n---\n{body.strip(chr(10))}\n"


def _read(path, tid, builtin):
    with open(path, encoding="utf-8") as f:
        name, settings, body = parse(f.read())
    return {"id": tid, "name": name or tid, "builtin": builtin, "settings": settings, "body": body}


def all_templates():
    out = []
    for folder, builtin in ((BUILTIN, True), (USER, False)):
        if os.path.isdir(folder):
            for f in sorted(os.listdir(folder)):
                if f.endswith(".md"):
                    out.append(_read(os.path.join(folder, f), f[:-3], builtin))
    builtins = [t for t in out if t["builtin"]]
    return builtins + sorted((t for t in out if not t["builtin"]), key=lambda t: t["name"])


def get(tid):
    for t in all_templates():
        if t["id"] == tid:
            return t
    raise KeyError(tid)


def _unique(name, skip=None):
    taken = {t["name"] for t in all_templates() if t["id"] != skip}
    name = name.strip() or "模板"
    if name not in taken:
        return name
    n = 2
    while f"{name} {n}" in taken:
        n += 1
    return f"{name} {n}"


def _write(tid, name, settings, body):
    os.makedirs(USER, exist_ok=True)
    path = os.path.join(USER, tid + ".md")
    with open(path + ".tmp", "w", encoding="utf-8") as f:
        f.write(dump(name, settings, body))
    os.replace(path + ".tmp", path)
    return _read(path, tid, False)


def create(name, settings, body):
    return _write(uuid.uuid4().hex[:12], _unique(name), settings, body)


def update(tid, name=None, settings=None, body=None):
    t = get(tid)
    if t["builtin"]:
        raise PermissionError(tid)
    return _write(tid, _unique(name, tid) if name is not None else t["name"],
                  settings if settings is not None else t["settings"],
                  body if body is not None else t["body"])


def delete(tid):
    t = get(tid)
    if t["builtin"]:
        raise PermissionError(tid)
    os.remove(os.path.join(USER, tid + ".md"))
