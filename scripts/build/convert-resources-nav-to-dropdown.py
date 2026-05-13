#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Item #28 from PPP_Sandbox_Content_Review_v3.md: convert the global
nav 'Resources' link into a dropdown containing:

  - Free Downloads          → /resources
  - PPP Glossary            → /glossary
  - Vendor Contract Audit   → /vendor-contract-audit
  - Request a PPP Review    → /ppp-review

Spec only required Glossary in the dropdown, but Vendor Contract Audit
became a real resource page in Batch 2, so it's worth surfacing in the
global nav too.

The script patches both:
  1. Visible HTML  — uses relative hrefs (./resource/ from /, ../resource/ from subdirs).
  2. React Flight payload  — uses absolute hrefs (/resources, etc.) inside $L5 wrappers.

Idempotent: if the dropdown is already present, the script skips that file.

Run from repo root:  python3 scripts/build/convert-resources-nav-to-dropdown.py
"""

import re
from pathlib import Path

def visible_dropdown(prefix: str) -> str:
    """Build the visible HTML dropdown markup with the right relative prefix."""
    return (
        '<div class="nav__dropdown">'
        '<span class="nav__link nav__dropdown-trigger" role="button" tabindex="0" aria-haspopup="true">Resources</span>'
        '<div class="nav__dropdown-menu">'
        f'<a class="nav__link" href="{prefix}resources/index.html">Free Downloads</a>'
        f'<a class="nav__link" href="{prefix}glossary/index.html">PPP Glossary</a>'
        f'<a class="nav__link" href="{prefix}vendor-contract-audit/index.html">Vendor Contract Audit</a>'
        f'<a class="nav__link" href="{prefix}ppp-review/index.html">Request a PPP Review</a>'
        '</div></div>'
    )


def payload_dropdown(key: str) -> str:
    """Build the React Flight payload dropdown (with backslash-escaped quotes).

    Mirrors the structure of the existing 'By Role' dropdown payload:
    a <div> wrapping a <span> trigger and a <div> menu of $L5 Link entries.
    """
    return (
        '[\\"$\\",\\"div\\",\\"' + key + '\\",{\\"className\\":\\"nav__dropdown\\",\\"children\\":['
        '[\\"$\\",\\"span\\",null,{\\"className\\":\\"nav__link nav__dropdown-trigger\\",\\"role\\":\\"button\\",\\"tabIndex\\":0,\\"aria-haspopup\\":\\"true\\",\\"children\\":\\"Resources\\"}],'
        '[\\"$\\",\\"div\\",null,{\\"className\\":\\"nav__dropdown-menu\\",\\"children\\":['
        '[\\"$\\",\\"$L5\\",\\"0\\",{\\"href\\":\\"/resources\\",\\"className\\":\\"nav__link\\",\\"children\\":\\"Free Downloads\\"}],'
        '[\\"$\\",\\"$L5\\",\\"1\\",{\\"href\\":\\"/glossary\\",\\"className\\":\\"nav__link\\",\\"children\\":\\"PPP Glossary\\"}],'
        '[\\"$\\",\\"$L5\\",\\"2\\",{\\"href\\":\\"/vendor-contract-audit\\",\\"className\\":\\"nav__link\\",\\"children\\":\\"Vendor Contract Audit\\"}],'
        '[\\"$\\",\\"$L5\\",\\"3\\",{\\"href\\":\\"/ppp-review\\",\\"className\\":\\"nav__link\\",\\"children\\":\\"Request a PPP Review\\"}]'
        ']}]'
        ']}]'
    )


def patch_visible(content: str, prefix: str) -> tuple[str, bool]:
    """Replace the flat Resources <a> with the dropdown <div>."""
    # Idempotency: if a Resources dropdown trigger already exists, skip.
    if '<span class="nav__link nav__dropdown-trigger" role="button" tabindex="0" aria-haspopup="true">Resources</span>' in content:
        return content, False

    # Flat link variants:
    #   ./resources/index.html / ../resources/index.html / ../../... (static export)
    #   /resources (production-style HTML after live sync)
    patterns = [
        re.compile(r'<a class="nav__link" href="(?:\.\./)*\.?/?resources/index\.html">Resources</a>'),
        re.compile(r'<a class="nav__link" href="/resources">Resources</a>'),
    ]
    for pattern in patterns:
        m = pattern.search(content)
        if m:
            return content[: m.start()] + visible_dropdown(prefix) + content[m.end():], True
    return content, False


def patch_payload(content: str) -> tuple[str, bool]:
    """Replace the $L5 Resources link in the React Flight payload with a
    dropdown div carrying the same nav position key (typically '5').
    """
    # Idempotency check on payload side
    if '\\"nav__link nav__dropdown-trigger\\",\\"role\\":\\"button\\",\\"tabIndex\\":0,\\"aria-haspopup\\":\\"true\\",\\"children\\":\\"Resources\\"' in content:
        return content, False

    # Match: ,["$","$L5","5",{"href":"/resources","className":"nav__link","children":"Resources"}]
    # (all backslash-escaped because it lives inside a JS string literal)
    pattern = re.compile(
        r'\[\\"\$\\",\\"\$L5\\",\\"(\d+)\\",\{\\"href\\":\\"/resources\\",\\"className\\":\\"nav__link\\",\\"children\\":\\"Resources\\"\}\]'
    )
    m = pattern.search(content)
    if not m:
        return content, False
    key = m.group(1)
    return content[: m.start()] + payload_dropdown(key) + content[m.end():], True


def main():
    results = []
    for fp in PAGES:
        path = Path(fp)
        if not path.exists():
            results.append((fp, "missing", False, False))
            continue
        content = path.read_text(encoding="utf-8")

        # Determine relative prefix based on file depth
        # All files are either at root (index.html) or one level deep (subdir/index.html)
        depth = fp.count("/")
        prefix = "./" if depth == 0 else "../"

        new_content, vis_changed = patch_visible(content, prefix)
        new_content, pl_changed = patch_payload(new_content)

        if vis_changed or pl_changed:
            path.write_text(new_content, encoding="utf-8")
        results.append((fp, "patched" if (vis_changed or pl_changed) else "skipped", vis_changed, pl_changed))

    print("Resources nav dropdown conversion:")
    for fp, status, v, p in results:
        marker = {"patched": "→", "skipped": "✓", "missing": "?"}[status]
        suffix = f"visible={'Y' if v else 'N'} payload={'Y' if p else 'N'}"
        print(f"  {marker} {fp:<48} {status:<8} {suffix}")
    patched = sum(1 for _, s, _, _ in results if s == "patched")
    print(f"\nTotal: patched {patched} file(s)")


if __name__ == "__main__":
    main()
