# -*- coding: utf-8 -*-
"""Footer + head additions for /be-on-the-show/index.html."""

FILE = "be-on-the-show/index.html"

EDITS = [
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
    {
        "label": "head additions (be-on-the-show)",
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
            '<meta property="og:title" content="Be on the Peak Property Performance® Podcast"/>'
            '<meta property="og:description" content="Pitch yourself as a guest. Open to CRE operators, PropTech founders, capital allocators, and category experts."/>'
            '<meta property="og:type" content="website"/>'
            '<meta property="og:url" content="https://peakpropertyperformance.com/be-on-the-show"/>'
            '<meta property="og:image" content="https://peakpropertyperformance.com/public/images/og-image.png"/>'
            '<meta name="twitter:card" content="summary_large_image"/>'
            '<meta name="twitter:image" content="https://peakpropertyperformance.com/public/images/og-image.png"/>',
        ),
    },
]
