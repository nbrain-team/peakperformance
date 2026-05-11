# -*- coding: utf-8 -*-
"""Retrofit /index.html — replace the badge-overlay-on-cover pattern with the
single composite Best Seller marketing image (book + badge + FC Press lockup)."""

FILE = "index.html"

EDITS = [
    {
        "label": "retrofit composite (visible) — hero + retailer",
        "html": (
            '<div class="book-cover-image book-cover-with-badge"><img src="./api/media/file/cover.png" alt="Peak Property Performance® — book cover"/><img src="./public/images/amazon-best-seller-400.png" alt="Amazon Best Seller" class="best-seller-badge"/></div>',
            '<div class="book-cover-image"><img src="./public/images/book-cover-with-bestseller.png" alt="Peak Property Performance® — Amazon Best Seller — book cover from Fast Company Press."/></div>',
        ),
        "html_count": 2,
    },
    {
        "label": "retrofit composite (payload) — hero + retailer",
        "payload": (
            '["$","div",null,{"className":"book-cover-image book-cover-with-badge","children":[["$","img",null,{"src":"https://www.peakpropertyperformance.com/api/media/file/cover.png","alt":"Peak Property Performance® — book cover"}],["$","img",null,{"src":"/public/images/amazon-best-seller-400.png","alt":"Amazon Best Seller","className":"best-seller-badge"}]]}]',
            '["$","div",null,{"className":"book-cover-image","children":["$","img",null,{"src":"/public/images/book-cover-with-bestseller.png","alt":"Peak Property Performance® — Amazon Best Seller — book cover from Fast Company Press."}]}]',
        ),
        "payload_count": 2,
    },
]
