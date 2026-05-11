# -*- coding: utf-8 -*-
"""Edits for /podcast/index.html (item 25, A6, head additions, PodcastSeries JSON-LD)."""

FILE = "podcast/index.html"

EDITS = [
    # ---- 25. Hero lede ----
    {
        "label": "#25 hero lede (visible)",
        "html": (
            '<p class="hero__lede mt-3">Conversations with owners, operators, and the people building the future of commercial real estate. Hosted by Bill Douglas and Drew Hall.</p>',
            '<p class="hero__lede mt-3">Weekly conversations with CRE owners, operators, and the leaders building the future of the industry. Hosted by Bill Douglas and Drew Hall — co-authors of the Amazon Best Seller Peak Property Performance®.</p>',
        ),
    },
    {
        "label": "#25 hero lede (payload)",
        "payload": (
            '"hero__lede mt-3","children":"Conversations with owners, operators, and the people building the future of commercial real estate. Hosted by Bill Douglas and Drew Hall."',
            '"hero__lede mt-3","children":"Weekly conversations with CRE owners, operators, and the leaders building the future of the industry. Hosted by Bill Douglas and Drew Hall — co-authors of the Amazon Best Seller Peak Property Performance®."',
        ),
    },
    # ---- 35. Episode card "Read More" -> "Listen Now" (if present) ----
    {
        "label": "#35 episode card CTA (visible)",
        "html": ('<span class="episode-card__cta">Read More<!-- --> →</span>',
                 '<span class="episode-card__cta">Listen Now<!-- --> →</span>'),
        "optional": True,
    },
    {
        "label": "#35 episode card CTA (payload)",
        "payload": ('"className":"episode-card__cta","children":["Read More"," →"]',
                    '"className":"episode-card__cta","children":["Listen Now"," →"]'),
        "optional": True,
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
    # ---- head additions (podcast — PodcastSeries JSON-LD) ----
    {
        "label": "head additions (podcast)",
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
            '<meta property="og:title" content="Peak Property Performance® Podcast"/>'
            '<meta property="og:description" content="Weekly conversations with CRE owners, operators, and the leaders building the future of the industry."/>'
            '<meta property="og:type" content="website"/>'
            '<meta property="og:url" content="https://peakpropertyperformance.com/podcast"/>'
            '<meta property="og:image" content="https://peakpropertyperformance.com/public/images/og-image.png"/>'
            '<meta property="og:image:width" content="1200"/>'
            '<meta property="og:image:height" content="630"/>'
            '<meta name="twitter:card" content="summary_large_image"/>'
            '<meta name="twitter:image" content="https://peakpropertyperformance.com/public/images/og-image.png"/>'
            '<script type="application/ld+json">{"@context":"https://schema.org","@type":"PodcastSeries","name":"Peak Property Performance Podcast","url":"https://peakpropertyperformance.com/podcast","webFeed":"https://anchor.fm/s/1057cecf4/podcast/rss","author":[{"@type":"Person","name":"Bill Douglas"},{"@type":"Person","name":"Drew Hall"}]}</script>',
        ),
    },
]
