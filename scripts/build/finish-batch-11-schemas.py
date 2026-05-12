#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Finish Batch 11 from PPP_Sandbox_Content_Review_v3.md item #36:

  - Organization JSON-LD on every page that doesn't already have one
    (spec: 'Organization schema — emit on every page in a shared template')
  - Person JSON-LD × 3 on /about (Bill Douglas, Drew Hall, Ryan R. Goble)
  - BreadcrumbList JSON-LD on every non-home page (2-level for marketing,
    3-level for podcast episodes)

Each insertion lands in the visible <head> as <script type="application/ld+json">
immediately before </head>. Idempotent: re-running detects existing
sentinels (by @id or @type+name) and skips.

Episode breadcrumb names are extracted from the page's existing
PodcastEpisode JSON-LD 'name' field. No manual list needed — this is
robust to new episodes being added later.

Run from repo root:  python3 scripts/build/finish-batch-11-schemas.py
"""

import json
import re
from pathlib import Path

BASE = "https://peakpropertyperformance.com"

# -----------------------------------------------------------------------
# Schema source-of-truth data
# -----------------------------------------------------------------------

ORGANIZATION = {
    "@context": "https://schema.org",
    "@type": "Organization",
    "@id": f"{BASE}/#organization",
    "name": "Peak Property Performance®",
    "alternateName": "PPP",
    "url": BASE,
    "logo": f"{BASE}/api/media/file/ppp-logo.webp",
    "parentOrganization": {
        "@type": "Organization",
        "name": "OpticWise",
        "url": "https://opticwise.com",
    },
}

# Three Person entries for /about. Facts pulled from the existing /about
# bios + book/podcast cross-references on the live site. No invented data.
ABOUT_PERSONS = {
    "@context": "https://schema.org",
    "@graph": [
        {
            "@type": "Person",
            "@id": f"{BASE}/about#bill-douglas",
            "name": "Bill Douglas",
            "jobTitle": "CEO, OpticWise",
            "worksFor": {
                "@type": "Organization",
                "name": "OpticWise",
                "url": "https://opticwise.com",
            },
            "url": f"{BASE}/about",
            "image": f"{BASE}/api/media/file/bill-douglas.webp",
            "description": "Co-author of the Amazon Best Seller Peak Property Performance® and CEO of OpticWise. Helps organizations turn data and digital infrastructure into owner-controlled assets that drive NOI, control, and AI readiness.",
            "knowsAbout": [
                "Commercial real estate",
                "Data and digital infrastructure",
                "AI readiness for buildings",
                "NOI growth",
                "Vendor lock-in",
                "Owner-controlled infrastructure",
            ],
        },
        {
            "@type": "Person",
            "@id": f"{BASE}/about#drew-hall",
            "name": "Drew Hall",
            "jobTitle": "Founder & Chief Architect, OpticWise",
            "worksFor": {
                "@type": "Organization",
                "name": "OpticWise",
                "url": "https://opticwise.com",
            },
            "url": f"{BASE}/about",
            "image": f"{BASE}/api/media/file/drew-hall.webp",
            "description": "Co-author of Peak Property Performance® and co-host of the podcast. Spent his career in the field-level realities of data and digital infrastructure across CRE portfolios.",
            "knowsAbout": [
                "Network architecture",
                "Data and digital infrastructure",
                "Managed services for CRE",
                "Owner-controlled IT",
                "Site-level operations",
            ],
        },
        {
            "@type": "Person",
            "@id": f"{BASE}/about#ryan-r-goble",
            "name": "Ryan R. Goble",
            "jobTitle": "Contributing Author, Peak Property Performance®",
            "url": f"{BASE}/about",
            "image": f"{BASE}/api/media/file/ryan-goble.webp",
            "description": "Contributing author of Peak Property Performance®. Brought decades of CRE operations and editorial craft to the playbook.",
            "knowsAbout": [
                "CRE operations",
                "Playbook narrative",
                "Data and digital infrastructure",
            ],
        },
    ],
}


# Marketing pages: (relative file path, page URL path, breadcrumb name)
MARKETING_PAGES = [
    ("book/index.html",                    "/book",                  "The Book"),
    ("about/index.html",                   "/about",                 "About"),
    ("5c-framework/index.html",            "/5c-framework",          "The 5C\u2122 Framework"),
    ("podcast/index.html",                 "/podcast",               "Podcast"),
    ("resources/index.html",               "/resources",             "Resources"),
    ("ppp-review/index.html",              "/ppp-review",            "Request a PPP Review"),
    ("for-owners/index.html",              "/for-owners",            "For Owners & Operators"),
    ("for-asset-managers/index.html",      "/for-asset-managers",    "For Asset Managers"),
    ("for-property-managers/index.html",   "/for-property-managers", "For Property Managers"),
    ("for-it-managers/index.html",         "/for-it-managers",       "For IT Managers"),
    ("glossary/index.html",                "/glossary",              "PPP Glossary"),
    ("vendor-contract-audit/index.html",   "/vendor-contract-audit", "Vendor Contract Audit"),
    ("be-on-the-show/index.html",          "/be-on-the-show",        "Be on the Show"),
]


def breadcrumb_two_level(name: str, url: str) -> dict:
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "@id": f"{BASE}{url}#breadcrumbs",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home",  "item": f"{BASE}/"},
            {"@type": "ListItem", "position": 2, "name": name,    "item": f"{BASE}{url}"},
        ],
    }


def breadcrumb_three_level(ep_name: str, ep_url_path: str) -> dict:
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "@id": f"{BASE}{ep_url_path}#breadcrumbs",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home",    "item": f"{BASE}/"},
            {"@type": "ListItem", "position": 2, "name": "Podcast", "item": f"{BASE}/podcast"},
            {"@type": "ListItem", "position": 3, "name": ep_name,   "item": f"{BASE}{ep_url_path}"},
        ],
    }


# -----------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------

def render_ld(obj: dict) -> str:
    """Render a JSON-LD object as a <script> block. ensure_ascii=False so
    typographic ™/®/curly quotes don't become \\uXXXX escapes."""
    return (
        '<script type="application/ld+json">'
        + json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
        + "</script>"
    )


def insert_before_head_close(content: str, *blocks: str) -> str:
    """Insert one or more <script> blocks immediately before </head>."""
    idx = content.find("</head>")
    if idx == -1:
        raise RuntimeError("no </head> in file")
    return content[:idx] + "".join(blocks) + content[idx:]


def has_schema_id(content: str, schema_id: str) -> bool:
    """Detect existing schema by its unique @id."""
    return f'"@id":"{schema_id}"' in content or f'"@id": "{schema_id}"' in content


def extract_episode_name(content: str):
    """Pull the episode title from the page's PodcastEpisode JSON-LD.
    Returns None if no episode JSON-LD or no 'name' field present."""
    m = re.search(
        r'"@type"\s*:\s*"PodcastEpisode".*?"name"\s*:\s*"([^"]+)"',
        content, re.DOTALL
    )
    return m.group(1) if m else None


# -----------------------------------------------------------------------
# Patching
# -----------------------------------------------------------------------

def patch_marketing_page(fp: str, url: str, breadcrumb_name: str) -> dict:
    """Inject Organization (if missing) + BreadcrumbList (if missing) into
    a marketing page's <head>. /about gets the additional Person × 3 graph."""
    path = Path(fp)
    if not path.exists():
        return {"file": fp, "status": "missing"}

    content = path.read_text(encoding="utf-8")
    blocks_to_add = []
    added = []

    if not has_schema_id(content, ORGANIZATION["@id"]):
        blocks_to_add.append(render_ld(ORGANIZATION))
        added.append("Organization")

    bc = breadcrumb_two_level(breadcrumb_name, url)
    if not has_schema_id(content, bc["@id"]):
        blocks_to_add.append(render_ld(bc))
        added.append("BreadcrumbList")

    # Special case: /about gets the three Person entries as well
    if fp == "about/index.html":
        bill_id = f"{BASE}/about#bill-douglas"
        if not has_schema_id(content, bill_id):
            blocks_to_add.append(render_ld(ABOUT_PERSONS))
            added.append("Person×3")

    if blocks_to_add:
        content = insert_before_head_close(content, *blocks_to_add)
        path.write_text(content, encoding="utf-8")
        return {"file": fp, "status": "patched", "added": added}
    return {"file": fp, "status": "skipped", "added": []}


def patch_episode_page(ep_dir: Path) -> dict:
    """Inject Organization + 3-level BreadcrumbList into a podcast episode."""
    fp = ep_dir / "index.html"
    rel = str(fp.relative_to(Path.cwd())) if fp.is_absolute() else str(fp)

    if not fp.exists():
        return {"file": rel, "status": "missing"}

    content = fp.read_text(encoding="utf-8")
    ep_name = extract_episode_name(content)
    if not ep_name:
        return {"file": rel, "status": "no-episode-name"}

    ep_url = f"/podcast/{ep_dir.name}"
    blocks_to_add = []
    added = []

    if not has_schema_id(content, ORGANIZATION["@id"]):
        blocks_to_add.append(render_ld(ORGANIZATION))
        added.append("Organization")

    bc = breadcrumb_three_level(ep_name, ep_url)
    if not has_schema_id(content, bc["@id"]):
        blocks_to_add.append(render_ld(bc))
        added.append("BreadcrumbList")

    if blocks_to_add:
        content = insert_before_head_close(content, *blocks_to_add)
        fp.write_text(content, encoding="utf-8")
        return {"file": rel, "status": "patched", "added": added}
    return {"file": fp.name, "status": "skipped", "added": []}


# -----------------------------------------------------------------------
# Entry point
# -----------------------------------------------------------------------

def main():
    results = []

    # Marketing pages
    for fp, url, name in MARKETING_PAGES:
        results.append(patch_marketing_page(fp, url, name))

    # Episode pages
    podcast_root = Path("podcast")
    if podcast_root.exists():
        episodes = sorted([p for p in podcast_root.iterdir() if p.is_dir()])
        for ep in episodes:
            results.append(patch_episode_page(ep))

    # Summary report
    print("\nBATCH 11 SCHEMA INJECTION REPORT")
    print("=" * 90)
    marker = {"patched": "→", "skipped": "✓", "missing": "?", "no-episode-name": "!"}
    total_patched = 0
    total_added = {"Organization": 0, "BreadcrumbList": 0, "Person×3": 0}
    for r in results:
        m = marker.get(r["status"], "?")
        added = ", ".join(r.get("added", [])) or "—"
        print(f"  {m} {r['file']:<70} {r['status']:<10} {added}")
        if r["status"] == "patched":
            total_patched += 1
            for a in r.get("added", []):
                total_added[a] = total_added.get(a, 0) + 1

    print("=" * 90)
    print(f"  Files patched: {total_patched}")
    print(f"  Organization injections:    {total_added['Organization']}")
    print(f"  BreadcrumbList injections:  {total_added['BreadcrumbList']}")
    print(f"  Person×3 injections:        {total_added['Person×3']}  (target: 1, on /about)")


if __name__ == "__main__":
    main()
