#!/usr/bin/env python3
"""Fetch fresh HTML from peakpropertyperformance.com and rewrite paths for
static export folders (../_next, ../api).

Use after Flight payloads become corrupted; then re-run scripts/apply-edits.py
and scripts/edits/roles.py per usual."""

from __future__ import annotations

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
    """Production serves /_next and /api from root; export pages live in subdirs."""
    return html.replace("/_next/", "../_next/").replace("/api/", "../api/")


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
