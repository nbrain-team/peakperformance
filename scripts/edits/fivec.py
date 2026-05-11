# -*- coding: utf-8 -*-
"""Edits for /5c-framework/index.html (items 22-24, A6, head additions)."""

FILE = "5c-framework/index.html"

EDITS = [
    # ---- 22. "Why this order" h2 ----
    {
        "label": "#22 order h2 (visible)",
        "html": ('<h2 class="mt-4 mb-5">The order isn&#x27;t arbitrary.</h2>',
                 '<h2 class="mt-4 mb-5">Order matters. Here&#x27;s why.</h2>'),
    },
    {
        "label": "#22 order h2 (payload)",
        "payload": ('"mt-4 mb-5","children":"The order isn\'t arbitrary."',
                    '"mt-4 mb-5","children":"Order matters. Here\'s why."'),
    },
    # ---- 23. FAQ section h2 ----
    {
        "label": "#23 FAQ h2 (visible)",
        "html": ('About the 5C™ Framework.</h2>',
                 'What owners ask before running it.</h2>'),
    },
    {
        "label": "#23 FAQ h2 (payload)",
        "payload": ('"About the 5C™ Framework."',
                    '"What owners ask before running it."'),
    },
    # ---- 24. Closing CTA paragraph — Monday ----
    {
        "label": "#24 closing CTA paragraph (visible+payload identical content)",
        "html": (
            "We&#x27;ll do the Clarify pass on one property — at no cost — and leave you with a one-pager you can act on. No software pitch. No rip-and-replace.",
            "We&#x27;ll run the Clarify pass on one property — at no cost — and leave you with a one-pager you can act on Monday. No software pitch. No rip-and-replace.",
        ),
    },
    {
        "label": "#24 closing CTA paragraph (payload)",
        "payload": (
            "We'll do the Clarify pass on one property — at no cost — and leave you with a one-pager you can act on. No software pitch. No rip-and-replace.",
            "We'll run the Clarify pass on one property — at no cost — and leave you with a one-pager you can act on Monday. No software pitch. No rip-and-replace.",
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
    # ---- 36 (FAQPage JSON-LD) + 38 head additions ----
    {
        "label": "head additions (5C — favicon + OG + FAQPage JSON-LD)",
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
            '<meta property="og:title" content="The 5C™ Framework — Peak Property Performance®"/>'
            '<meta property="og:description" content="Clarify · Connect · Collect · Coordinate · Control. The strategic playbook for compounding property intelligence across a CRE portfolio."/>'
            '<meta property="og:type" content="website"/>'
            '<meta property="og:url" content="https://peakpropertyperformance.com/5c-framework"/>'
            '<meta property="og:image" content="https://peakpropertyperformance.com/public/images/og-image.png"/>'
            '<meta property="og:image:width" content="1200"/>'
            '<meta property="og:image:height" content="630"/>'
            '<meta name="twitter:card" content="summary_large_image"/>'
            '<meta name="twitter:image" content="https://peakpropertyperformance.com/public/images/og-image.png"/>'
            '<script type="application/ld+json">{"@context":"https://schema.org","@type":"FAQPage","mainEntity":['
                '{"@type":"Question","name":"How long does it take to run the Framework?","acceptedAnswer":{"@type":"Answer","text":"For a single property, a Clarify pass takes about a week. For a portfolio, the full 5C™ cycle is a quarter for the first building and faster on every building after."}},'
                '{"@type":"Question","name":"Do I need to throw out my existing tech stack?","acceptedAnswer":{"@type":"Answer","text":"No. The Framework is platform-agnostic by design. Most owners keep what works and add owner-controlled connectivity and governance underneath."}}'
            ']}</script>',
        ),
    },
]
