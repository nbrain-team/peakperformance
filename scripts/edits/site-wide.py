# -*- coding: utf-8 -*-
"""Site-wide #34 — expand standalone 'infrastructure' to
'data and digital infrastructure' in marketing-page prose.

Three real hits (not slugs, not titles, not structured data):
  index.html         — "treat infrastructure as a strategic asset"
  about/index.html   — "naive about the infrastructure that ran it"
  5c-framework/...   — "Clarify first — then build infrastructure to match"

Applied as individual entries so the script reports each one clearly.
"""

from pathlib import Path


def to_js_string_literal_escape(s: str) -> str:
    return (s
            .replace("\\", "\\\\")
            .replace('"', '\\"')
            .replace("&", "\\u0026")
            .replace("<", "\\u003c")
            .replace(">", "\\u003e"))


CHANGES = [
    ("index.html",
     "treat infrastructure as a strategic asset",
     "treat data and digital infrastructure as a strategic asset"),
    ("about/index.html",
     "naive about the infrastructure that ran it",
     "naive about the data and digital infrastructure that ran it"),
    ("5c-framework/index.html",
     "Clarify first — then build infrastructure to match",
     "Clarify first — then build data and digital infrastructure to match"),
]


def main():
    repo_root = Path(__file__).resolve().parent.parent.parent
    for file, old, new in CHANGES:
        path = repo_root / file
        src = path.read_text()
        # Replace in visible HTML literal (no entities involved in these phrases)
        # and in Flight payload (no encoding diff needed since no quotes/&/</>)
        cnt = src.count(old)
        if cnt == 0:
            print(f"  SKIP {file}: pattern not found")
            continue
        new_content = src.replace(old, new)
        path.write_text(new_content)
        print(f"  OK   {file}: replaced {cnt}x ({old!r} → {new!r})")


if __name__ == "__main__":
    main()
