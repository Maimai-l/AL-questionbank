"""The settings page (docs/data-manager.md, section 6): question-paper layout and theme,
one JSON file in paths.WORK."""
import json
import os

from lib import paths

PATH = os.path.join(paths.WORK, "settings.json")
DEFAULTS = {
    "cie_space": True,          # CIE questions with the paper's answer space
    "adm_layout": "two",        # admissions tests: "two" per page, half a page each; "flow"
    "footer_name": True,        # footer: set name
    "footer_code": True,        #         paper code and question number
    "footer_page": True,        #         page number
    "theme": "system",          # system | light | dark
}


def load():
    try:
        with open(PATH, encoding="utf-8") as f:
            return {**DEFAULTS, **{k: v for k, v in json.load(f).items() if k in DEFAULTS}}
    except (OSError, ValueError):
        return dict(DEFAULTS)


def save(changes):
    s = load()
    s.update({k: v for k, v in changes.items() if k in DEFAULTS and type(v) is type(DEFAULTS[k])})
    os.makedirs(paths.WORK, exist_ok=True)
    with open(PATH, "w", encoding="utf-8") as f:
        json.dump(s, f, ensure_ascii=False, indent=1)
    return s
