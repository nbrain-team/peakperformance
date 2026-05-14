# -*- coding: utf-8 -*-
"""Add the global 'Three ways in.' CTA block to every page that doesn't have it.

P1-2 follow-up (May 2026 punch list, user clarification):
  > "i want this on every page bottom for CTA, like it is on /about and some other pages"

The canonical block already lives on all 13 marketing/role pages (about, book,
resources, podcast hub, ppp-review, 5c-framework, the 4 role pages, glossary,
vendor-contract-audit, be-on-the-show). It is missing from the home page and
all 34 podcast episode pages — 35 pages total — which is what this script
fixes.

Strategy:
  1. Walk all *.html files under the repo (excluding _next, public, etc.).
  2. Skip any file that already contains 'three-ways-blocks' (idempotent).
  3. Determine relative-path depth from the file's location:
       depth 0  → home page (`./book/...`)
       depth 1  → marketing pages (`../book/...`)        — already shipped
       depth 2  → podcast episode pages (`../../book/...`)
  4. Insert the depth-appropriate block immediately before `</main>`.
     Fall back to inserting before `<footer ` if `</main>` is missing.

Run from repo root:
    python3 scripts/edits/add-three-ways-cta.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


SKIP_DIRS = {".git", "_next", ".venv", "node_modules", "public", "_external", "scripts", "docs", "transcripts"}


def block_for_prefix(prefix: str) -> str:
    """Render the canonical block with the given href prefix.

    `prefix` examples: "./", "../", "../../"
    """
    return (
        '<section class="cta-section cta-section--dark three-ways-blocks">'
        '<div class="container">'
        '<span class="eyebrow no-rule" style="justify-content:center;display:flex">Get Started</span>'
        '<h2 class="mt-4 mb-4">Three ways in.</h2>'
        '<p class="lede three-ways-blocks__lede" style="max-width:52ch;margin-inline:auto">'
        "Whether you&#x27;re scouting, training camp, or game time — there&#x27;s a way to start today."
        "</p>"
        '<div class="three-ways-blocks__cta-rows">'
        '<div class="three-ways-blocks__cta-row three-ways-blocks__cta-row--primary">'
        f'<a class="btn btn-primary btn-lg" href="{prefix}book/index.html#retailers">Get the book</a>'
        f'<a class="btn btn-primary btn-lg" href="{prefix}book/index.html#audiobook-retailers">Listen to the book</a>'
        f'<a class="btn btn-primary btn-lg" href="{prefix}podcast/index.html">Listen to the podcast</a>'
        "</div>"
        '<div class="three-ways-blocks__cta-row three-ways-blocks__cta-row--secondary">'
        f'<a class="btn btn-lg three-ways-blocks__cta-review" href="{prefix}ppp-review/index.html">Request PPP Review</a>'
        "</div></div></div></section>"
    )


def depth_of(rel_path: str) -> int:
    """Return how many directories deep the file is from repo root.

    `index.html`                       → 0
    `book/index.html`                  → 1
    `podcast/<slug>/index.html`        → 2
    """
    parts = Path(rel_path).parts
    return max(0, len(parts) - 1)


def prefix_for_depth(d: int) -> str:
    if d == 0:
        return "./"
    return "../" * d


def insert_block(html: str, block: str) -> tuple[str, str]:
    """Return (new_html, where) — `where` is 'main', 'footer', or 'none'."""
    anchor = "</main>"
    i = html.rfind(anchor)
    if i != -1:
        return html[:i] + block + html[i:], "main"
    anchor2 = "<footer "
    i = html.find(anchor2)
    if i != -1:
        return html[:i] + block + html[i:], "footer"
    return html, "none"


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    os.chdir(repo_root)

    updated, skipped, failed = [], [], []
    for root, dirs, names in os.walk("."):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
        for n in names:
            if not n.endswith(".html"):
                continue
            rel = os.path.relpath(os.path.join(root, n), ".")
            with open(rel, encoding="utf-8") as fh:
                src = fh.read()
            if "three-ways-blocks" in src:
                skipped.append(rel)
                continue
            d = depth_of(rel)
            block = block_for_prefix(prefix_for_depth(d))
            new, where = insert_block(src, block)
            if where == "none":
                failed.append(rel)
                continue
            with open(rel, "w", encoding="utf-8") as fh:
                fh.write(new)
            updated.append((rel, where))

    print(f"UPDATED ({len(updated)}):")
    for rel, where in sorted(updated):
        print(f"   + {rel:80s}  [inserted before {where}]")
    print(f"\nSKIPPED — already had block ({len(skipped)}):")
    for rel in sorted(skipped):
        print(f"   = {rel}")
    if failed:
        print(f"\nFAILED — no </main> or <footer> anchor ({len(failed)}):")
        for rel in sorted(failed):
            print(f"   ! {rel}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
