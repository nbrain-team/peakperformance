#!/usr/bin/env python3
"""Fetch fresh HTML from peakpropertyperformance.com and rewrite paths for
static export folders (../_next only — preserve absolute CMS /api URLs).

Use after Flight payloads become corrupted; then re-run scripts/apply-edits.py
and scripts/edits/roles.py per usual."""

from __future__ import annotations

import re
import urllib.request
from pathlib import Path

BASE = "https://www.peakpropertyperformance.com"

# Repo-relative path -> site path (no trailing slash)
PAGES: list[tuple[str, str]] = [
    ("about/index.html", "/about"),
    ("for-owners/index.html", "/for-owners"),
    ("for-property-managers/index.html", "/for-property-managers"),
    ("for-asset-managers/index.html", "/for-asset-managers"),
    ("for-it-managers/index.html", "/for-it-managers"),
    ("resources/index.html", "/resources"),
    ("be-on-the-show/index.html", "/be-on-the-show"),
    ("5c-framework/index.html", "/5c-framework"),
    ("ppp-review/index.html", "/ppp-review"),
    ("book/index.html", "/book"),
]


def rewrite_for_static_export(html: str) -> str:
    """Production uses root-relative /_next URLs; static export pages live in subdirs.

    Do not rewrite /api/ — production uses absolute CMS URLs like
    https://www.peakpropertyperformance.com/api/... and blind replace would corrupt them.
    """
    html = html.replace("/_next/", "../_next/")
    # Match local edit-script anchors and chunk filenames used offline (no dpl query).
    html = re.sub(r"\?dpl=dpl_[A-Za-z0-9_-]+", "", html)
    return html


def fetch(url: str) -> str:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; ppp-html-sync/1.0)",
            "Accept": "text/html,application/xhtml+xml",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read().decode("utf-8")


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    for rel, path in PAGES:
        url = BASE.rstrip("/") + path
        target = root / rel
        print(f"fetch {url} -> {rel}")
        html = rewrite_for_static_export(fetch(url))
        target.write_text(html)
    print("done")


if __name__ == "__main__":
    main()
