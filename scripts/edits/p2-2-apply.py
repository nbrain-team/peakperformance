# -*- coding: utf-8 -*-
"""P2-2 — SEO/AEO foundation: inject missing schemas + fix sitemap.

For each page in PAGE_SPECS:
  • Insert Organization JSON-LD into <head> (if missing)
  • Insert BreadcrumbList JSON-LD into <head> (if missing)

Special case for /about:
  • Insert 3 Person JSON-LD blocks (Bill, Drew, Ryan)

Sitemap:
  • Add /glossary and /vendor-contract-audit URLs

Idempotent: each insert is wrapped in sentinel HTML comments so re-runs
detect-and-skip cleanly. Run from repo root:
    python3 scripts/edits/p2-2-apply.py
"""

from __future__ import annotations
import json
import os
import re
import sys
from pathlib import Path

# Sentinel comments for idempotency.
SENTINEL_ORG = "p2-2:org-schema"
SENTINEL_BC = "p2-2:breadcrumb-schema"
SENTINEL_PERSONS = "p2-2:person-schemas"

# Pages that need Organization + BreadcrumbList injected. Each entry is the
# breadcrumb-friendly display name + the canonical URL path.
PAGE_SPECS = [
    ("5c-framework/index.html",         "5C™ Framework",            "/5c-framework"),
    ("about/index.html",                "About",                    "/about"),
    ("be-on-the-show/index.html",       "Be on the Show",           "/be-on-the-show"),
    ("book/index.html",                 "The Book",                 "/book"),  # Org already there; only Breadcrumb missing
    ("faq/index.html",                  "FAQ",                      "/faq"),
    ("for-asset-managers/index.html",   "For Asset Managers",       "/for-asset-managers"),
    ("for-it-managers/index.html",      "For IT Managers",          "/for-it-managers"),
    ("for-owners/index.html",           "For Owners",               "/for-owners"),
    ("for-property-managers/index.html","For Property Managers",    "/for-property-managers"),
    ("ppp-review/index.html",           "Request a PPP Review",     "/ppp-review"),
    ("resources/index.html",            "Free Resources",           "/resources"),
]

ORG_OBJ = {
    "@context": "https://schema.org",
    "@type": "Organization",
    "@id": "https://peakpropertyperformance.com/#organization",
    "name": "Peak Property Performance®",
    "alternateName": "PPP",
    "url": "https://peakpropertyperformance.com",
    "logo": "https://peakpropertyperformance.com/api/media/file/ppp-logo.webp",
    "parentOrganization": {
        "@type": "Organization",
        "name": "OpticWise",
        "url": "https://opticwise.com",
    },
}


def breadcrumb_obj(page_name: str, page_path: str) -> dict:
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "@id": f"https://peakpropertyperformance.com{page_path}#breadcrumbs",
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": 1,
                "name": "Home",
                "item": "https://peakpropertyperformance.com/",
            },
            {
                "@type": "ListItem",
                "position": 2,
                "name": page_name,
                "item": f"https://peakpropertyperformance.com{page_path}",
            },
        ],
    }


PERSON_BILL = {
    "@context": "https://schema.org",
    "@type": "Person",
    "@id": "https://peakpropertyperformance.com/about#bill-douglas",
    "name": "Bill Douglas",
    "givenName": "Bill",
    "familyName": "Douglas",
    "jobTitle": "CEO, OpticWise",
    "worksFor": {
        "@type": "Organization",
        "name": "OpticWise",
        "url": "https://opticwise.com",
    },
    "url": "https://peakpropertyperformance.com/about",
    "image": "https://www.peakpropertyperformance.com/api/media/file/bill-douglas.webp",
    "description": "Co-author of the Amazon Best Seller Peak Property Performance® and CEO of OpticWise. For decades, Bill has helped organizations turn data and digital infrastructure into owner-controlled assets that drive NOI, control, and AI readiness.",
    "knowsAbout": [
        "Commercial Real Estate",
        "Data and Digital Infrastructure",
        "5C™ Framework",
        "AI Readiness",
        "Property Technology Strategy",
    ],
    "sameAs": [
        "https://opticwise.com",
        "https://www.linkedin.com/in/billdouglas/",
    ],
    "author": {
        "@type": "Book",
        "name": "Peak Property Performance®",
        "isbn": "978-1-63908-128-8",
    },
}

PERSON_DREW = {
    "@context": "https://schema.org",
    "@type": "Person",
    "@id": "https://peakpropertyperformance.com/about#drew-hall",
    "name": "Drew Hall",
    "givenName": "Drew",
    "familyName": "Hall",
    "jobTitle": "Founder & Chief Architect, OpticWise",
    "worksFor": {
        "@type": "Organization",
        "name": "OpticWise",
        "url": "https://opticwise.com",
    },
    "url": "https://peakpropertyperformance.com/about",
    "image": "https://www.peakpropertyperformance.com/api/media/file/drew-hall.webp",
    "description": "Co-author of the Amazon Best Seller Peak Property Performance® and co-host of the PPP Podcast. Drew brings the practitioner's voice to the playbook — what actually happens when the network goes down at 2 AM and the leasing tour is at 9.",
    "knowsAbout": [
        "Commercial Real Estate",
        "Data and Digital Infrastructure",
        "Network Architecture",
        "5C™ Framework",
    ],
    "author": {
        "@type": "Book",
        "name": "Peak Property Performance®",
        "isbn": "978-1-63908-128-8",
    },
}

PERSON_RYAN = {
    "@context": "https://schema.org",
    "@type": "Person",
    "@id": "https://peakpropertyperformance.com/about#ryan-r-goble",
    "name": "Ryan R. Goble",
    "givenName": "Ryan",
    "familyName": "Goble",
    "jobTitle": "Contributing Author",
    "url": "https://peakpropertyperformance.com/about",
    "image": "https://www.peakpropertyperformance.com/api/media/file/ryan-goble.webp",
    "description": "Contributing author and collaborator on Peak Property Performance®. Ryan sharpens the playbook on the operational and governance side of building intelligence — the parts that don't make the slideware but determine whether a strategy actually works under pressure.",
    "knowsAbout": [
        "Commercial Real Estate",
        "Data Governance",
        "Building Intelligence",
    ],
    "author": {
        "@type": "Book",
        "name": "Peak Property Performance®",
        "isbn": "978-1-63908-128-8",
    },
}


def script_block(sentinel: str, obj: dict | list[dict]) -> str:
    """Render a JSON-LD script tag wrapped in sentinel comments for idempotency."""
    if isinstance(obj, list):
        body = "".join(json.dumps(o, separators=(",", ":"), ensure_ascii=False) for o in obj)
        # Use array-of-objects pattern: emit each as its own <script>
        scripts = "".join(
            f'<script type="application/ld+json">{json.dumps(o, separators=(",", ":"), ensure_ascii=False)}</script>'
            for o in obj
        )
    else:
        scripts = f'<script type="application/ld+json">{json.dumps(obj, separators=(",", ":"), ensure_ascii=False)}</script>'
    return f"<!-- {sentinel}:start -->{scripts}<!-- {sentinel}:end -->"


def insert_before_head_close(html: str, block: str) -> str:
    """Insert block immediately before </head>."""
    return html.replace("</head>", f"{block}</head>", 1)


def patch_one_page(path: str, page_name: str, page_path: str, has_org: bool, has_bc: bool) -> list[str]:
    actions = []
    src = Path(path).read_text(encoding="utf-8")
    new = src

    # 1. Organization schema (skip if already present, in any form)
    if not has_org and SENTINEL_ORG not in new:
        new = insert_before_head_close(new, script_block(SENTINEL_ORG, ORG_OBJ))
        actions.append("+org")

    # 2. BreadcrumbList schema
    if not has_bc and SENTINEL_BC not in new:
        new = insert_before_head_close(new, script_block(SENTINEL_BC, breadcrumb_obj(page_name, page_path)))
        actions.append("+breadcrumb")

    if new != src:
        Path(path).write_text(new, encoding="utf-8")
    return actions


def patch_about_persons() -> list[str]:
    actions = []
    path = "about/index.html"
    src = Path(path).read_text(encoding="utf-8")
    if SENTINEL_PERSONS in src:
        return ["already-has-persons"]
    block = script_block(SENTINEL_PERSONS, [PERSON_BILL, PERSON_DREW, PERSON_RYAN])
    new = insert_before_head_close(src, block)
    Path(path).write_text(new, encoding="utf-8")
    actions.append("+3-persons")
    return actions


def patch_sitemap() -> list[str]:
    """Add /glossary and /vendor-contract-audit if missing."""
    actions = []
    path = "sitemap.xml"
    src = Path(path).read_text(encoding="utf-8")
    new = src

    additions = [
        ("https://peakpropertyperformance.com/glossary", "0.7"),
        ("https://peakpropertyperformance.com/vendor-contract-audit", "0.7"),
    ]
    for url, prio in additions:
        if f"<loc>{url}</loc>" in new:
            actions.append(f"sitemap:already-has:{url.rsplit('/', 1)[-1]}")
            continue
        # Insert before </urlset>
        entry = (
            f"  <url>\n"
            f"    <loc>{url}</loc>\n"
            f"    <lastmod>2026-05-14</lastmod>\n"
            f"    <changefreq>monthly</changefreq>\n"
            f"    <priority>{prio}</priority>\n"
            f"  </url>\n"
        )
        new = new.replace("</urlset>", entry + "</urlset>", 1)
        actions.append(f"+sitemap:{url.rsplit('/', 1)[-1]}")

    if new != src:
        Path(path).write_text(new, encoding="utf-8")
    return actions


def detect_existing_schema(html: str, type_name: str) -> bool:
    """Detect whether the given @type already appears in any JSON-LD block on the page."""
    for m in re.finditer(r'<script type="application/ld\+json">([\s\S]*?)</script>', html):
        try:
            data = json.loads(m.group(1))
        except json.JSONDecodeError:
            # Fall back to substring check for malformed JSON-LD
            if f'"@type":"{type_name}"' in m.group(1):
                return True
            continue
        def walk(node):
            if isinstance(node, dict):
                t = node.get("@type")
                if t == type_name or (isinstance(t, list) and type_name in t):
                    return True
                return any(walk(v) for v in node.values())
            elif isinstance(node, list):
                return any(walk(v) for v in node)
            return False
        if walk(data):
            return True
    return False


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    os.chdir(repo_root)

    print("=" * 100)
    print("P2-2 — SEO/AEO foundation: schema + sitemap fixes")
    print("=" * 100)

    overall_actions = {}

    # ---- 1. Per-page Organization + BreadcrumbList ----
    print("\nPage-level schema injection:")
    for path, page_name, page_path in PAGE_SPECS:
        if not Path(path).exists():
            print(f"  ❌ {path}  (file not found)")
            overall_actions[path] = ["MISSING-FILE"]
            continue
        src = Path(path).read_text(encoding="utf-8")
        has_org = detect_existing_schema(src, "Organization")
        has_bc = detect_existing_schema(src, "BreadcrumbList")
        actions = patch_one_page(path, page_name, page_path, has_org, has_bc)
        overall_actions[path] = actions
        status = ", ".join(actions) if actions else "no-change-needed"
        print(f"  📄 {path:50s}  [{status}]")

    # ---- 2. /about Person schemas ----
    print("\n/about Person schemas:")
    p_actions = patch_about_persons()
    print(f"  📄 about/index.html                                  [{', '.join(p_actions)}]")

    # ---- 3. Sitemap additions ----
    print("\nSitemap additions:")
    sm_actions = patch_sitemap()
    for a in sm_actions:
        print(f"  📄 sitemap.xml                                        [{a}]")

    print("\n" + "=" * 100)
    total_actions = sum(len(v) for v in overall_actions.values()) + len(p_actions) + len(sm_actions)
    print(f"TOTAL ACTIONS APPLIED: {total_actions}")
    print("=" * 100)
    return 0


if __name__ == "__main__":
    sys.exit(main())
