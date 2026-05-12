# -*- coding: utf-8 -*-
"""Edits for /ppp-review/index.html (items 1, 28-30, A6, head additions).

Item 1 (P0): Static PPP Review form + mailto fallback is maintained via
scripts/build/build-ppp-review-form.py (visible HTML + Flight payload + body-end
handler). The former OpticWise embed loader is intentionally NOT shipped here:
it injected a second mount next to the static form and interfered with submits.

Historical note: /be-on-the-show/ still uses the OpticWise embed pattern."""

FILE = "ppp-review/index.html"

EDITS = [
    # ---- 28. Hero H1 + add eyebrow (visible) ----
    {
        "label": "#28 hero eyebrow + H1 (visible)",
        "html": (
            '<h1 class="hero__heading mt-4">Complimentary CRE Data &amp; Digital Review.</h1>',
            '<span class="eyebrow">Complimentary, no software pitch</span><h1 class="hero__heading mt-4">One building. 45 minutes. A one-pager you can act on Monday.</h1>',
        ),
    },
    {
        "label": "#28 hero H1 (payload)",
        "payload": (
            '"hero__heading mt-4","children":"Complimentary CRE Data & Digital Review."',
            '"hero__heading mt-4","children":"One building. 45 minutes. A one-pager you can act on Monday."',
        ),
    },
    # NOTE: the eyebrow on the visible hero is INSERTED before H1; the
    # payload's hero already has another structure — we don't add an extra
    # eyebrow node to the payload to avoid restructuring the container.
    # ---- 30. Closing alt-path h2 ----
    {
        "label": "#30 closing alt-path h2 (visible)",
        "html": ('<h2 class="mt-4 mb-4">Want to read or listen first?</h2>',
                 '<h2 class="mt-4 mb-4">Not ready? Start here.</h2>'),
    },
    {
        "label": "#30 closing alt-path h2 (payload)",
        "payload": ('"mt-4 mb-4","children":"Want to read or listen first?"',
                    '"mt-4 mb-4","children":"Not ready? Start here."'),
    },
    # ---- 29. Stafford trust strip (visible) — insert between
    # "Four things, in one read-out" cards section and the form section ----
    {
        "label": "#29 Stafford trust strip (visible) — insert before rich-content form section",
        "html": (
            # Anchor: the rich-content-section that contains the form prompt
            '</section><section class="rich-content-section">',
            '</section>'
            '<section class="pull-quote pull-quote--dark"><div class="container">'
            '<blockquote class="pull-quote__text">“After implementing the OpticWise methodology at our 200-acre Aspiria campus, I can attest: These strategies work.”</blockquote>'
            '<p class="pull-quote__attr">Chad J. Stafford, President, Occidental Management, Inc.</p>'
            '</div></section>'
            '<section class="rich-content-section">',
        ),
    },
    # ---- 1 (P0). Form embed: swap the "Please use the form below" prompt ----
    {
        "label": "#1 P0 form mount (visible) — replace prompt with embed container",
        "html": (
            '<div class="rich-content"><p>Please use the form below.</p></div>',
            '<div class="rich-content"><p>Please use the form below to share who you are, the building, and what you’re hoping to learn. We respond within 1 business day.</p></div>'
            '<div class="ppp-review-form-mount"><div data-opticwise-form="ppp-review"></div></div>',
        ),
    },
    {
        "label": "#1 P0 form mount (payload) — replace prompt with embed container",
        "payload": (
            '"dangerouslySetInnerHTML":{"__html":"<p>Please use the form below.</p>"}',
            '"dangerouslySetInnerHTML":{"__html":"<p>Please use the form below to share who you are, the building, and what you’re hoping to learn. We respond within 1 business day.</p><div class=\\"ppp-review-form-mount\\"><div data-opticwise-form=\\"ppp-review\\"></div></div>"}',
        ),
    },
    # ---- A6 footer tagline ----
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
        "label": "head additions (ppp-review)",
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
            '<meta property="og:title" content="Complimentary CRE Data & Digital Review"/>'
            '<meta property="og:description" content="One building. 45 minutes. A one-pager you can act on Monday."/>'
            '<meta property="og:type" content="website"/>'
            '<meta property="og:url" content="https://peakpropertyperformance.com/ppp-review"/>'
            '<meta property="og:image" content="https://peakpropertyperformance.com/public/images/og-image.png"/>'
            '<meta name="twitter:card" content="summary_large_image"/>'
            '<meta name="twitter:image" content="https://peakpropertyperformance.com/public/images/og-image.png"/>',
        ),
    },
]
