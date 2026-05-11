# -*- coding: utf-8 -*-
"""Edits for role pages — items 31, 32, 35, A6, head additions.

Driven by a loop in __main__, since the four pages share structure.
"""

# This file is special — apply-edits.py expects FILE + EDITS. To handle
# all four role pages, we use a small driver pattern: when invoked as a
# script, this module enumerates each role and writes its updated file
# directly using the same escape-and-replace primitives.

import sys
from pathlib import Path

# Load apply-edits helper
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from apply_edits import to_js_string_literal_escape  # type: ignore

ROLE_PAGES = [
    {
        "file": "for-owners/index.html",
        "h1_visible_from": "<h1 class=\"hero__heading mt-4\">Lead from the skybox. Not the field.</h1>",
        "h1_visible_to": "<h1 class=\"hero__heading mt-4\">Lead from the skybox. Not the field.</h1>",  # no change
        "h1_payload_from": '"hero__heading mt-4","children":"Lead from the skybox. Not the field."',
        "h1_payload_to": '"hero__heading mt-4","children":"Lead from the skybox. Not the field."',
        "cta_to": "Run the PPP Review on Your Portfolio →",
        "og_title": "For CRE Owners — Peak Property Performance®",
        "og_description": "Lead the long game from the skybox. The PPP playbook for CRE owners who want NOI growth and AI readiness without vendor lock-in.",
        "og_url": "https://peakpropertyperformance.com/for-owners",
    },
    {
        "file": "for-asset-managers/index.html",
        "h1_visible_from": "<h1 class=\"hero__heading mt-4\">Move from reporting to leading.</h1>",
        "h1_visible_to": "<h1 class=\"hero__heading mt-4\">The portfolio play. The capital-stack lens.</h1>",
        "h1_payload_from": '"hero__heading mt-4","children":"Move from reporting to leading."',
        "h1_payload_to": '"hero__heading mt-4","children":"The portfolio play. The capital-stack lens."',
        "cta_to": "Get the Portfolio Diagnostic →",
        "og_title": "For Asset Managers — Peak Property Performance®",
        "og_description": "The portfolio play. The capital-stack lens. ROI plays and data fluency for asset managers running CRE portfolios.",
        "og_url": "https://peakpropertyperformance.com/for-asset-managers",
    },
    {
        "file": "for-property-managers/index.html",
        "h1_visible_from": "<h1 class=\"hero__heading mt-4\">Less firefighting. More foresight.</h1>",
        "h1_visible_to": "<h1 class=\"hero__heading mt-4\">Less firefighting. More signal.</h1>",
        "h1_payload_from": '"hero__heading mt-4","children":"Less firefighting. More foresight."',
        "h1_payload_to": '"hero__heading mt-4","children":"Less firefighting. More signal."',
        "cta_to": "Bring the Audit to Your PMs →",
        "og_title": "For Property Managers — Peak Property Performance®",
        "og_description": "Less firefighting. More signal. Run buildings with a systemic view and stop translating chaos into spreadsheets.",
        "og_url": "https://peakpropertyperformance.com/for-property-managers",
    },
    {
        "file": "for-it-managers/index.html",
        "h1_visible_from": "<h1 class=\"hero__heading mt-4\">One standard. Real governance. No more shadow networks.</h1>",
        "h1_visible_to": "<h1 class=\"hero__heading mt-4\">Run the rules. Vendors plug in under them.</h1>",
        "h1_payload_from": '"hero__heading mt-4","children":"One standard. Real governance. No more shadow networks."',
        "h1_payload_to": '"hero__heading mt-4","children":"Run the rules. Vendors plug in under them."',
        "cta_to": "Lock in the Owner-Controlled Standard →",
        "og_title": "For IT Managers — Peak Property Performance®",
        "og_description": "Run the rules. Vendors plug in under them. The PPP play that ends shadow networks and locks in owner-controlled governance.",
        "og_url": "https://peakpropertyperformance.com/for-it-managers",
    },
]


def apply_role(role):
    repo_root = Path(__file__).resolve().parent.parent.parent
    target = repo_root / role["file"]
    src = target.read_text()
    new = src

    # ---- 31. H1 (skip if visible_from == visible_to) ----
    if role["h1_visible_from"] != role["h1_visible_to"]:
        cnt = new.count(role["h1_visible_from"])
        if cnt != 1:
            raise RuntimeError(f"{role['file']}: H1 visible expected 1, got {cnt}")
        new = new.replace(role["h1_visible_from"], role["h1_visible_to"])
        # payload
        payload_from = to_js_string_literal_escape(role["h1_payload_from"])
        payload_to = to_js_string_literal_escape(role["h1_payload_to"])
        cnt = new.count(payload_from)
        if cnt != 1:
            raise RuntimeError(f"{role['file']}: H1 payload expected 1, got {cnt}")
        new = new.replace(payload_from, payload_to)

    # ---- 32. Differentiated CTA ----
    cta_from_v = '<a class="btn btn-primary btn-lg" href="../ppp-review/index.html">Request a PPP Review</a>'
    cta_to_v = f'<a class="btn btn-primary btn-lg" href="../ppp-review/index.html">{role["cta_to"]}</a>'
    cnt = new.count(cta_from_v)
    if cnt >= 1:
        new = new.replace(cta_from_v, cta_to_v)
    cta_from_p_raw = '"className":"btn btn-primary btn-lg","children":"Request a PPP Review"'
    cta_to_p_raw = f'"className":"btn btn-primary btn-lg","children":"{role["cta_to"]}"'
    cta_from_p = to_js_string_literal_escape(cta_from_p_raw)
    cta_to_p = to_js_string_literal_escape(cta_to_p_raw)
    cnt = new.count(cta_from_p)
    if cnt >= 1:
        new = new.replace(cta_from_p, cta_to_p)

    # ---- 35. Role grid generic CTAs (only on the home page; role pages may have them too) ----
    rc_from_v = '<span class="role-card__cta">Read More<!-- --> →</span>'
    rc_to_v = '<span class="role-card__cta">See Your Role<!-- --> →</span>'
    if rc_from_v in new:
        new = new.replace(rc_from_v, rc_to_v)
    rc_from_p_raw = '"className":"role-card__cta","children":["Read More"," →"]'
    rc_to_p_raw = '"className":"role-card__cta","children":["See Your Role"," →"]'
    rc_from_p = to_js_string_literal_escape(rc_from_p_raw)
    rc_to_p = to_js_string_literal_escape(rc_to_p_raw)
    if rc_from_p in new:
        new = new.replace(rc_from_p, rc_to_p)

    # ---- A6. Footer tagline ----
    ft_from_v = '<p class="footer__tagline">A best-selling book and podcast for commercial real estate leaders.</p>'
    ft_to_v = '<p class="footer__tagline">Amazon Best Seller. The CRE strategy playbook for owners, operators, and the leaders building the future of the industry.</p>'
    if ft_from_v in new:
        new = new.replace(ft_from_v, ft_to_v)
    ft_from_p_raw = '"className":"footer__tagline","children":"A best-selling book and podcast for commercial real estate leaders."'
    ft_to_p_raw = '"className":"footer__tagline","children":"Amazon Best Seller. The CRE strategy playbook for owners, operators, and the leaders building the future of the industry."'
    ft_from_p = to_js_string_literal_escape(ft_from_p_raw)
    ft_to_p = to_js_string_literal_escape(ft_to_p_raw)
    if ft_from_p in new:
        new = new.replace(ft_from_p, ft_to_p)

    # ---- head additions ----
    head_anchor = '<link rel="stylesheet" href="../_next/static/css/f3145fbd800cc712.css" data-precedence="next"/>'
    head_insert = (
        head_anchor
        + '<link rel="stylesheet" href="../public/css/ppp-additions.css"/>'
        + '<link rel="icon" type="image/x-icon" href="../public/favicon.ico"/>'
        + '<link rel="icon" type="image/png" sizes="32x32" href="../public/favicon-32x32.png"/>'
        + '<link rel="icon" type="image/png" sizes="16x16" href="../public/favicon-16x16.png"/>'
        + '<link rel="apple-touch-icon" sizes="180x180" href="../public/apple-touch-icon.png"/>'
        + '<link rel="manifest" href="../public/site.webmanifest"/>'
        + '<meta name="theme-color" content="#1B3526"/>'
        + f'<meta property="og:title" content="{role["og_title"]}"/>'
        + f'<meta property="og:description" content="{role["og_description"]}"/>'
        + '<meta property="og:type" content="website"/>'
        + f'<meta property="og:url" content="{role["og_url"]}"/>'
        + '<meta property="og:image" content="https://peakpropertyperformance.com/public/images/og-image.png"/>'
        + '<meta name="twitter:card" content="summary_large_image"/>'
        + '<meta name="twitter:image" content="https://peakpropertyperformance.com/public/images/og-image.png"/>'
    )
    cnt = new.count(head_anchor)
    if cnt != 1:
        raise RuntimeError(f"{role['file']}: head anchor expected 1, got {cnt}")
    new = new.replace(head_anchor, head_insert)

    if new == src:
        print(f"  NO CHANGES: {role['file']}")
        return
    target.write_text(new)
    print(f"  OK: {role['file']}")


if __name__ == "__main__":
    for r in ROLE_PAGES:
        apply_role(r)
