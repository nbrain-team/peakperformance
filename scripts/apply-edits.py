#!/usr/bin/env python3
"""
apply-edits.py — surgical text/markup replacements in Next.js static-export HTML.

Each file has TWO copies of every text string:
  1. The pre-rendered HTML body (uses HTML entities: &#x27; &amp; etc.)
  2. The React Flight payload at the bottom (JSON-escaped: raw ' & etc.)

When the page hydrates, React replaces the DOM with whatever's in the Flight
payload. So every change has to be made in both places or it'll flash on
screen and disappear.

Usage:
    python3 scripts/apply-edits.py <edits.json>

edits.json schema:
{
  "file": "index.html",
  "replacements": [
    {
      "label": "human description",
      "html": ["old html", "new html"],          # body change (HTML-entity encoded)
      "payload": ["old payload", "new payload"], # Flight payload change (raw json string)
      "html_count": 1,                            # expected occurrences (defaults to 1)
      "payload_count": 1,
      "optional": false                           # if true, missing matches don't fail
    }
  ]
}

If `html` and `payload` are omitted, you can use `both` as a single pair
that gets applied in BOTH locations (safe when there are no characters
that escape differently).

Exits non-zero on any unexpected match count.
"""
import json
import sys
from pathlib import Path


def main():
    if len(sys.argv) != 2:
        print("usage: apply-edits.py <edits.json>", file=sys.stderr)
        sys.exit(2)

    spec_path = Path(sys.argv[1])
    spec = json.loads(spec_path.read_text())

    repo_root = Path(__file__).resolve().parent.parent
    target = repo_root / spec["file"]
    if not target.exists():
        print(f"ERROR: {target} not found", file=sys.stderr)
        sys.exit(2)

    src = target.read_text()
    new = src
    log = []

    for r in spec["replacements"]:
        label = r.get("label", "(unlabeled)")
        optional = r.get("optional", False)

        pairs = []
        if "both" in r:
            old, repl = r["both"]
            pairs.append(("both", old, repl, r.get("count", None)))
        else:
            if "html" in r:
                old, repl = r["html"]
                pairs.append(("html", old, repl, r.get("html_count", 1)))
            if "payload" in r:
                old, repl = r["payload"]
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
                print(f"ERROR [{label}] ({kind}): pattern not found:\n    {old[:200]!r}", file=sys.stderr)
                sys.exit(1)
            if expected is not None and actual != expected:
                print(f"ERROR [{label}] ({kind}): expected {expected} occurrences, found {actual}\n    {old[:200]!r}", file=sys.stderr)
                sys.exit(1)
            new = new.replace(old, repl)
            log.append(f"  - ok     [{label}] ({kind}): replaced {actual}x")

    if new == src:
        print(f"NO CHANGES applied to {spec['file']}", file=sys.stderr)
        sys.exit(0)

    target.write_text(new)
    print(f"OK: {spec['file']}")
    for line in log:
        print(line)


if __name__ == "__main__":
    main()
