#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Item #34 from PPP_Sandbox_Content_Review_v3.md: enforce ® consistency.

Every appearance of 'Peak Property Performance' should be 'Peak Property
Performance®'. Auto-fix across all HTML files. Idempotent.

Scope of fixes:
  - JSON-LD schema fields (name, alternateName, description, publisher.name)
  - HTML alt text and visible copy
  - React Flight payload strings (escaped or otherwise)

Skipped on purpose:
  - URLs containing 'peakpropertyperformance' (no trademark in domains)
  - Strings already containing 'Peak Property Performance®' (idempotency)

Run from repo root:  python3 scripts/build/fix-trademark-consistency.py
"""

import re
from pathlib import Path

FILES = [
    "index.html",
    "book/index.html",
    "about/index.html",
    "5c-framework/index.html",
    "podcast/index.html",
    "resources/index.html",
    "ppp-review/index.html",
    "for-owners/index.html",
    "for-asset-managers/index.html",
    "for-property-managers/index.html",
    "for-it-managers/index.html",
    "glossary/index.html",
    "vendor-contract-audit/index.html",
    "be-on-the-show/index.html",
]

# Pattern: 'Peak Property Performance' NOT followed by ® and NOT inside a URL.
# We use a negative lookbehind for hostname prefixes (peakpropertyperformance.com)
# and a negative lookahead for ® (so already-fixed strings are untouched).
PATTERN = re.compile(r"Peak Property Performance(?!\xae)")


def looks_like_url_context(content: str, match_start: int) -> bool:
    """Skip matches that are inside obvious URL strings — those use the
    lower-cased domain form (peakpropertyperformance.com) not the
    Title Case prose form. We only need to guard against an edge case
    where prose 'Peak Property Performance' appears immediately inside
    a URL path. In practice this doesn't happen, but be safe."""
    # check 20 chars on either side for '://' or '.com'
    window = content[max(0, match_start - 30):match_start + 30]
    return "://" in window and content[match_start - 1:match_start] not in (' ', '>', '"', "'", '\\', '\n')


def fix(content: str) -> tuple[str, int]:
    # Use a function replacement so we can skip URL contexts.
    fixes = 0

    def repl(m):
        nonlocal fixes
        if looks_like_url_context(content, m.start()):
            return m.group(0)
        fixes += 1
        return "Peak Property Performance\xae"

    new_content = PATTERN.sub(repl, content)
    return new_content, fixes


def main():
    total_fixes = 0
    file_results = []
    for fp in FILES:
        path = Path(fp)
        if not path.exists():
            file_results.append((fp, "missing", 0))
            continue
        original = path.read_text(encoding="utf-8")
        fixed, count = fix(original)
        if count > 0:
            path.write_text(fixed, encoding="utf-8")
            file_results.append((fp, "patched", count))
            total_fixes += count
        else:
            file_results.append((fp, "ok", 0))

    print("Trademark consistency report:")
    for fp, status, count in file_results:
        marker = {"ok": "✓", "patched": "→", "missing": "?"}[status]
        if count > 0:
            print(f"  {marker} {fp:<48} {count} ® inserted")
        else:
            print(f"  {marker} {fp:<48} {status}")
    print(f"\nTotal: {total_fixes} ® insertions across {sum(1 for _,s,_ in file_results if s == 'patched')} files")


if __name__ == "__main__":
    main()
