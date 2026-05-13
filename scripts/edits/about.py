# -*- coding: utf-8 -*-
"""Edits for /about/index.html."""

FILE = "about/index.html"

EDITS = [
    # ---- 17. Tighten the /about hero subhead ----
    {
        "label": "#17 hero subhead (visible)",
        "html": (
            'Decades of operating technology for commercial real estate — translated into a playbook any owner can run. We didn&#x27;t write a manifesto. We wrote a plan owners can run on Monday morning.',
            'Decades of operating CRE technology — translated into a playbook any owner can run. We didn&#x27;t write a manifesto. We wrote plays you can run on Monday morning.',
        ),
    },
    {
        "label": "#17 hero subhead (payload)",
        "payload": (
            "\"children\":\"Decades of operating technology for commercial real estate — translated into a playbook any owner can run. We didn't write a manifesto. We wrote a plan owners can run on Monday morning.\"",
            "\"children\":\"Decades of operating CRE technology — translated into a playbook any owner can run. We didn't write a manifesto. We wrote plays you can run on Monday morning.\"",
        ),
    },
    # ---- 18. Sharpen Conviction 3 (remove hedge "can be") ----
    {
        "label": "#18 Conviction 3 (visible)",
        "html": (
            'One building&#x27;s investment can be overhead. Five buildings standardized on the same backplane is leverage. Fifty is a moat.',
            'One building&#x27;s investment is overhead. Five buildings standardized on the same backplane is leverage. Fifty is a moat.',
        ),
    },
    {
        "label": "#18 Conviction 3 (payload)",
        "payload": (
            "\"One building's investment can be overhead. Five buildings standardized on the same backplane is leverage. Fifty is a moat.\"",
            "\"One building's investment is overhead. Five buildings standardized on the same backplane is leverage. Fifty is a moat.\"",
        ),
    },
    # ---- 19. Behind the Book + closing CTA: "Request a PPP Review" -> "Run the Play on One Building" ----
    {
        "label": "#19 PPP Review CTA (visible) — btn-primary",
        "html": (
            '<a class="btn btn-primary btn-lg" href="/ppp-review">Request a PPP Review</a>',
            '<a class="btn btn-primary btn-lg" href="../ppp-review/index.html">Run the Play on One Building</a>',
        ),
        "html_count": 2,
    },
    {
        "label": "#19 PPP Review CTA (payload) — btn-primary",
        "payload": (
            '"className":"btn btn-primary btn-lg","children":"Request a PPP Review"',
            '"className":"btn btn-primary btn-lg","children":"Run the Play on One Building"',
        ),
        "payload_count": 2,
    },
    # ---- A10. Bill Douglas bio — add Amazon Best Seller credit ----
    {
        "label": "A10 Bill bio (visible) — Amazon Best Seller credit",
        "html": (
            '<p class="author-card__bio">For decades, Bill has helped organizations turn data and digital infrastructure into owner-controlled assets that drive NOI, control, and AI readiness.',
            '<p class="author-card__bio">Bill is co-author of the Amazon Best Seller <em>Peak Property Performance®</em> and CEO of OpticWise. For decades, he&#x27;s helped organizations turn data and digital infrastructure into owner-controlled assets that drive NOI, control, and AI readiness.',
        ),
    },
    {
        "label": "A10 Bill bio (payload)",
        "payload": (
            '"author-card__bio","children":"For decades, Bill has helped organizations turn data and digital infrastructure into owner-controlled assets that drive NOI, control, and AI readiness.',
            '"author-card__bio","children":"Bill is co-author of the Amazon Best Seller Peak Property Performance® and CEO of OpticWise. For decades, he\'s helped organizations turn data and digital infrastructure into owner-controlled assets that drive NOI, control, and AI readiness.',
        ),
    },
    # ---- 20. Tighten Bill Douglas bio closing ----
    {
        "label": "#20 Bill bio closing (visible)",
        "html": (
            'When he&#x27;s not running OpticWise, he&#x27;s coaching execs/entrepreneurs as the &quot;ResilienceGuy&quot;, hosting the PPP Podcast, and pursuing unique shared experiences in this treasured life.',
            'When he&#x27;s not running OpticWise, he&#x27;s hosting the Peak Property Performance® Podcast and coaching execs as the ResilienceGuy.',
        ),
    },
    {
        "label": "#20 Bill bio closing (payload)",
        "payload": (
            'When he\'s not running OpticWise, he\'s coaching execs/entrepreneurs as the \\"ResilienceGuy\\", hosting the PPP Podcast, and pursuing unique shared experiences in this treasured life.',
            "When he's not running OpticWise, he's hosting the Peak Property Performance® Podcast and coaching execs as the ResilienceGuy.",
        ),
    },
    # ---- 21. Foreword attributions ----
    {
        "label": "#21 Dorit foreword attribution (visible)",
        "html": (
            '>Dorit Fischer, Foreword 1 · Partner, NAI Shames Makovsky<',
            '>Dorit Fischer · NAI Shames Makovsky · Foreword writer<',
        ),
    },
    {
        "label": "#21 Dorit foreword attribution (payload)",
        "payload": (
            '"Dorit Fischer, Foreword 1 · Partner, NAI Shames Makovsky"',
            '"Dorit Fischer · NAI Shames Makovsky · Foreword writer"',
        ),
    },
    {
        "label": "#21 Zain foreword attribution (visible)",
        "html": (
            'Zain Jaffer, Foreword 2 · Blue Field Capital &amp; Zain Ventures Family Office',
            'Zain Jaffer · Blue Field Capital · Foreword writer',
        ),
    },
    {
        "label": "#21 Zain foreword attribution (payload)",
        "payload": (
            '"Zain Jaffer, Foreword 2 · Blue Field Capital & Zain Ventures Family Office"',
            '"Zain Jaffer · Blue Field Capital · Foreword writer"',
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
    # ---- 36 + 38 head additions ----
    {
        "label": "head additions (about)",
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
            '<meta property="og:title" content="About — Peak Property Performance®"/>'
            '<meta property="og:description" content="Bill Douglas, Drew Hall, and Ryan R. Goble — co-authors of the Amazon Best Seller Peak Property Performance®."/>'
            '<meta property="og:type" content="website"/>'
            '<meta property="og:url" content="https://peakpropertyperformance.com/about"/>'
            '<meta property="og:image" content="https://peakpropertyperformance.com/public/images/og-image.png"/>'
            '<meta property="og:image:width" content="1200"/>'
            '<meta property="og:image:height" content="630"/>'
            '<meta name="twitter:card" content="summary_large_image"/>'
            '<meta name="twitter:image" content="https://peakpropertyperformance.com/public/images/og-image.png"/>',
        ),
    },
]
