#!/usr/bin/env python3
"""
apply-edits.py — surgical text/markup replacements in Next.js static-export HTML.

Each file has TWO copies of every text string:
  1. The pre-rendered HTML body (uses HTML entities: &#x27; &amp; etc.)
  2. The React Flight payload at the bottom, which is a JS string literal
     where every double quote is already escaped as \\"

When the page hydrates, React replaces the DOM with whatever's in the Flight
payload. So every change has to be made in BOTH places or it'll flash on
screen and disappear.

Edits files are Python modules that expose:
    FILE = "relative/path/to/index.html"
    EDITS = [
        {
            "label": "human description",
            "html": (old_html, new_html),         # body change (HTML entities)
            "payload": (old_payload, new_payload),# Flight payload, RAW JSON
            "html_count": 1,
            "payload_count": 1,
            "optional": False,
        },
        ...
    ]

The script automatically converts `payload` raw-JSON strings to their
JS-string-literal escaped form (`"` -> `\"`, `\\` -> `\\\\`) before
searching/replacing. Pass `payload_raw=True` to opt out.

Usage:
    python3 scripts/apply-edits.py scripts/edits/<name>.py
"""
import importlib.util
import sys
from pathlib import Path


def to_js_string_literal_escape(s: str) -> str:
    """Convert raw JSON content to its file-literal form.

    Next.js's React Server Components serializer puts the Flight payload
    inside a JS string literal:
        self.__next_f.push([1,"...content..."])
    Inside that JS string, the JSON is encoded with these substitutions
    (in addition to standard JS string escaping):
      \\  -> \\\\
      "  -> \\"
      &  -> \\u0026   (so HTML can't accidentally see an entity start)
      <  -> \\u003c   (so the browser can't see </script>)
      >  -> \\u003e
    Order matters: backslash first, then quotes, then HTML-special chars.
    """
    return (s
            .replace("\\", "\\\\")
            .replace('"', '\\"')
            .replace("&", "\\u0026")
            .replace("<", "\\u003c")
            .replace(">", "\\u003e"))


def main():
    if len(sys.argv) != 2:
        print("usage: apply-edits.py <edits.py>", file=sys.stderr)
        sys.exit(2)

    spec_path = Path(sys.argv[1])
    if not spec_path.exists():
        print(f"ERROR: {spec_path} not found", file=sys.stderr)
        sys.exit(2)

    spec = importlib.util.spec_from_file_location("edits_module", spec_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    repo_root = Path(__file__).resolve().parent.parent
    target = repo_root / mod.FILE
    if not target.exists():
        print(f"ERROR: {target} not found", file=sys.stderr)
        sys.exit(2)

    src = target.read_text()
    new = src
    log = []

    for r in mod.EDITS:
        label = r.get("label", "(unlabeled)")
        optional = r.get("optional", False)

        pairs = []  # list of (kind, old, new, expected_count)
        if "both" in r:
            old, repl = r["both"]
            pairs.append(("both", old, repl, r.get("count", None)))
        if "html" in r:
            old, repl = r["html"]
            pairs.append(("html", old, repl, r.get("html_count", 1)))
        if "payload" in r:
            old, repl = r["payload"]
            if not r.get("payload_raw", False):
                old = to_js_string_literal_escape(old)
                repl = to_js_string_literal_escape(repl)
            pairs.append(("payload", old, repl, r.get("payload_count", 1)))

        if not pairs:
            print(f"ERROR [{label}]: no html/payload/both keys", file=sys.stderr)
            sys.exit(2)

        for kind, old, repl, expected in pairs:
            actual = new.count(old)
            if actual == 0:
                if optional:
                    log.append(f"  - skip   [{label}] ({kind}): not found (optional)")
                    continue
                print(f"ERROR [{label}] ({kind}): pattern not found", file=sys.stderr)
                print(f"  searched for: {old[:200]!r}", file=sys.stderr)
                sys.exit(1)
            if expected is not None and actual != expected:
                print(f"ERROR [{label}] ({kind}): expected {expected} occurrences, found {actual}", file=sys.stderr)
                print(f"  searched for: {old[:200]!r}", file=sys.stderr)
                sys.exit(1)
            new = new.replace(old, repl)
            log.append(f"  - ok     [{label}] ({kind}): replaced {actual}x")

    if new == src:
        print(f"NO CHANGES applied to {mod.FILE}", file=sys.stderr)
        sys.exit(0)

    target.write_text(new)
    print(f"OK: {mod.FILE}")
    for line in log:
        print(line)


if __name__ == "__main__":
    main()
