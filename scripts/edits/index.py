# -*- coding: utf-8 -*-
"""Edits for /index.html (home page).

Items applied (from PPP_Sandbox_Content_Review_v2.md):
  A4, A5, A6, A7, A8 (head meta + footer + hero badge + eyebrow)
  2  (hero subhead)
  3  (thesis eyebrow)
  4  (thesis 3 column h3 rewrites)
  5  (5C eyebrow)
  6  (Champion outcome callout)
  7  (episode grid eyebrow + h2)
  8  (Get the Book card body)
  9  (credit line h2 + lede)
  35 (role grid CTAs)
  36 (Organization JSON-LD)
  38 (favicon refs)
"""

FILE = "index.html"

EDITS = [
    # ---- A7. Meta description ------------------------------------------------
    {
        "label": "A7 meta description (visible)",
        "html": (
            '<meta name="description" content="The CRE Strategy Playbook for Data, Digital &amp; AI. Game-changing strategies for commercial real estate owners who want control, NOI, and AI readiness — without the vendor lock-in tax. Best-selling book and podcast published by Fast Company Press."/>',
            '<meta name="description" content="Amazon Best Seller. The CRE strategy playbook for data, digital, and AI. Game-changing plays for owners who want NOI growth, AI readiness, and control — without vendor lock-in. Book + weekly podcast from Fast Company Press."/>',
        ),
    },
    {
        "label": "A7 meta description (Flight payload)",
        "payload": (
            '"name":"description","content":"The CRE Strategy Playbook for Data, Digital \\u0026 AI. Game-changing strategies for commercial real estate owners who want control, NOI, and AI readiness — without the vendor lock-in tax. Best-selling book and podcast published by Fast Company Press."',
            '"name":"description","content":"Amazon Best Seller. The CRE strategy playbook for data, digital, and AI. Game-changing plays for owners who want NOI growth, AI readiness, and control — without vendor lock-in. Book + weekly podcast from Fast Company Press."',
        ),
    },
    # ---- A5. Hero eyebrow ----------------------------------------------------
    {
        "label": "A5 hero eyebrow (visible)",
        "html": (
            '<span class="eyebrow">A Best-Selling Book &amp; Podcast for CRE Leaders</span>',
            '<span class="eyebrow">Amazon Best Seller · Podcast for CRE Leaders</span>',
        ),
    },
    {
        "label": "A5 hero eyebrow (Flight payload)",
        "payload": (
            '"children":"A Best-Selling Book \\u0026 Podcast for CRE Leaders"',
            '"children":"Amazon Best Seller · Podcast for CRE Leaders"',
        ),
    },
    # ---- 2. Hero subhead -----------------------------------------------------
    {
        "label": "#2 hero subhead (visible)",
        "html": (
            'Game-changing strategies for commercial real estate owners who want control, NOI, and AI readiness — without the vendor lock-in tax.',
            'For commercial real estate owners who want control, NOI growth, and AI readiness — without the vendor lock-in tax.',
        ),
        "html_count": 1,
    },
    {
        "label": "#2 hero subhead (payload)",
        "payload": (
            '"children":"Game-changing strategies for commercial real estate owners who want control, NOI, and AI readiness — without the vendor lock-in tax."',
            '"children":"For commercial real estate owners who want control, NOI growth, and AI readiness — without the vendor lock-in tax."',
        ),
    },
    # ---- A4. Hero book cover badge wrap (visible) ----------------------------
    {
        "label": "A4 hero book cover (visible) — add badge sibling",
        "html": (
            '<div class="book-cover-image"><img src="./api/media/file/cover.png" alt="Peak Property Performance® — book cover"/></div></div></div></section><section class="thesis-section',
            '<div class="book-cover-image book-cover-with-badge"><img src="./api/media/file/cover.png" alt="Peak Property Performance® — book cover"/><img src="./public/images/amazon-best-seller-400.png" alt="Amazon Best Seller" class="best-seller-badge"/></div></div></div></section><section class="thesis-section',
        ),
    },
    {
        "label": "A4 hero book cover (payload) — add badge sibling",
        "payload": (
            '[\"$\",\"div\",null,{\"className\":\"book-cover-image\",\"children\":[\"$\",\"img\",null,{\"src\":\"https://www.peakpropertyperformance.com/api/media/file/cover.png\",\"alt\":\"Peak Property Performance® — book cover\"}]}]',
            '[\"$\",\"div\",null,{\"className\":\"book-cover-image book-cover-with-badge\",\"children\":[[\"$\",\"img\",null,{\"src\":\"https://www.peakpropertyperformance.com/api/media/file/cover.png\",\"alt\":\"Peak Property Performance® — book cover\"}],[\"$\",\"img\",null,{\"src\":\"/public/images/amazon-best-seller-400.png\",\"alt\":\"Amazon Best Seller\",\"className\":\"best-seller-badge\"}]]}]',
        ),
        "payload_raw": True,
        "payload_count": 2,  # appears in both hero block & retailer block
    },
    # ---- 3. Thesis eyebrow ---------------------------------------------------
    {
        "label": "#3 thesis eyebrow (visible)",
        "html": ('<span class="eyebrow">Why This Playbook Now</span>',
                 '<span class="eyebrow">The Pattern</span>'),
    },
    {
        "label": "#3 thesis eyebrow (payload)",
        "payload": ('"eyebrow","children":"Why This Playbook Now"',
                    '"eyebrow","children":"The Pattern"'),
    },
    # ---- 4. Three column thesis h3s -----------------------------------------
    {
        "label": "#4 col1 h3 (visible)",
        "html": ('<h3>It&#x27;s not about collecting data.</h3>',
                 '<h3>Equipment isn&#x27;t intelligence.</h3>'),
    },
    {
        "label": "#4 col1 h3 (payload)",
        "payload": ('"children":"It\'s not about collecting data."',
                    '"children":"Equipment isn\'t intelligence."'),
    },
    {
        "label": "#4 col2 h3 (visible)",
        "html": ('<h3>Tech transformation is a team sport.</h3>',
                 '<h3>One specialist won&#x27;t get you there.</h3>'),
    },
    {
        "label": "#4 col2 h3 (payload)",
        "payload": ('"children":"Tech transformation is a team sport."',
                    '"children":"One specialist won\'t get you there."'),
    },
    {
        "label": "#4 col3 h3 (visible)",
        "html": ('<h3>The winners of tomorrow won&#x27;t be the ones with the most locations or the most capital.</h3>',
                 '<h3>The winners aren&#x27;t the ones with the most buildings.</h3>'),
    },
    {
        "label": "#4 col3 h3 (payload)",
        "payload": ('"children":"The winners of tomorrow won\'t be the ones with the most locations or the most capital."',
                    '"children":"The winners aren\'t the ones with the most buildings."'),
    },
    # ---- 5. 5C section eyebrow ----------------------------------------------
    {
        "label": "#5 5C eyebrow (visible)",
        "html": ('<span class="eyebrow">The Playbook</span><h2 class="mt-4 mb-5">The 5C™ Framework',
                 '<span class="eyebrow">The Framework</span><h2 class="mt-4 mb-5">The 5C™ Framework'),
    },
    {
        "label": "#5 5C eyebrow (payload)",
        "payload": ('"eyebrow","children":"The Playbook"',
                    '"eyebrow","children":"The Framework"'),
    },
    # ---- 6. Champion outcome callout (replace fivec__champion) --------------
    {
        "label": "#6 Champion callout (visible)",
        "html": (
            '<div class="fivec__champion">&quot;Champion&quot; is what happens when intelligence compounds across the portfolio — not just one building.</div>',
            '<div class="outcome-callout"><strong>The outcome is Champion.</strong><p>Intelligence that compounds across the portfolio. Not just one building.</p></div>',
        ),
    },
    {
        "label": "#6 Champion callout (payload)",
        "payload": (
            '[\"$\",\"div\",null,{\"className\":\"fivec__champion\",\"children\":\"\\\"Champion\\\" is what happens when intelligence compounds across the portfolio — not just one building.\"}]',
            '[\"$\",\"div\",null,{\"className\":\"outcome-callout\",\"children\":[[\"$\",\"strong\",null,{\"children\":\"The outcome is Champion.\"}],[\"$\",\"p\",null,{\"children\":\"Intelligence that compounds across the portfolio. Not just one building.\"}]]}]',
        ),
        "payload_raw": True,
    },
    # ---- 7. Episode grid eyebrow + h2 ---------------------------------------
    {
        "label": "#7 episode grid header (visible)",
        "html": (
            '<div class="episode-grid__header"><div><span class="eyebrow">Peak Property Performance® Podcast latest episodes</span></div>',
            '<div class="episode-grid__header"><div><span class="eyebrow">The Podcast</span><h2 class="mt-3 mb-0">This week&#x27;s playbook conversations.</h2></div>',
        ),
    },
    {
        "label": "#7 episode grid header (payload)",
        "payload": (
            '[\"$\",\"div\",null,{\"children\":[[\"$\",\"span\",null,{\"className\":\"eyebrow\",\"children\":\"Peak Property Performance® Podcast latest episodes\"}],null]}]',
            '[\"$\",\"div\",null,{\"children\":[[\"$\",\"span\",null,{\"className\":\"eyebrow\",\"children\":\"The Podcast\"}],[\"$\",\"h2\",null,{\"className\":\"mt-3 mb-0\",\"children\":\"This week\'s playbook conversations.\"}]]}]',
        ),
        "payload_raw": True,
    },
    # ---- 8. Get the Book card body ------------------------------------------
    {
        "label": "#8 Get the Book card body (visible)",
        "html": (
            '<p class="card__body">Available at Amazon, Barnes &amp; Noble, Bookshop, and Hudson. Bulk pricing through Porchlight.</p>',
            '<p class="card__body">Amazon Best Seller. Available at Amazon, Barnes &amp; Noble, Bookshop, and Hudson. Forewords by Dorit Fischer (NAI Shames Makovsky) and Zain Jaffer (Blue Field Capital).</p>',
        ),
    },
    {
        "label": "#8 Get the Book card body (payload)",
        "payload": (
            '"children":"Available at Amazon, Barnes \\u0026 Noble, Bookshop, and Hudson. Bulk pricing through Porchlight."',
            '"children":"Amazon Best Seller. Available at Amazon, Barnes \\u0026 Noble, Bookshop, and Hudson. Forewords by Dorit Fischer (NAI Shames Makovsky) and Zain Jaffer (Blue Field Capital)."',
        ),
    },
    # ---- 9. Credit line h2 + lede -------------------------------------------
    {
        "label": "#9 credit line h2 (visible)",
        "html": ('<h2 class="mt-4 mb-4">Written by operators. For operators.</h2>',
                 '<h2 class="mt-4 mb-4">Three operators. One playbook.</h2>'),
    },
    {
        "label": "#9 credit line h2 (payload)",
        "payload": ('"children":"Written by operators. For operators."',
                    '"children":"Three operators. One playbook."'),
    },
    {
        "label": "#9 credit line lede (visible)",
        "html": (
            'Bill Douglas, Drew Hall, and Ryan R. Goble — three voices, decades of technology, operations, and CRE -  one playbook.',
            'Bill Douglas, Drew Hall, and Ryan R. Goble — decades of operating CRE technology, distilled into a plan any owner can run.',
        ),
    },
    {
        "label": "#9 credit line lede (payload)",
        "payload": (
            '"children":"Bill Douglas, Drew Hall, and Ryan R. Goble — three voices, decades of technology, operations, and CRE -  one playbook."',
            '"children":"Bill Douglas, Drew Hall, and Ryan R. Goble — decades of operating CRE technology, distilled into a plan any owner can run."',
        ),
    },
    # ---- A6. Footer tagline -------------------------------------------------
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
    # ---- 35. Role grid generic CTAs ----------------------------------------
    {
        "label": "#35 role-card CTA (visible)",
        "html": ('<span class="role-card__cta">Read More<!-- --> →</span>',
                 '<span class="role-card__cta">See Your Role<!-- --> →</span>'),
        "html_count": 4,
    },
    {
        "label": "#35 role-card CTA (payload)",
        "payload": ('"className":"role-card__cta","children":["Read More"," →"]',
                    '"className":"role-card__cta","children":["See Your Role"," →"]'),
        "payload_count": 4,
    },
    # ---- A8 + 36 + 38. Head additions: OG, favicon, ppp-additions.css, JSON-LD ----
    {
        "label": "head additions: ppp-additions.css + favicon + OG + JSON-LD (visible)",
        "html": (
            '<link rel="stylesheet" href="./_next/static/css/f3145fbd800cc712.css" data-precedence="next"/>',
            '<link rel="stylesheet" href="./_next/static/css/f3145fbd800cc712.css" data-precedence="next"/>'
            '<link rel="stylesheet" href="./public/css/ppp-additions.css"/>'
            '<link rel="icon" type="image/x-icon" href="./public/favicon.ico"/>'
            '<link rel="icon" type="image/png" sizes="32x32" href="./public/favicon-32x32.png"/>'
            '<link rel="icon" type="image/png" sizes="16x16" href="./public/favicon-16x16.png"/>'
            '<link rel="apple-touch-icon" sizes="180x180" href="./public/apple-touch-icon.png"/>'
            '<link rel="manifest" href="./public/site.webmanifest"/>'
            '<meta name="theme-color" content="#1B3526"/>'
            '<meta property="og:title" content="Peak Property Performance® — Amazon Best Seller"/>'
            '<meta property="og:description" content="The CRE strategy playbook for data, digital, and AI. Amazon Best Seller from Fast Company Press."/>'
            '<meta property="og:type" content="website"/>'
            '<meta property="og:url" content="https://peakpropertyperformance.com/"/>'
            '<meta property="og:image" content="https://peakpropertyperformance.com/public/images/og-image.png"/>'
            '<meta property="og:image:width" content="1200"/>'
            '<meta property="og:image:height" content="630"/>'
            '<meta name="twitter:card" content="summary_large_image"/>'
            '<meta name="twitter:image" content="https://peakpropertyperformance.com/public/images/og-image.png"/>'
            '<script type="application/ld+json">{"@context":"https://schema.org","@type":"Organization","name":"Peak Property Performance","alternateName":"PPP","url":"https://peakpropertyperformance.com","logo":"https://peakpropertyperformance.com/api/media/file/fast-company-press.webp","sameAs":["https://www.amazon.com/Peak-Property-Performance-Game-Changing-Strategies/dp/1639081283/"],"parentOrganization":{"@type":"Organization","name":"OpticWise","url":"https://opticwise.com"}}</script>',
        ),
    },
]
