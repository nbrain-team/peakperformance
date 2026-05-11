# -*- coding: utf-8 -*-
"""Edits for /resources/index.html (items 26, 27, A9, A6, head additions).

Note: item 26 (Add 4 downloadable cards) is implemented by inserting a NEW
section before the StarterKit block. That's done as a single HTML insert
in both visible body and Flight payload."""

FILE = "resources/index.html"

EDITS = [
    # ---- A9. Hero lede on /resources ----
    {
        "label": "A9 resources hero lede (visible)",
        "html": (
            '<p class="hero__lede mt-3">Everything we wished existed when we were running our first portfolio. Use them. Adapt them. Run them on your buildings.</p>',
            '<p class="hero__lede mt-3">Free playbooks, worksheets, and the Starter Kit from the Amazon Best Seller. Use them. Adapt them. Run them on your buildings.</p>',
        ),
    },
    {
        "label": "A9 resources hero lede (payload)",
        "payload": (
            '"hero__lede mt-3","children":"Everything we wished existed when we were running our first portfolio. Use them. Adapt them. Run them on your buildings."',
            '"hero__lede mt-3","children":"Free playbooks, worksheets, and the Starter Kit from the Amazon Best Seller. Use them. Adapt them. Run them on your buildings."',
        ),
    },
    # ---- 26. Insert Free Downloads CardGrid section BEFORE the StarterKit section ----
    {
        "label": "#26 insert Free Downloads CardGrid (visible) — before starter-kit",
        "html": (
            '</section><section class="starter-kit',
            '</section>'
            '<section class="card-grid-section card-grid-section--paper">'
            '<div class="container">'
            '<span class="eyebrow">Free Downloads</span>'
            '<h2 class="mt-4 mb-4">Free tools for operators.</h2>'
            '<p class="lede" style="max-width:60ch">Worksheets and references from the Amazon Best Seller. Use them. Adapt them. Run them on your buildings.</p>'
            '<div class="card-grid card-grid--3">'
                '<div class="card"><h3 class="card__heading">The 5C™ Framework one-pager</h3><p class="card__body">The whole framework on one page. Print-ready. The version you hand to your CFO before a portfolio review.</p><a class="card__cta" href="../public/downloads/ppp-5c-framework-one-pager.pdf">Download →</a></div>'
                '<div class="card"><h3 class="card__heading">Five Questions Every Owner Should Ask About Their Building Data</h3><p class="card__body">A short worksheet to run in your next ops meeting. Identifies leakage, ownership gaps, and your top three monthly plays.</p><a class="card__cta" href="../public/downloads/ppp-five-questions-worksheet.pdf">Download →</a></div>'
                '<div class="card"><h3 class="card__heading">PPP Audit Worksheet</h3><p class="card__body">Start the Clarify pass on one of your buildings yourself. Map ownership, identify what&#x27;s portable, document what&#x27;s trustworthy.</p><a class="card__cta" href="../public/downloads/ppp-audit-worksheet.pdf">Download →</a></div>'
                '<div class="card card--gated"><h3 class="card__heading">Sample DDIA Report (Redacted)</h3><p class="card__body">Redacted. So you can see what a PPP Review actually delivers before you ask for one. Email-gated.</p><a class="card__cta" href="#starter-kit">Get the Sample →</a></div>'
            '</div>'
            '</div>'
            '</section><section class="starter-kit',
        ),
    },
    # ---- 27. "Beyond the Book" closing section ----
    {
        "label": "#27 closing h2 (visible)",
        "html": ('<h2 class="mt-4 mb-4">Run the play on one building.</h2>',
                 '<h2 class="mt-4 mb-4">Past the resources? Run a real review.</h2>'),
    },
    {
        "label": "#27 closing h2 (payload)",
        "payload": ('"mt-4 mb-4","children":"Run the play on one building."',
                    '"mt-4 mb-4","children":"Past the resources? Run a real review."'),
    },
    {
        "label": "#27 closing lede (visible)",
        "html": (
            'Want a complimentary PPP Review? We&#x27;ll run the Clarify pass on one of your buildings and leave you with a one-pager you can act on.',
            'We&#x27;ll run the Clarify pass on one of your buildings — at no cost — and leave you with a one-pager you can act on Monday. Owner-controlled. No software pitch. No rip-and-replace.',
        ),
    },
    {
        "label": "#27 closing lede (payload)",
        "payload": (
            "\"Want a complimentary PPP Review? We'll run the Clarify pass on one of your buildings and leave you with a one-pager you can act on.\"",
            "\"We'll run the Clarify pass on one of your buildings — at no cost — and leave you with a one-pager you can act on Monday. Owner-controlled. No software pitch. No rip-and-replace.\"",
        ),
    },
    # ---- A6. Footer tagline ----
    {
        "label": "A6 footer tagline (visible)",
        "html": (
            '<p class="footer__tagline">A best-selling book and podcast for commercial real estate leaders.</p>',
            '<p class="footer__tagline">Amazon Best Seller. The CRE strategy playbook for owners, operators, and the leaders building the future of the industry.</p>',
        ),
    },
    {
        "label": "A6 footer tagline (payload)",
        "payload": (
            '"className":"footer__tagline","children":"A best-selling book and podcast for commercial real estate leaders."',
            '"className":"footer__tagline","children":"Amazon Best Seller. The CRE strategy playbook for owners, operators, and the leaders building the future of the industry."',
        ),
    },
    # ---- head additions ----
    {
        "label": "head additions (resources)",
        "html": (
            '<link rel="stylesheet" href="../_next/static/css/f3145fbd800cc712.css" data-precedence="next"/>',
            '<link rel="stylesheet" href="../_next/static/css/f3145fbd800cc712.css" data-precedence="next"/>'
            '<link rel="stylesheet" href="../public/css/ppp-additions.css"/>'
            '<link rel="icon" type="image/x-icon" href="../public/favicon.ico"/>'
            '<link rel="icon" type="image/png" sizes="32x32" href="../public/favicon-32x32.png"/>'
            '<link rel="icon" type="image/png" sizes="16x16" href="../public/favicon-16x16.png"/>'
            '<link rel="apple-touch-icon" sizes="180x180" href="../public/apple-touch-icon.png"/>'
            '<link rel="manifest" href="../public/site.webmanifest"/>'
            '<meta name="theme-color" content="#1B3526"/>'
            '<meta property="og:title" content="Free Resources — Peak Property Performance®"/>'
            '<meta property="og:description" content="Free playbooks, worksheets, and the Starter Kit from the Amazon Best Seller."/>'
            '<meta property="og:type" content="website"/>'
            '<meta property="og:url" content="https://peakpropertyperformance.com/resources"/>'
            '<meta property="og:image" content="https://peakpropertyperformance.com/public/images/og-image.png"/>'
            '<meta name="twitter:card" content="summary_large_image"/>'
            '<meta name="twitter:image" content="https://peakpropertyperformance.com/public/images/og-image.png"/>',
        ),
    },
]
