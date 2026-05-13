# -*- coding: utf-8 -*-
"""Verify every internal href in *.html resolves to an existing site file.

Skips mailto:, tel:, http(s):, //, javascript:, and fragment-only links.

Run from repo root: python3 scripts/audit-internal-links.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
HREF_RE = re.compile(r'''href\s*=\s*["']([^"'<>]+)["']''', re.I)


def main() -> int:
    broken: list[tuple[str, str, str]] = []

    for html_path in sorted(ROOT.rglob("*.html")):
        site_rel = html_path.relative_to(ROOT)
        text = html_path.read_text(encoding="utf-8", errors="replace")

        for m in HREF_RE.finditer(text):
            href = m.group(1).strip()
            if not href or href.startswith("#"):
                continue
            if href.startswith(("mailto:", "tel:", "javascript:", "data:", "//")):
                continue
            parsed = urlparse(href)
            if parsed.scheme in ("http", "https"):
                continue

            path_only = href.split("?", 1)[0].split("#", 1)[0]
            base = (ROOT / site_rel).parent
            target = (base / path_only).resolve()
            try:
                rel = target.relative_to(ROOT.resolve()).as_posix()
            except ValueError:
                broken.append((site_rel.as_posix(), href, "__outside_repo__"))
                continue

            p = ROOT / rel
            if not p.is_file():
                broken.append((site_rel.as_posix(), href, rel))

    if not broken:
        print("OK — all internal href targets exist as files.")
        return 0

    print(f"FAIL — {len(broken)} broken link(s):\n")
    for src, href, resolved in broken:
        print(f"  {src}\n    href={href!r}\n    → {resolved}\n")
    return 1


if __name__ == "__main__":
    sys.exit(main())
