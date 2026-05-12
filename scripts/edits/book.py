# -*- coding: utf-8 -*-
"""Edits for /book/index.html."""

FILE = "book/index.html"

EDITS = [
    # ---- A7. Meta description (book) ----
    {
        "label": "A7 book meta description (visible)",
        "html": (
            '<meta name="description" content="Peak Property Performance®: Game-Changing AI and Digital Strategies for Commercial Real Estate. By Bill Douglas and Drew Hall, with Ryan R. Goble. Published by Fast Company Press."/>',
            '<meta name="description" content="Amazon Best Seller. Peak Property Performance® — Game-Changing AI and Digital Strategies for Commercial Real Estate. By Bill Douglas and Drew Hall, with Ryan R. Goble. Published by Fast Company Press."/>',
        ),
    },
    {
        "label": "A7 book meta description (payload)",
        "payload": (
            '"name":"description","content":"Peak Property Performance®: Game-Changing AI and Digital Strategies for Commercial Real Estate. By Bill Douglas and Drew Hall, with Ryan R. Goble. Published by Fast Company Press."',
            '"name":"description","content":"Amazon Best Seller. Peak Property Performance® — Game-Changing AI and Digital Strategies for Commercial Real Estate. By Bill Douglas and Drew Hall, with Ryan R. Goble. Published by Fast Company Press."',
        ),
    },
    # ---- A3. Hero eyebrow → Amazon Best Seller · Fast Company Press --------
    {
        "label": "A3 hero eyebrow (visible)",
        "html": (
            '<span class="eyebrow">Published by Fast Company Press</span><h1 class="hero__heading mt-4">Peak Property Performance®.</h1>',
            '<span class="eyebrow eyebrow--bestseller">Amazon Best Seller · Fast Company Press</span><h1 class="hero__heading mt-4">Peak Property Performance®.</h1>',
        ),
    },
    {
        "label": "A3 hero eyebrow (payload)",
        "payload": (
            '"className":"eyebrow","children":"Published by Fast Company Press"',
            '"className":"eyebrow eyebrow--bestseller","children":"Amazon Best Seller · Fast Company Press"',
        ),
    },
    # ---- 10. Hook line under H1 -------------------------------------------
    {
        "label": "#10 hero hook (visible) — insert h2 after h1",
        "html": (
            '<h1 class="hero__heading mt-4">Peak Property Performance®.</h1>',
            '<h1 class="hero__heading mt-4">Peak Property Performance®.</h1><h2 class="hero__hook">The strategy playbook for CRE owners who refuse to rent their decisions from their vendors.</h2>',
        ),
    },
    {
        "label": "#10 hero hook (payload) — insert hook node after h1",
        "payload": (
            '"hero__heading mt-4","children":"Peak Property Performance®."}]',
            '"hero__heading mt-4","children":"Peak Property Performance®."}],["$","h2",null,{"className":"hero__hook","children":"The strategy playbook for CRE owners who refuse to rent their decisions from their vendors."}]',
        ),
    },
    # ---- 12. Tighten BookHero body paragraph ------------------------------
    {
        "label": "#12 BookHero body (visible)",
        "html": (
            '<p class="hero__lede mt-3">Game-Changing AI and Digital Strategies for Commercial Real Estate. By Bill Douglas and Drew Hall, with Ryan R. Goble. Forewords by Dorit Fischer of NAI Shames Makovsky and Zain Jaffer of Blue Field Capital.</p>',
            '<p class="hero__lede mt-3">By Bill Douglas and Drew Hall, with Ryan R. Goble. Forewords by Dorit Fischer (NAI Shames Makovsky) and Zain Jaffer (Blue Field Capital). Published by Fast Company Press.</p>',
        ),
    },
    {
        "label": "#12 BookHero body (payload)",
        "payload": (
            '"hero__lede mt-3","children":"Game-Changing AI and Digital Strategies for Commercial Real Estate. By Bill Douglas and Drew Hall, with Ryan R. Goble. Forewords by Dorit Fischer of NAI Shames Makovsky and Zain Jaffer of Blue Field Capital."',
            '"hero__lede mt-3","children":"By Bill Douglas and Drew Hall, with Ryan R. Goble. Forewords by Dorit Fischer (NAI Shames Makovsky) and Zain Jaffer (Blue Field Capital). Published by Fast Company Press."',
        ),
    },
    # ---- 11. CTA buttons: Amazon primary, All Retailers secondary ---------
    {
        "label": "#11 CTA buttons (visible)",
        "html": (
            '<a class="btn btn-primary btn-lg" href="#retailers">View Retailers</a>',
            '<a class="btn btn-primary btn-lg" href="https://www.amazon.com/Peak-Property-Performance-Game-Changing-Strategies/dp/1639081283/" target="_blank" rel="noopener">Get the Book on Amazon</a><a class="btn btn-secondary btn-lg" href="#retailers">All Retailers</a><a class="btn btn-secondary btn-lg" href="#audiobook-retailers">Listen to the book</a>',
        ),
    },
    {
        "label": "#11 CTA buttons (payload)",
        "payload": (
            '"href":"#retailers","className":"btn btn-primary btn-lg","children":"View Retailers"',
            '"href":"https://www.amazon.com/Peak-Property-Performance-Game-Changing-Strategies/dp/1639081283/","target":"_blank","rel":"noopener","className":"btn btn-primary btn-lg","children":"Get the Book on Amazon"}],["$","a",null,{"href":"#retailers","className":"btn btn-secondary btn-lg","children":"All Retailers"}],["$","a",null,{"href":"#audiobook-retailers","className":"btn btn-secondary btn-lg","children":"Listen to the book"',
        ),
    },
    # ---- A2. Book covers — swap cover.png for composite (hero + retailer) ----
    {
        "label": "A2 book cover (visible) — composite (hero + retailer)",
        "html": (
            '<div class="book-cover-image"><img src="../api/media/file/cover.png" alt="Peak Property Performance® — book cover"/></div>',
            '<div class="book-cover-image"><img src="../public/images/book-cover-with-bestseller.png" alt="Peak Property Performance® — Amazon Best Seller — book cover from Fast Company Press."/></div>',
        ),
        "html_count": 2,
    },
    {
        "label": "A2 book cover (payload) — composite (hero + retailer)",
        "payload": (
            '["$","div",null,{"className":"book-cover-image","children":["$","img",null,{"src":"https://www.peakpropertyperformance.com/api/media/file/cover.png","alt":"Peak Property Performance® — book cover"}]}]',
            '["$","div",null,{"className":"book-cover-image","children":["$","img",null,{"src":"/public/images/book-cover-with-bestseller.png","alt":"Peak Property Performance® — Amazon Best Seller — book cover from Fast Company Press."}]}]',
        ),
        "payload_count": 2,
    },
    # ---- 13. "What you get" → "What's in the book" ------------------------
    {
        "label": "#13 What you get heading (visible)",
        "html": ('<h2 class="mt-4 mb-4">What you get.</h2>',
                 '<h2 class="mt-4 mb-4">What&#x27;s in the book.</h2>'),
    },
    {
        "label": "#13 What you get heading (payload)",
        "payload": ('"mt-4 mb-4","children":"What you get."',
                    '"mt-4 mb-4","children":"What\'s in the book."'),
    },
    # ---- 14. Card 2 — Implementation Patterns -----------------------------
    {
        "label": "#14 Implementation Patterns body (visible)",
        "html": (
            '<p class="card__body">Real-world patterns from the field. What works, what fails, and what to do differently when your portfolio scales past a few buildings.</p>',
            '<p class="card__body">What works. What fails. What changes when your portfolio scales past five buildings.</p>',
        ),
    },
    {
        "label": "#14 Implementation Patterns body (payload)",
        "payload": (
            '"card__body","children":"Real-world patterns from the field. What works, what fails, and what to do differently when your portfolio scales past a few buildings."',
            '"card__body","children":"What works. What fails. What changes when your portfolio scales past five buildings."',
        ),
    },
    # ---- 14. Card 3 — Tools You Can Use -----------------------------------
    {
        "label": "#14 Tools You Can Use body (visible)",
        "html": (
            '<p class="card__body">Worksheets, audit templates, and decision frameworks. Designed to be used by an operating team, not filed away as a reference.</p>',
            '<p class="card__body">Worksheets, audit templates, and decision frameworks an operating team will actually use — not file away.</p>',
        ),
    },
    {
        "label": "#14 Tools You Can Use body (payload)",
        "payload": (
            '"card__body","children":"Worksheets, audit templates, and decision frameworks. Designed to be used by an operating team, not filed away as a reference."',
            '"card__body","children":"Worksheets, audit templates, and decision frameworks an operating team will actually use — not file away."',
        ),
    },
    # ---- 14. Card 4 — The Operator Voice ----------------------------------
    {
        "label": "#14 Operator Voice body (visible)",
        "html": (
            '<p class="card__body">No academic theory. Written by people who own and run CRE — for people who own and run CRE.</p>',
            '<p class="card__body">Written by operators. For operators. Zero academic theory.</p>',
        ),
    },
    {
        "label": "#14 Operator Voice body (payload)",
        "payload": (
            '"card__body","children":"No academic theory. Written by people who own and run CRE — for people who own and run CRE."',
            '"card__body","children":"Written by operators. For operators. Zero academic theory."',
        ),
    },
    # ---- 15. Dorit Fischer attribution (foreword pull quote) -------------
    {
        "label": "#15 Dorit Fischer attribution (visible)",
        "html": ('>Dorit Fischer · Partner, NAI Shames Makovsky · Foreword<',
                 '>Dorit Fischer wrote the foreword. She’s a Partner at NAI Shames Makovsky.<'),
    },
    {
        "label": "#15 Dorit Fischer attribution (payload)",
        "payload": ('"Dorit Fischer · Partner, NAI Shames Makovsky · Foreword"',
                    '"Dorit Fischer wrote the foreword. She’s a Partner at NAI Shames Makovsky."'),
    },
    # ---- 16. Joe Fielden Jr ----------------------------------------------
    {
        "label": "#16 Joe Fielden attribution (visible)",
        "html": ('>Joe Fielden Jr., President, Neyland Apartment Associates LLC<',
                 '>Joe Fielden Jr. · President, Neyland Apartment Associates · 4,000+ unit operator<'),
    },
    {
        "label": "#16 Joe Fielden attribution (payload)",
        "payload": ('"Joe Fielden Jr., President, Neyland Apartment Associates LLC"',
                    '"Joe Fielden Jr. · President, Neyland Apartment Associates · 4,000+ unit operator"'),
    },
    # ---- 16. Kevin Choquette ---------------------------------------------
    {
        "label": "#16 Kevin Choquette attribution (visible)",
        "html": ('>Kevin Choquette, Founder, Fident Capital<',
                 '>Kevin Choquette · Founder, Fident Capital · CRE Capital Markets<'),
    },
    {
        "label": "#16 Kevin Choquette attribution (payload)",
        "payload": ('"Kevin Choquette, Founder, Fident Capital"',
                    '"Kevin Choquette · Founder, Fident Capital · CRE Capital Markets"'),
    },
    # ---- A6. Footer tagline (book) ---------------------------------------
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
    # ---- 35 site-wide: Read More CTA on role grid (if present on book) ---
    {
        "label": "#35 role-card CTA (visible) — book page",
        "html": ('<span class="role-card__cta">Read More<!-- --> →</span>',
                 '<span class="role-card__cta">See Your Role<!-- --> →</span>'),
        "html_count": 4,
        "optional": True,
    },
    {
        "label": "#35 role-card CTA (payload) — book page",
        "payload": ('"className":"role-card__cta","children":["Read More"," →"]',
                    '"className":"role-card__cta","children":["See Your Role"," →"]'),
        "payload_count": 4,
        "optional": True,
    },
    # ---- Audiobook (listen) strip + Flight hydration -----------------------
    {
        "label": "Audiobook retailer section (visible)",
        "html": (
            '<a href="https://www.porchlightbooks.com/products/peak-property-performance-bill-douglas-9781639081288" target="_blank" rel="noopener" class="retailer-link">Bulk at Porchlight</a></div></div></div></div></section><section class="publisher-band publisher-band--dark dark-section">',
            '<a href="https://www.porchlightbooks.com/products/peak-property-performance-bill-douglas-9781639081288" target="_blank" rel="noopener" class="retailer-link">Bulk at Porchlight</a></div></div></div></div></section><section class="retailer-section"><div class="container"><div class="retailer-section__inner"><div class="book-cover-image"><img src="../public/images/book-cover-with-bestseller.png" alt="Peak Property Performance® — audiobook from Fast Company Press."/></div><div><span class="eyebrow">Listen to the Book</span><h2 class="mt-4 mb-4">Available on leading audiobook platforms.</h2><p class="lede">Stream or download wherever you listen.</p><div class="retailer-list" id="audiobook-retailers"><a href="https://www.audible.com/pd/Peak-Property-Performance-Audiobook/B0FLYMCKMT" target="_blank" rel="noopener" class="retailer-link">Audible</a><a href="https://play.google.com/store/audiobooks/details/Peak_Property_Performance_Game_Changing_AI_and_Dig?id=AQAAAEDKViUW_M&amp;hl=en_US" target="_blank" rel="noopener" class="retailer-link">Google Play Audiobooks</a><a href="https://open.spotify.com/show/5R1dHz7Hdk8WO2X9VNGIfy" target="_blank" rel="noopener" class="retailer-link">Spotify</a></div></div></div></div></section><section class="publisher-band publisher-band--dark dark-section">',
        ),
    },
    {
        "label": "Flight: insert $L14 between print retailers and publisher band",
        "payload": (
            '\\"$L12\\",\\"$L13\\",[\\"$\\",\\"section\\",\\"69efb8125996bea084142e3a\\",{\\"className\\":\\"card',
            '\\"$L12\\",\\"$L14\\",\\"$L13\\",[\\"$\\",\\"section\\",\\"69efb8125996bea084142e3a\\",{\\"className\\":\\"card',
        ),
        "payload_raw": True,
    },
    {
        "label": "Flight: hero Listen to the book CTA",
        "payload": (
            ',[\\"$\\",\\"a\\",null,{\\"href\\":\\"#retailers\\",\\"className\\":\\"btn btn-secondary btn-lg\\",\\"children\\":\\"All Retailers\\"}],\\"\\"]',
            ',[\\"$\\",\\"a\\",null,{\\"href\\":\\"#retailers\\",\\"className\\":\\"btn btn-secondary btn-lg\\",\\"children\\":\\"All Retailers\\"}],[\\"$\\",\\"a\\",null,{\\"href\\":\\"#audiobook-retailers\\",\\"className\\":\\"btn btn-secondary btn-lg\\",\\"children\\":\\"Listen to the book\\"}],\\"\\"]',
        ),
        "payload_raw": True,
    },
    {
        "label": "Flight: audiobook retailer-section chunk + footer push split",
        "payload": (
            r'Bulk at Porchlight\"}]]}]]}]]}]}]}]\n"])</script><script>self.__next_f.push([1,"6:[\"$\",\"footer\",null,{\"className\":',
            r'Bulk at Porchlight\"}]]}]]}]]}]}]}]\n"])</script><script>self.__next_f.push([1,"14:[\"$\",\"section\",\"69efb8125996bea084142e35\",{\"className\":\"retailer-section\",\"children\":[\"$\",\"div\",null,{\"className\":\"container\",\"children\":[\"$\",\"div\",null,{\"className\":\"retailer-section__inner\",\"children\":[[\"$\",\"div\",null,{\"className\":\"book-cover-image\",\"children\":[\"$\",\"img\",null,{\"src\":\"/public/images/book-cover-with-bestseller.png\",\"alt\":\"Peak Property Performance® — audiobook from Fast Company Press.\"}]}],[\"$\",\"div\",null,{\"children\":[[\"$\",\"span\",null,{\"className\":\"eyebrow\",\"children\":\"Listen to the Book\"}],[\"$\",\"h2\",null,{\"className\":\"mt-4 mb-4\",\"children\":\"Available on leading audiobook platforms.\"}],[\"$\",\"p\",null,{\"className\":\"lede\",\"children\":\"Stream or download wherever you listen.\"}],[\"$\",\"div\",null,{\"className\":\"retailer-list\",\"id\":\"audiobook-retailers\",\"children\":[[\"$\",\"a\",\"audible\",{\"href\":\"https://www.audible.com/pd/Peak-Property-Performance-Audiobook/B0FLYMCKMT\",\"target\":\"_blank\",\"rel\":\"noopener\",\"className\":\"retailer-link\",\"children\":\"Audible\"}],[\"$\",\"a\",\"googlePlayAudiobooks\",{\"href\":\"https://play.google.com/store/audiobooks/details/Peak_Property_Performance_Game_Changing_AI_and_Dig?id=AQAAAEDKViUW_M\u0026hl=en_US\",\"target\":\"_blank\",\"rel\":\"noopener\",\"className\":\"retailer-link\",\"children\":\"Google Play Audiobooks\"}],[\"$\",\"a\",\"spotify\",{\"href\":\"https://open.spotify.com/show/5R1dHz7Hdk8WO2X9VNGIfy\",\"target\":\"_blank\",\"rel\":\"noopener\",\"className\":\"retailer-link\",\"children\":\"Spotify\"}]]}]]}]]}]}]}]}]\n"])</script><script>self.__next_f.push([1,"6:[\"$\",\"footer\",null,{\"className\":',
        ),
        "payload_raw": True,
    },
    # ---- A8 + 36 + 38. Head additions: Book schema, OG, favicon, css -----
    {
        "label": "head additions (book)",
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
            '<meta property="og:title" content="Peak Property Performance® — the Book"/>'
            '<meta property="og:description" content="Amazon Best Seller. Game-Changing AI and Digital Strategies for Commercial Real Estate. By Bill Douglas and Drew Hall."/>'
            '<meta property="og:type" content="book"/>'
            '<meta property="og:url" content="https://peakpropertyperformance.com/book"/>'
            '<meta property="og:image" content="https://peakpropertyperformance.com/public/images/og-image.png"/>'
            '<meta property="og:image:width" content="1200"/>'
            '<meta property="og:image:height" content="630"/>'
            '<meta name="twitter:card" content="summary_large_image"/>'
            '<meta name="twitter:image" content="https://peakpropertyperformance.com/public/images/og-image.png"/>'
            '<script type="application/ld+json">{"@context":"https://schema.org","@type":"Book","name":"Peak Property Performance","alternateName":"Peak Property Performance: Game-Changing AI and Digital Strategies for Commercial Real Estate","isbn":"978-1-63908-128-8","bookFormat":"Hardcover","author":[{"@type":"Person","name":"Bill Douglas"},{"@type":"Person","name":"Drew Hall"}],"contributor":[{"@type":"Person","name":"Ryan R. Goble"}],"publisher":{"@type":"Organization","name":"Fast Company Press"},"image":"https://peakpropertyperformance.com/api/media/file/cover.png","description":"Amazon Best Seller. Game-Changing AI and Digital Strategies for Commercial Real Estate.","award":"Amazon Best Seller","offers":[{"@type":"Offer","url":"https://www.amazon.com/Peak-Property-Performance-Game-Changing-Strategies/dp/1639081283/","seller":{"@type":"Organization","name":"Amazon"}},{"@type":"Offer","url":"https://www.barnesandnoble.com/w/peak-property-performance-bill-douglas/1147029132?ean=9781639081288","seller":{"@type":"Organization","name":"Barnes & Noble"}}]}</script>',
        ),
    },
]
