# -*- coding: utf-8 -*-
"""Add an 'FAQ' entry to the Resources nav dropdown on every HTML page.

Inserts the link right after 'PPP Glossary' and before 'Vendor Contract Audit'.
Depth-aware: uses '../faq/index.html' on 1-deep pages and '../../faq/index.html'
on 2-deep podcast episode pages.

Also adds an 'FAQ' link to the footer's 'Get Started' column (between
'Free Resources' and 'Request a PPP Review').

Idempotent: skips pages that already contain '/faq/index.html'.

Run from repo root:
    python3 scripts/edits/add-faq-nav-link.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

SKIP_DIRS = {".git", "_next", ".venv", "node_modules", "public", "_external", "scripts", "docs", "transcripts"}


def depth_of(rel_path: str) -> int:
    return max(0, len(Path(rel_path).parts) - 1)


def prefix_for_depth(d: int) -> str:
    if d == 0:
        return "./"
    return "../" * d


def patch(html: str, prefix: str) -> tuple[str, list[str]]:
    """Return (new_html, [actions...])."""
    actions: list[str] = []
    new = html

    # --- Nav dropdown insert (between PPP Glossary and Vendor Contract Audit) ---
    nav_glossary = (
        f'<a class="nav__link" href="{prefix}glossary/index.html">PPP Glossary</a>'
        f'<a class="nav__link" href="{prefix}vendor-contract-audit/index.html">Vendor Contract Audit</a>'
    )
    nav_glossary_with_faq = (
        f'<a class="nav__link" href="{prefix}glossary/index.html">PPP Glossary</a>'
        f'<a class="nav__link" href="{prefix}faq/index.html">FAQ</a>'
        f'<a class="nav__link" href="{prefix}vendor-contract-audit/index.html">Vendor Contract Audit</a>'
    )
    if nav_glossary in new and nav_glossary_with_faq not in new:
        new = new.replace(nav_glossary, nav_glossary_with_faq, 1)
        actions.append("nav")

    # --- Footer link insert (between Free Resources and Request a PPP Review) ---
    footer_anchor = (
        f'<a class="footer__link" href="{prefix}resources/index.html">Free Resources</a>'
        f'<a class="footer__link" href="{prefix}ppp-review/index.html">Request a PPP Review</a>'
    )
    footer_with_faq = (
        f'<a class="footer__link" href="{prefix}resources/index.html">Free Resources</a>'
        f'<a class="footer__link" href="{prefix}faq/index.html">FAQ</a>'
        f'<a class="footer__link" href="{prefix}ppp-review/index.html">Request a PPP Review</a>'
    )
    if footer_anchor in new and footer_with_faq not in new:
        new = new.replace(footer_anchor, footer_with_faq, 1)
        actions.append("footer")

    return new, actions


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    os.chdir(repo_root)

    updated, skipped, partial = [], [], []
    for root, dirs, names in os.walk("."):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
        for n in names:
            if not n.endswith(".html"):
                continue
            rel = os.path.relpath(os.path.join(root, n), ".")
            with open(rel, encoding="utf-8") as fh:
                src = fh.read()
            # Skip the new FAQ page itself
            if rel == os.path.join("faq", "index.html"):
                skipped.append((rel, "is /faq itself"))
                continue
            d = depth_of(rel)
            prefix = prefix_for_depth(d)
            new, actions = patch(src, prefix)
            if not actions:
                skipped.append((rel, "no anchor found or already patched"))
                continue
            with open(rel, "w", encoding="utf-8") as fh:
                fh.write(new)
            if len(actions) == 2:
                updated.append((rel, "nav+footer"))
            else:
                partial.append((rel, "+".join(actions)))

    print(f"UPDATED ({len(updated)}):")
    for rel, a in sorted(updated):
        print(f"   + {rel:80s}  [{a}]")
    if partial:
        print(f"\nPARTIAL — only one of nav/footer patched ({len(partial)}):")
        for rel, a in sorted(partial):
            print(f"   ~ {rel:80s}  [{a}]")
    print(f"\nSKIPPED ({len(skipped)}):")
    for rel, why in sorted(skipped):
        print(f"   = {rel:80s}  [{why}]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
