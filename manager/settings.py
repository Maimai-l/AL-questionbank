"""The settings page (docs/data-manager.md, section 6): the practice paper's footer and the
colour scheme, and the answer space a practice paper leaves by default (an export may choose
another), one JSON file in paths.WORK."""
import json
import os

from lib import paths

PATH = os.path.join(paths.WORK, "settings.json")
DEFAULTS = {
    "footer_name": True,        # footer: set name
    "footer_code": True,        #         paper code and question number
    "footer_page": True,        #         page number
    "theme": "system",          # system | light | dark
    "space": 3,                 # the practice paper's answer space by default, 0 (紧凑) to 3 (宽松, the original): paper.SPACE
}


def _space(v):
    """版面 as a step 0..3; past the last (a fifth step, 4, was once) is the last."""
    return max(0, min(3, v)) if type(v) is int else DEFAULTS["space"]


def load():
    try:
        with open(PATH, encoding="utf-8") as f:
            s = {**DEFAULTS, **{k: v for k, v in json.load(f).items() if k in DEFAULTS}}
    except (OSError, ValueError):
        return dict(DEFAULTS)
    s["space"] = _space(s["space"])
    return s


def save(changes):
    s = load()
    s.update({k: v for k, v in changes.items() if k in DEFAULTS and type(v) is type(DEFAULTS[k])})
    s["space"] = _space(s["space"])
    os.makedirs(paths.WORK, exist_ok=True)
    with open(PATH, "w", encoding="utf-8") as f:
        json.dump(s, f, ensure_ascii=False, indent=1)
    return s
