# -*- coding: utf-8 -*-
"""P1-8 — Role page polish across all four /for-* pages.

For each role page:
  • Update <meta name="description"> with v3-aligned, "For [role]:" pattern copy
  • Sharpen <meta property="og:title"> with role-specific positioning
  • Refresh <meta property="og:description">
  • Add <meta property="og:image:width">, <meta property="og:image:height">
  • Add <meta name="twitter:title">, <meta name="twitter:description">
  • Insert a role-specific transitional CTA block (eyebrow, h2, lede, button)
    immediately BEFORE the global "Three ways in." block. Sentinel-comment
    wrapped for idempotent re-application.

Run from repo root:
    python3 scripts/edits/p1-8-role-pages.py
"""

from __future__ import annotations
import os
import re
import sys
from pathlib import Path

ROLES = {
    "for-owners": {
        "h1": "Lead from the skybox. Not the field.",
        "meta_desc": "For CRE owners: own the data and digital infrastructure that determines NOI, control, and AI readiness. The plays from the Amazon Best Seller.",
        "og_title": "For CRE Owners — Lead from the skybox. | Peak Property Performance®",
        "og_desc": "For CRE owners and operators: own the foundation that determines NOI, control, and AI readiness. The plays. The 5C™ Framework. The Amazon Best Seller.",
        "tw_title": "For CRE Owners — Lead from the skybox. | Peak Property Performance®",
        "tw_desc": "Own the foundation that determines NOI, control, and AI readiness. The plays from the Amazon Best Seller.",
        "cta": {
            "eyebrow": "Run the Play",
            "h2": "Run the play on your portfolio.",
            "lede": "Map who owns what, where the data lives, and where the leakage is — across one building, then the portfolio. Owner-controlled. No software pitch. No rip-and-replace.",
            "btn_label": "Run the PPP Review on Your Portfolio →",
        },
    },
    "for-asset-managers": {
        "h1": "The portfolio play. The capital-stack lens.",
        "meta_desc": "For asset managers: lead bold ROI plays, deepen data fluency, and surface insights that drive smarter capital allocations. Built on the 5C™ Framework.",
        "og_title": "For Asset Managers — The portfolio play. | Peak Property Performance®",
        "og_desc": "For asset managers: portfolio-grade insights for capital allocation, refinance, and exit math. Built on the 5C™ Framework from the Amazon Best Seller.",
        "tw_title": "For Asset Managers — The portfolio play. | Peak Property Performance®",
        "tw_desc": "ROI plays, data fluency, and the capital-stack lens for asset managers running CRE portfolios. Built on the 5C™ Framework.",
        "cta": {
            "eyebrow": "Run the Play",
            "h2": "Get the portfolio diagnostic.",
            "lede": "We&#x27;ll map property data flow, the control gaps, and the recoverable NOI you can take to your next investment committee — diligence-grade and owner-controlled.",
            "btn_label": "Get the Portfolio Diagnostic →",
        },
    },
    "for-property-managers": {
        "h1": "Less firefighting. More signal.",
        "meta_desc": "For property managers: less reactive firefighting. More proactive insight. Run buildings with a systemic view — and stop translating chaos into spreadsheets.",
        "og_title": "For Property Managers — Less firefighting. More signal. | Peak Property Performance®",
        "og_desc": "For property managers: a systemic view of the building. Owner-controlled connectivity that gives your team signal instead of weekly chaos.",
        "tw_title": "For Property Managers — Less firefighting. More signal. | Peak Property Performance®",
        "tw_desc": "Run buildings with a systemic view. Stop translating chaos into spreadsheets. The plays from the Amazon Best Seller.",
        "cta": {
            "eyebrow": "Run the Play",
            "h2": "Bring the audit to your PMs.",
            "lede": "Trade reactive firefighting for a systemic view. We&#x27;ll show you what owner-controlled connectivity unlocks for your team — and which playbook items convert chaos into signal.",
            "btn_label": "Bring the Audit to Your PMs →",
        },
    },
    "for-it-managers": {
        "h1": "Run the rules. Vendors plug in under them.",
        "meta_desc": "For IT managers: one owner-controlled standard. Real governance. Vendors plug in under your rules. The play that ends shadow networks.",
        "og_title": "For IT Managers — Run the rules. | Peak Property Performance®",
        "og_desc": "For IT managers: one owner-controlled standard. Real governance. Vendors plug in under your rules. The play that ends shadow networks across CRE portfolios.",
        "tw_title": "For IT Managers — Run the rules. | Peak Property Performance®",
        "tw_desc": "One owner-controlled standard. Real governance. Vendors plug in under your rules. The play from the Amazon Best Seller.",
        "cta": {
            "eyebrow": "Run the Play",
            "h2": "Lock in the owner-controlled standard.",
            "lede": "One backplane. Real governance. Vendors plug in under your rules. We&#x27;ll map your existing stack against the 5C™ Framework and identify the shadow networks to retire first.",
            "btn_label": "Lock in the Owner-Controlled Standard →",
        },
    },
}

# Sentinel comments make the CTA block idempotent — re-running replaces, never duplicates.
CTA_START = "<!-- p1-8:role-cta:start -->"
CTA_END = "<!-- p1-8:role-cta:end -->"
CTA_BLOCK_RE = re.compile(
    re.escape(CTA_START) + r"[\s\S]*?" + re.escape(CTA_END)
)


def build_cta_block(role_key: str, cta: dict) -> str:
    return (
        f'{CTA_START}'
        f'<section class="resources-closing-cta" id="run-the-play">'
        f'<div class="container">'
        f'<span class="eyebrow no-rule" style="justify-content:center;display:flex">{cta["eyebrow"]}</span>'
        f'<h2 class="resources-closing-cta__heading">{cta["h2"]}</h2>'
        f'<p class="resources-closing-cta__lede">{cta["lede"]}</p>'
        f'<div style="margin-top:1.75rem;text-align:center">'
        f'<a class="btn btn-primary btn-lg" href="../ppp-review/index.html">{cta["btn_label"]}</a>'
        f'</div>'
        f'</div>'
        f'</section>'
        f'{CTA_END}'
    )


def patch_meta(html: str, spec: dict) -> tuple[str, list[str]]:
    """Update meta description, og:title/description, og:image:width/height, twitter:title/description."""
    actions: list[str] = []
    new = html

    # 1. <meta name="description">
    new, n = re.subn(
        r'<meta name="description" content="[^"]*"\s*/>',
        f'<meta name="description" content="{spec["meta_desc"]}"/>',
        new,
        count=1,
    )
    if n:
        actions.append("meta-desc")

    # 2. <meta property="og:title">
    new, n = re.subn(
        r'<meta property="og:title" content="[^"]*"\s*/>',
        f'<meta property="og:title" content="{spec["og_title"]}"/>',
        new,
        count=1,
    )
    if n:
        actions.append("og:title")

    # 3. <meta property="og:description">
    new, n = re.subn(
        r'<meta property="og:description" content="[^"]*"\s*/>',
        f'<meta property="og:description" content="{spec["og_desc"]}"/>',
        new,
        count=1,
    )
    if n:
        actions.append("og:desc")

    # 4. og:image:width / og:image:height — insert immediately after og:image if missing
    if '<meta property="og:image:width"' not in new:
        new, n = re.subn(
            r'(<meta property="og:image" content="[^"]*"\s*/>)',
            r'\1<meta property="og:image:width" content="1200"/><meta property="og:image:height" content="630"/>',
            new,
            count=1,
        )
        if n:
            actions.append("og:image:wh")

    # 5. twitter:title / twitter:description — insert before twitter:image if missing
    if 'name="twitter:title"' not in new:
        new, n = re.subn(
            r'(<meta name="twitter:image" content="[^"]*"\s*/>)',
            f'<meta name="twitter:title" content="{spec["tw_title"]}"/><meta name="twitter:description" content="{spec["tw_desc"]}"/>\\1',
            new,
            count=1,
        )
        if n:
            actions.append("tw:title+desc")

    return new, actions


def patch_cta(html: str, role_key: str, cta: dict) -> tuple[str, list[str]]:
    """Insert (or replace) the role-specific transitional CTA block above the global Three-ways block."""
    actions: list[str] = []
    block = build_cta_block(role_key, cta)
    new = html

    # If a sentinel-wrapped block already exists, replace it for idempotency.
    if CTA_START in new and CTA_END in new:
        new = CTA_BLOCK_RE.sub(block, new, count=1)
        actions.append("cta-replace")
        return new, actions

    # Otherwise insert it immediately before the global Three-ways CTA.
    three_ways = '<section class="cta-section cta-section--dark three-ways-blocks">'
    if three_ways in new:
        new = new.replace(three_ways, block + three_ways, 1)
        actions.append("cta-insert")
    else:
        actions.append("cta-NO-ANCHOR")
    return new, actions


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    os.chdir(repo_root)

    results = {}
    for role_key, spec in ROLES.items():
        path = f"{role_key}/index.html"
        with open(path, encoding="utf-8") as fh:
            src = fh.read()
        new = src
        new, m_actions = patch_meta(new, spec)
        new, c_actions = patch_cta(new, role_key, spec)
        actions = m_actions + c_actions
        if new != src:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(new)
            results[role_key] = ("UPDATED", actions)
        else:
            results[role_key] = ("UNCHANGED", actions)

    print("=== P1-8 role-page patch results ===")
    for role_key, (status, actions) in results.items():
        print(f"  /{role_key:24s}  {status:10s}  [{', '.join(actions) if actions else 'no-op'}]")

    return 0


if __name__ == "__main__":
    sys.exit(main())
