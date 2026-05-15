# -*- coding: utf-8 -*-
"""P2-2 — Read-only SEO/AEO foundation audit.

Reports:
  1. Schema.org JSON-LD coverage per page (Organization, BreadcrumbList, page-specific)
  2. /book/index.html — Book schema with "award" field
  3. /about/index.html — Person schema for Bill, Drew, Ryan
  4. sitemap.xml + robots.txt status
  5. Favicon set + site.webmanifest theme_color check
"""

from __future__ import annotations
import os
import re
import json
from collections import defaultdict
from pathlib import Path

SKIP_DIRS = {".git", "_next", ".venv", "node_modules", "public", "_external", "scripts", "docs", "transcripts", "api"}

SCHEMA_TYPES_TO_TRACK = [
    "Organization",
    "BreadcrumbList",
    "WebSite",
    "Book",
    "PodcastSeries",
    "PodcastEpisode",
    "FAQPage",
    "Person",
    "DefinedTermSet",
    "WebApplication",
]


def collect_html_files(root: Path) -> list[Path]:
    paths = []
    for r, dirs, names in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
        for n in names:
            if n.endswith(".html"):
                paths.append(Path(r) / n)
    return sorted(paths)


def types_in_html(html: str) -> tuple[set[str], list[str]]:
    """Return (set of @type values found in JSON-LD, list of parse errors)."""
    types = set()
    errors = []
    for m in re.finditer(r'<script type="application/ld\+json">([\s\S]*?)</script>', html):
        body = m.group(1).strip()
        try:
            data = json.loads(body)
        except json.JSONDecodeError as e:
            errors.append(f"  parse error: {e}")
            # Fall back to regex extraction
            for tm in re.finditer(r'"@type":\s*"([^"]+)"', body):
                types.add(tm.group(1))
            continue
        # Walk the structure — @type can appear nested
        def walk(node):
            if isinstance(node, dict):
                t = node.get("@type")
                if isinstance(t, str):
                    types.add(t)
                elif isinstance(t, list):
                    types.update(t)
                for v in node.values():
                    walk(v)
            elif isinstance(node, list):
                for v in node:
                    walk(v)
        walk(data)
    return types, errors


def main():
    repo_root = Path(__file__).resolve().parents[2]
    os.chdir(repo_root)

    files = collect_html_files(Path("."))
    print(f"Scanning {len(files)} HTML files...\n")

    # ============ 1. Schema coverage matrix ============
    print("=" * 100)
    print("1. SCHEMA.ORG JSON-LD COVERAGE PER PAGE")
    print("=" * 100)

    coverage = {}
    for fp in files:
        s = fp.read_text(encoding="utf-8")
        types, errors = types_in_html(s)
        coverage[str(fp)] = {"types": types, "errors": errors}

    # Aggregate counts per schema type
    agg = defaultdict(int)
    for fp, info in coverage.items():
        for t in info["types"]:
            agg[t] += 1

    print(f"\n  Schema types found across all {len(files)} files:")
    for t, c in sorted(agg.items(), key=lambda x: -x[1]):
        print(f"     {t:20s}  on {c:>3d} page(s)")

    # ============ 2. Per-page coverage ============
    print(f"\n  Per-page (showing only key marketing pages + missing schemas):")
    KEY_PAGES = [
        "index.html",
        "book/index.html",
        "podcast/index.html",
        "5c-framework/index.html",
        "about/index.html",
        "ppp-review/index.html",
        "resources/index.html",
        "faq/index.html",
        "glossary/index.html",
        "vendor-contract-audit/index.html",
        "be-on-the-show/index.html",
        "for-owners/index.html",
        "for-asset-managers/index.html",
        "for-property-managers/index.html",
        "for-it-managers/index.html",
    ]
    for fp_str in KEY_PAGES:
        info = coverage.get(fp_str, None)
        if not info:
            print(f"     ❌ {fp_str:50s}  FILE NOT FOUND")
            continue
        types_str = ", ".join(sorted(info["types"])) or "(none)"
        print(f"     {fp_str:50s}  {types_str}")
        if info["errors"]:
            for e in info["errors"]:
                print(f"        {e}")

    # ============ 3. Pages MISSING Organization or BreadcrumbList ============
    print("\n  Coverage gap analysis (every page should have Organization; every non-home page should have BreadcrumbList):")
    missing_org = []
    missing_breadcrumb = []
    for fp_str, info in coverage.items():
        if "Organization" not in info["types"]:
            missing_org.append(fp_str)
        if fp_str != "index.html" and "BreadcrumbList" not in info["types"]:
            missing_breadcrumb.append(fp_str)
    print(f"     Pages missing Organization schema: {len(missing_org)}/{len(files)}")
    for f in missing_org[:20]:
        print(f"        ❌ {f}")
    if len(missing_org) > 20:
        print(f"        ...and {len(missing_org) - 20} more")
    print(f"\n     Non-home pages missing BreadcrumbList schema: {len(missing_breadcrumb)}/{len(files) - 1}")
    for f in missing_breadcrumb[:20]:
        print(f"        ❌ {f}")
    if len(missing_breadcrumb) > 20:
        print(f"        ...and {len(missing_breadcrumb) - 20} more")

    # ============ 4. Book schema on /book ============
    print("\n" + "=" * 100)
    print("2. /book/index.html — Book schema with 'award' field")
    print("=" * 100)
    book_html = (Path("book/index.html")).read_text(encoding="utf-8")
    book_jsonld = None
    for m in re.finditer(r'<script type="application/ld\+json">([\s\S]*?)</script>', book_html):
        try:
            d = json.loads(m.group(1))
            def find_book(node):
                if isinstance(node, dict):
                    if node.get("@type") == "Book":
                        return node
                    for v in node.values():
                        r = find_book(v)
                        if r:
                            return r
                elif isinstance(node, list):
                    for v in node:
                        r = find_book(v)
                        if r:
                            return r
                return None
            b = find_book(d)
            if b:
                book_jsonld = b
                break
        except json.JSONDecodeError:
            continue
    if book_jsonld:
        print("   Book schema found. Fields present:")
        for k in sorted(book_jsonld.keys()):
            v = book_jsonld[k]
            v_str = json.dumps(v) if not isinstance(v, str) else v
            print(f"      {k}: {v_str[:120]}")
        print(f"\n   ✅ has 'award' field: {'award' in book_jsonld}")
        if "award" in book_jsonld:
            print(f"   award value: {book_jsonld['award']}")
    else:
        print("   ❌ NO Book schema found on /book/index.html")

    # ============ 5. Person schema on /about ============
    print("\n" + "=" * 100)
    print("3. /about/index.html — Person schema for authors")
    print("=" * 100)
    about_html = (Path("about/index.html")).read_text(encoding="utf-8")
    persons = []
    for m in re.finditer(r'<script type="application/ld\+json">([\s\S]*?)</script>', about_html):
        try:
            d = json.loads(m.group(1))
            def find_persons(node, acc):
                if isinstance(node, dict):
                    if node.get("@type") == "Person":
                        acc.append(node)
                    for v in node.values():
                        find_persons(v, acc)
                elif isinstance(node, list):
                    for v in node:
                        find_persons(v, acc)
            find_persons(d, persons)
        except json.JSONDecodeError:
            continue
    print(f"   Person schemas found: {len(persons)}")
    for p in persons:
        print(f"      • {p.get('name', '(no name)')}  fields: {sorted(p.keys())}")
    expected = {"Bill Douglas", "Drew Hall", "Ryan R. Goble"}
    found_names = {p.get("name") for p in persons}
    missing = expected - found_names
    if missing:
        print(f"   ❌ Missing Person schema for: {missing}")
    else:
        print(f"   ✅ All 3 expected authors have Person schema")

    # ============ 6. sitemap.xml + robots.txt ============
    print("\n" + "=" * 100)
    print("4. sitemap.xml + robots.txt")
    print("=" * 100)
    sm = Path("sitemap.xml")
    if sm.exists():
        sm_text = sm.read_text(encoding="utf-8")
        url_count = sm_text.count("<loc>")
        print(f"   ✅ sitemap.xml exists  ({url_count} URLs)")
        # Check expected URLs
        expected_paths = [
            "/", "/book", "/podcast", "/5c-framework", "/about",
            "/resources", "/faq", "/ppp-review", "/glossary",
            "/vendor-contract-audit", "/be-on-the-show",
            "/for-owners", "/for-asset-managers", "/for-property-managers", "/for-it-managers",
        ]
        for p in expected_paths:
            url = f"https://peakpropertyperformance.com{p}" if p != "/" else "https://peakpropertyperformance.com/"
            present = f"<loc>{url}</loc>" in sm_text
            symbol = "✅" if present else "❌"
            print(f"      {symbol} {p}")
        # Episode pages count
        episode_count = len([f for f in files if "podcast/" in str(f) and "podcast/index" not in str(f)])
        ep_in_sitemap = sm_text.count("/podcast/") - (1 if "/podcast<" in sm_text else 0) - (1 if "/podcast/</loc>" in sm_text else 0)
        print(f"      Episode page URLs in sitemap: ~{ep_in_sitemap} (filesystem has {episode_count})")
    else:
        print("   ❌ sitemap.xml missing")

    rt = Path("robots.txt")
    if rt.exists():
        rt_text = rt.read_text(encoding="utf-8")
        print(f"\n   ✅ robots.txt exists  ({len(rt_text)} chars)")
        print(f"      Contains 'Sitemap:' line: {'Sitemap:' in rt_text}")
        print(f"      Contains 'User-agent:' line: {'User-agent:' in rt_text}")
        print(f"\n   robots.txt contents:")
        for line in rt_text.splitlines():
            print(f"      | {line}")
    else:
        print("\n   ❌ robots.txt MISSING")

    # ============ 7. Favicon set ============
    print("\n" + "=" * 100)
    print("5. Favicon set + site.webmanifest")
    print("=" * 100)
    expected_favicons = [
        "public/favicon.ico",
        "public/favicon-16x16.png",
        "public/favicon-32x32.png",
        "public/apple-touch-icon.png",
        "public/android-chrome-192x192.png",
        "public/android-chrome-512x512.png",
        "public/site.webmanifest",
    ]
    for ico in expected_favicons:
        p = Path(ico)
        if p.exists():
            print(f"   ✅ {ico:50s}  ({p.stat().st_size:,} bytes)")
        else:
            print(f"   ❌ {ico:50s}  MISSING")
    # Check webmanifest theme_color
    wm = Path("public/site.webmanifest")
    if wm.exists():
        try:
            data = json.loads(wm.read_text(encoding="utf-8"))
            theme = data.get("theme_color")
            print(f"\n   site.webmanifest theme_color: {theme!r}  (expected '#1B3526')")
            print(f"   {'✅' if theme == '#1B3526' else '❌'} matches expected")
        except json.JSONDecodeError as e:
            print(f"   ❌ site.webmanifest parse error: {e}")


if __name__ == "__main__":
    main()
