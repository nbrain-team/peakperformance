# -*- coding: utf-8 -*-
"""P2-1 — Apply the targeted trademark + language fixes identified by the audit.

Scope (per audit triage):
  • glossary/index.html: "5C Framework" → "5C™ Framework" (13 occurrences in
    schema names, descriptions, and prose; URL slugs left alone via lookahead)
  • 5c-framework/index.html: "build infrastructure to match" → "build data and
    digital infrastructure to match"  (1 occurrence in body thesis copy)
  • about/index.html: "naive about the infrastructure that ran it" → "naive
    about the data and digital infrastructure that ran it"  (1 occurrence)
  • index.html: meta description — drop "Game-changing plays for owners…"
    (1 occurrence)
  • podcast/index.html: hero H1 — drop "Game-changing CRE strategy, every
    week." (1 occurrence)

Idempotent. Run from repo root:
    python3 scripts/edits/p2-1-apply.py
"""

from __future__ import annotations
import os
import re
import sys
from pathlib import Path

# (path, label, before_pattern_or_str, after_str, count_expected_first_run)
EDITS = [
    # --- 1. 5C Framework → 5C™ Framework on glossary (regex; protects URL slugs and existing ™) ---
    (
        "glossary/index.html",
        "5C Framework → 5C™ Framework",
        re.compile(r"5C(?!™|&trade;|&#8482;) Framework"),
        "5C™ Framework",
        13,
    ),
    # --- 2. /5c-framework body copy: build infrastructure → build data and digital infrastructure ---
    (
        "5c-framework/index.html",
        "build infrastructure → build data and digital infrastructure",
        "build infrastructure to match",
        "build data and digital infrastructure to match",
        1,
    ),
    # --- 3. /about body copy: naive about the infrastructure → naive about the data and digital infrastructure ---
    (
        "about/index.html",
        "naive about the infrastructure → naive about the data and digital infrastructure",
        "naive about the infrastructure that ran it",
        "naive about the data and digital infrastructure that ran it",
        1,
    ),
    # --- 4. /index.html meta description: drop "Game-changing plays" filler ---
    #     Current: "...Game-changing plays for owners who want NOI growth, AI readiness, and control..."
    #     New:     "...The plays for owners who want NOI growth, AI readiness, and control..."
    (
        "index.html",
        "meta description: drop 'Game-changing plays' filler",
        "Game-changing plays for owners",
        "The plays for owners",
        1,
    ),
    # --- 5. /podcast hero H1: drop "Game-changing" filler ---
    #     Current: "Game-changing CRE strategy, every week."
    #     New:     "CRE strategy, every week."
    (
        "podcast/index.html",
        "hero H1: 'Game-changing CRE strategy' → 'CRE strategy'",
        "Game-changing CRE strategy, every week.",
        "CRE strategy, every week.",
        1,
    ),
]


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    os.chdir(repo_root)

    print("=" * 100)
    print("P2-1 — Trademark + language fixes (targeted, idempotent)")
    print("=" * 100)

    total_changes = 0
    for path, label, before, after, expected in EDITS:
        with open(path, encoding="utf-8") as fh:
            src = fh.read()

        if isinstance(before, re.Pattern):
            new, n = before.subn(after, src)
        else:
            n = src.count(before)
            new = src.replace(before, after)

        already_done = (n == 0) and (after in src)
        status = "APPLIED" if n > 0 else ("ALREADY-DONE" if already_done else "NO-MATCH")

        if n > 0:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(new)
            total_changes += n

        print(f"\n  📄 {path}")
        print(f"     edit: {label}")
        print(f"     {status}  (matched {n} time(s); first-run expected {expected})")

    print("\n" + "=" * 100)
    print(f"TOTAL CHANGES APPLIED: {total_changes}")
    print("=" * 100)
    return 0


if __name__ == "__main__":
    sys.exit(main())
