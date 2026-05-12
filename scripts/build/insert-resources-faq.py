#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Insert the /resources FAQ section (16 Q&As + FAQPage JSON-LD) into
resources/index.html.

Source: PPP_Resources_Content_Deliverables_v3.md, Deliverable 3.

Inserts:
  1. Visible HTML <section class="faq-section faq-section--paper">…
     immediately before the "cta-section cta-section--paper" (Beyond the
     Book) closing section.
  2. Same FAQ rendered into the React Flight payload as a $L-style
     section so React hydration doesn't strip it on first paint.
  3. FAQPage JSON-LD <script type="application/ld+json"> appended to <head>.

Idempotent: if any of the three insertions already exists (detected by a
sentinel marker), this script skips that part. Re-run after FAQ content
edits and the existing block is replaced atomically.
"""

import json
import re
import sys
from pathlib import Path

FILE = Path("resources/index.html")
SENTINEL_HTML = '<section class="faq-section faq-section--paper"'
SENTINEL_PAYLOAD = '\\"className\\":\\"faq-section faq-section--paper\\"'
SENTINEL_JSONLD_NAME = '"PPP /resources FAQ"'

FAQS = [
    # category label, question, answer (plain text — minimal HTML allowed in answer_html)
    {
        "cat": "About the book and podcast",
        "q": "What is Peak Property Performance®, exactly?",
        "a_text": "Peak Property Performance® is a 2026 Amazon Best Seller published by Fast Company Press, co-authored by Bill Douglas (CEO, OpticWise) and Drew Hall, with Ryan R. Goble. It's the CRE strategy playbook for data and digital infrastructure — written for owners, asset managers, and operators who want NOI growth, AI readiness, and control without vendor lock-in. The book introduces the 5C™ Framework (Clarify · Connect · Collect · Coordinate · Control) and is the foundation of the Peak Property Performance® Podcast.",
        "a_html": '<em>Peak Property Performance®</em> is a 2026 <strong>Amazon Best Seller</strong> published by Fast Company Press, co-authored by Bill Douglas (CEO, OpticWise) and Drew Hall, with Ryan R. Goble. It\u2019s the CRE strategy playbook for data and digital infrastructure — written for owners, asset managers, and operators who want NOI growth, AI readiness, and control without vendor lock-in. The book introduces the <strong>5C™ Framework</strong> (Clarify · Connect · Collect · Coordinate · Control) and is the foundation of the Peak Property Performance® Podcast.',
    },
    {
        "cat": "About the book and podcast",
        "q": "How is Peak Property Performance® different from other CRE tech books?",
        "a_text": "Most CRE technology books are written by consultants for executives who want strategy decks. Peak Property Performance® is written by operators for operators — people who actually run CRE properties and have spent decades doing it. The book skips the strategy abstractions and delivers plays you can run on Monday morning. It's also explicitly not a PropTech book; the thesis is that PropTech is the application layer, and the book is about the data and digital infrastructure that PropTech runs on.",
        "a_html": 'Most CRE technology books are written by consultants for executives who want strategy decks. <em>Peak Property Performance®</em> is written by operators for operators — people who actually run CRE properties and have spent decades doing it. The book skips the strategy abstractions and delivers plays you can run on Monday morning. It\u2019s also explicitly <em>not</em> a PropTech book; the thesis is that PropTech is the application layer, and the book is about the data and digital infrastructure that PropTech runs on.',
    },
    {
        "cat": "About the book and podcast",
        "q": "Do I need to read the book to listen to the podcast (or vice versa)?",
        "a_text": "No. The book is the playbook. The podcast is the weekly conversations — with CRE owners, operators, and industry leaders — that bring the playbook to life. They complement each other but each stands alone. Many listeners discover the podcast first and pick up the book once a specific episode lands; many readers pick up the podcast to stay current after finishing the book.",
        "a_html": 'No. The book is the playbook. The podcast is the weekly conversations — with CRE owners, operators, and industry leaders — that bring the playbook to life. They complement each other but each stands alone. Many listeners discover the podcast first and pick up the book once a specific episode lands; many readers pick up the podcast to stay current after finishing the book.',
    },
    {
        "cat": "About the process",
        "q": "What's the first step if I want to apply the playbook to my buildings?",
        "a_text": "A complimentary PPP Review (also called a PPP Audit™). One building, one working session, clear deliverables, no sales pitch. You'll come out of it with a Property Data Map, a Control Gap Analysis, and a prioritized Roadmap. It typically takes 45–90 minutes of live time with your team, plus our analysis and deliverable prep. It's how we both decide if there's a fit before anyone commits to anything larger.",
        "a_html": 'A complimentary <a href="../ppp-review/index.html"><strong>PPP Review</strong></a> (also called a PPP Audit™). One building, one working session, clear deliverables, no sales pitch. You\u2019ll come out of it with a Property Data Map, a Control Gap Analysis, and a prioritized Roadmap. It typically takes 45–90 minutes of live time with your team, plus our analysis and deliverable prep. It\u2019s how we both decide if there\u2019s a fit before anyone commits to anything larger.',
    },
    {
        "cat": "About the process",
        "q": "Do I need to switch vendors to apply the playbook?",
        "a_text": "No. The 5C™ Framework is vendor-agnostic and LLM-agnostic by design. You keep vendors who perform, replace vendors who don't, and swap both in the future without rewiring the building. The point of owner-controlled data and digital infrastructure is to make the owner the one choosing — not to dictate which vendors win or lose.",
        "a_html": 'No. The <strong>5C™ Framework</strong> is vendor-agnostic and LLM-agnostic by design. You keep vendors who perform, replace vendors who don\u2019t, and swap both in the future without rewiring the building. The point of owner-controlled data and digital infrastructure is to make the <em>owner</em> the one choosing — not to dictate which vendors win or lose.',
    },
    {
        "cat": "About the process",
        "q": "Will this disrupt our current operations?",
        "a_text": "No rip-and-replace. The Clarify step (the first C in the 5C™ Framework) happens alongside normal operations. Implementation is phased around turnover, CapEx timing, and lease-up milestones. Most retrofit deployments — when an owner chooses to act on the Clarify findings — complete in less than one quarter per building. New-construction deployments stay synchronized with the GC schedule.",
        "a_html": 'No rip-and-replace. The Clarify step (the first C in the 5C™ Framework) happens alongside normal operations. Implementation is phased around turnover, CapEx timing, and lease-up milestones. Most retrofit deployments — when an owner chooses to act on the Clarify findings — complete in less than one quarter per building. New-construction deployments stay synchronized with the GC schedule.',
    },
    {
        "cat": "About the process",
        "q": "What if my property manager already handles tech decisions?",
        "a_text": "This is the most common pattern in CRE — and it's the \"Right Butt, Wrong Seat\" problem described in the book. Property management and digital infrastructure are different positions. The PM runs day-to-day building operations. Picking the technology stack — network architecture, data plane, integration design, governance rules — requires a different skill set and a different timeframe. The decisions should sit with whoever owns NOI growth, debt service, refinancing terms, and exit math. That's the asset manager or owner, leading from the skybox, not the field.",
        "a_html": 'This is the most common pattern in CRE — and it\u2019s the <strong><a href="../glossary/index.html#term-right-butt-wrong-seat">&ldquo;Right Butt, Wrong Seat&rdquo;</a></strong> problem described in the book. Property management and digital infrastructure are different positions. The PM runs day-to-day building operations. Picking the technology stack — network architecture, data plane, integration design, governance rules — requires a different skill set and a different timeframe. The decisions should sit with whoever owns NOI growth, debt service, refinancing terms, and exit math. That\u2019s the asset manager or owner, leading from the <strong><a href="../glossary/index.html#term-skybox-principle">skybox</a></strong>, not the field.',
    },
    {
        "cat": "About the value",
        "q": "What kind of NOI uplift can I expect?",
        "a_text": "The Locked NOI Benchmarks from the OpticWise Wins & Nightmares Library are conservative and verifiable: Multifamily $500–$600 per door per year. Multi-tenant office $0.60–$0.90 per RSF per year. These are ranges, not point estimates. Specific projects can run higher — one case in the library is a 299-unit Class A multifamily that delivered $694/door blended NOI, driving roughly $4.88M in asset-value lift at a market cap rate. The realized number for any specific property depends on asset profile, occupancy posture, and how much of the Big Three Plays (utilities, insurance, occupancy) the owner can actually action.",
        "a_html": 'The <strong><a href="../glossary/index.html#term-locked-noi-benchmarks">Locked NOI Benchmarks</a></strong> from the OpticWise Wins &amp; Nightmares Library are conservative and verifiable:<ul><li><strong>Multifamily:</strong> $500–$600 per door per year</li><li><strong>Multi-tenant office:</strong> $0.60–$0.90 per RSF per year</li></ul>These are ranges, not point estimates. Specific projects can run higher — one case in the library is a 299-unit Class A multifamily that delivered $694/door blended NOI, driving roughly $4.88M in asset-value lift at a market cap rate. The realized number for any specific property depends on asset profile, occupancy posture, and how much of the <strong><a href="../glossary/index.html#term-big-three-plays">Big Three Plays</a></strong> (utilities, insurance, occupancy) the owner can actually action.',
    },
    {
        "cat": "About the value",
        "q": "How does this affect my exit math?",
        "a_text": "This is the Diligence Discount Thesis. When a property trades, recoverable NOI the seller wasn't capturing becomes a price negotiation lever for the buyer. Price = NOI × cap rate. If you've been operating with owner-controlled data and digital infrastructure for years, you walk into diligence with a portable, well-documented operating story that commands a diligence premium. If you've been operating with vendor-controlled infrastructure, you walk in with gaps the buyer's diligence team can price against you. The book treats this as one of the highest-leverage financial outcomes of running the playbook.",
        "a_html": 'This is the <strong><a href="../glossary/index.html#term-diligence-discount-thesis">Diligence Discount Thesis</a></strong>. When a property trades, recoverable NOI the seller wasn\u2019t capturing becomes a price negotiation lever for the buyer. <em>Price = NOI × cap rate.</em> If you\u2019ve been operating with owner-controlled data and digital infrastructure for years, you walk into diligence with a portable, well-documented operating story that commands a <strong><a href="../glossary/index.html#term-diligence-premium">diligence premium</a></strong>. If you\u2019ve been operating with vendor-controlled infrastructure, you walk in with gaps the buyer\u2019s diligence team can price against you. The book treats this as one of the highest-leverage financial outcomes of running the playbook.',
    },
    {
        "cat": "About the value",
        "q": "Will this slow down or accelerate my AI strategy?",
        "a_text": "Accelerate. AI readiness starts with governance, not with AI. Per the 2025/2026 Dealpath report 'The State of AI Readiness in Commercial Real Estate,' 98% of institutional CRE investors say improving their firm's data infrastructure is a top priority over the next 12–24 months. AI in CRE doesn't fail at the model — it fails at the data foundation. The 5C™ Framework builds the foundation any decision engine, large language model, or autonomous system can act on under owner permissions. When you swap AI models in six months, your data, your workflows, your governance, and your portfolio intelligence stay intact.",
        "a_html": 'Accelerate. <strong>AI readiness starts with governance, not with AI.</strong> Per the 2025/2026 Dealpath report <em>The State of AI Readiness in Commercial Real Estate</em>, 98% of institutional CRE investors say improving their firm\u2019s data infrastructure is a top priority over the next 12–24 months. AI in CRE doesn\u2019t fail at the model — it fails at the data foundation. The 5C™ Framework builds the foundation any decision engine, large language model, or autonomous system can act on under owner permissions. When you swap AI models in six months, your data, your workflows, your governance, and your portfolio intelligence stay intact.',
    },
    {
        "cat": "Benchmarks & Proof",
        "q": "What does NOI uplift look like on a real multifamily property?",
        "a_text": "A 299-unit Class A multifamily property delivered $694 per door of blended NOI — $624 per door on the income stack and $70 per door on the expense stack — translating to roughly $4.88 million in asset-value lift at a market cap rate. This is on the higher end of what's possible; the conservative range OpticWise publishes is $500–$600 per door per year. The realized number depends on asset profile, occupancy posture, and how much of the Big Three Plays (utilities, insurance, occupancy) the owner can actually action.",
        "a_html": 'A 299-unit Class A multifamily property delivered <strong>$694 per door</strong> of blended NOI — $624 per door on the income stack and $70 per door on the expense stack — translating to roughly <strong>$4.88 million in asset-value lift</strong> at a market cap rate. This is on the higher end of what\u2019s possible; the conservative range OpticWise publishes is <strong>$500–$600 per door per year</strong>. The realized number depends on asset profile, occupancy posture, and how much of the <strong><a href="../glossary/index.html#term-big-three-plays">Big Three Plays</a></strong> (utilities, insurance, occupancy) the owner can actually action.',
    },
    {
        "cat": "Benchmarks & Proof",
        "q": "What does NOI uplift look like on a real Class A office property?",
        "a_text": "A 450,000 RSF Class A office property delivered $0.62 per rentable square foot in NOI uplift on the income stack alone. The conservative range OpticWise publishes for multi-tenant office is $0.60–$0.90 per RSF per year. Same caveats apply: profile, occupancy, and the owner's ability to action the underlying plays drive where the specific property lands in the range.",
        "a_html": 'A 450,000 RSF Class A office property delivered <strong>$0.62 per rentable square foot</strong> in NOI uplift on the income stack alone. The conservative range OpticWise publishes for multi-tenant office is <strong>$0.60–$0.90 per RSF per year</strong>. Same caveats apply: profile, occupancy, and the owner\u2019s ability to action the underlying plays drive where the specific property lands in the range.',
    },
    {
        "cat": "Benchmarks & Proof",
        "q": "Can owner-controlled infrastructure protect capital outside the NOI stack?",
        "a_text": "Yes — and this is one of the underappreciated outcomes. At a 300,000 SF mixed-use property, power-quality monitoring on the owner's network caught out-of-spec voltage spikes hammering the rooftop HVAC units. The owner filed a utility claim with the documented data; the utility paid for a feeder-circuit and transformer rebuild; the rooftop units got an extra three to four years of useful life. Approximately $250,000 of premature replacement CapEx avoided. Same network, different lever. The point: owner-controlled data and digital infrastructure shows up on the balance sheet in ways the income statement doesn't capture.",
        "a_html": 'Yes — and this is one of the underappreciated outcomes. At a 300,000 SF mixed-use property, power-quality monitoring on the owner\u2019s network caught out-of-spec voltage spikes hammering the rooftop HVAC units. The owner filed a utility claim with the documented data; the utility paid for a feeder-circuit and transformer rebuild; the rooftop units got an extra three to four years of useful life. <strong>Approximately $250,000 of premature replacement CapEx avoided.</strong> Same network, different lever. The point: owner-controlled data and digital infrastructure shows up on the balance sheet in ways the income statement doesn\u2019t capture.',
    },
    {
        "cat": "Benchmarks & Proof",
        "q": "What's a single-property utility-savings example?",
        "a_text": "A Class A multi-tenant office property delivered $70,000 in annual utility savings — with simultaneous occupancy increase. Same property, same year. The two outcomes don't have to compete; they're produced by the same underlying capability (owner-controlled data, governed access, normalized operational reporting), applied to different decisions.",
        "a_html": 'A Class A multi-tenant office property delivered <strong>$70,000 in annual utility savings</strong> — with simultaneous occupancy increase. Same property, same year. The two outcomes don\u2019t have to compete; they\u2019re produced by the same underlying capability (owner-controlled data, governed access, normalized operational reporting), applied to different decisions.',
    },
    {
        "cat": "About the resources",
        "q": "Are these resources the same as the book?",
        "a_text": "The resources on this page draw from the book, but they're not excerpts. The book is the full playbook — case studies, implementation patterns, and chapter-by-chapter depth. The resources are the tools you'd want at your desk while running it: the 5C™ Quick-Start Worksheet as a self-assessment, the Vendor Contract Audit as a shareable tool, the PPP Glossary as a reference for executive conversations.",
        "a_html": 'The resources on this page draw from the book, but they\u2019re not excerpts. The book is the full playbook — case studies, implementation patterns, and chapter-by-chapter depth. The resources are the tools you\u2019d want at your desk while running it: the <strong>5C™ Quick-Start Worksheet</strong> as a self-assessment, the <strong><a href="../vendor-contract-audit/index.html">Vendor Contract Audit</a></strong> as a shareable tool, the <strong><a href="../glossary/index.html">PPP Glossary</a></strong> as a reference for executive conversations.',
    },
    {
        "cat": "About the resources",
        "q": "What's the difference between a PPP Review and these resources?",
        "a_text": "The resources are self-service. A PPP Review is a complimentary 45-minute walkthrough of one of your buildings by an OpticWise operator — Bill Douglas or a member of the team — with a written one-pager delivered within five business days. The resources help you do the diagnostic yourself. A PPP Review gets you a second set of eyes from people who've done this across hundreds of properties.",
        "a_html": 'The resources are self-service. A <strong><a href="../ppp-review/index.html">PPP Review</a></strong> is a complimentary 45-minute walkthrough of one of your buildings by an OpticWise operator — Bill Douglas or a member of the team — with a written one-pager delivered within five business days. The resources help you do the diagnostic yourself. A PPP Review gets you a second set of eyes from people who\u2019ve done this across hundreds of properties.',
    },
]

# Group questions into ordered subsections
SUBSECTIONS = [
    "About the book and podcast",
    "About the process",
    "About the value",
    "Benchmarks & Proof",
    "About the resources",
]


def build_visible_html() -> str:
    """Render the FAQ as a <section> using native <details>/<summary>."""
    parts = [
        '<section class="faq-section faq-section--paper"><div class="container">',
        '<span class="eyebrow">Questions about the resources, the book, and the process</span>',
        '<h2 class="mt-4 mb-4">What CRE owners ask before running this.</h2>',
        '<p class="lede" style="max-width:60ch">Direct answers for owners evaluating the playbook. If yours isn&#x27;t here, <a href="../ppp-review/index.html">request a complimentary PPP Review</a> and ask it directly.</p>',
        '<div class="faq-list">',
    ]
    for sub in SUBSECTIONS:
        items = [f for f in FAQS if f["cat"] == sub]
        parts.append(f'<div class="faq-subsection"><h3 class="faq-subsection__heading">{sub}</h3>')
        for f in items:
            parts.append(
                '<details class="faq-item">'
                f'<summary class="faq-item__q">{f["q"]}</summary>'
                f'<div class="faq-item__a">{f["a_html"]}</div>'
                '</details>'
            )
        parts.append('</div>')
    parts.append('</div></div></section>')
    return "".join(parts)


def js_escape_for_payload(s: str) -> str:
    """Escape a literal string for embedding inside a JS double-quoted string
    that already lives inside an HTML attribute. The outer file embeds the
    Flight payload as a JS string with backslash-escaped quotes, so every
    " in our content becomes \\" in the file. Backslash itself becomes \\\\.
    """
    s = s.replace("\\", "\\\\")
    s = s.replace('"', '\\"')
    return s


def build_payload_html() -> str:
    """Render the FAQ as a React Flight payload-style nested array. Each
    element is [\"$\",\"tag\",key,{props}]. Strings escape via js_escape_for_payload.
    """
    def el(tag, key, props_dict, children=None):
        # props minus children, then children appended
        parts = []
        for k, v in props_dict.items():
            if isinstance(v, str):
                parts.append(f'"{js_escape_for_payload(k)}":"{js_escape_for_payload(v)}"')
            else:
                parts.append(f'"{js_escape_for_payload(k)}":{json.dumps(v, ensure_ascii=False)}')
        if children is not None:
            parts.append(f'"children":{children}')
        props = "{" + ",".join(parts) + "}"
        key_part = "null" if key is None else f'"{js_escape_for_payload(key)}"'
        return f'["$","{tag}",{key_part},{props}]'

    def text(s):
        return f'"{js_escape_for_payload(s)}"'

    # Build each FAQ item as a details element. The answer HTML contains
    # arbitrary nested tags, so we use dangerouslySetInnerHTML. This is safe
    # because the source is our own static content.
    def faq_item_payload(faq, idx):
        # children = [summary, div]
        summary_el = el("summary", None, {"className": "faq-item__q"}, children=text(faq["q"]))
        # Use dangerouslySetInnerHTML for the answer to preserve inline HTML
        a_inner_html = faq["a_html"]
        a_div = (
            '["$","div",null,{"className":"faq-item__a","dangerouslySetInnerHTML":{"__html":"'
            + js_escape_for_payload(a_inner_html)
            + '"}}]'
        )
        return el("details", str(idx), {"className": "faq-item"}, children=f"[{summary_el},{a_div}]")

    subsection_payloads = []
    for sub_idx, sub in enumerate(SUBSECTIONS):
        heading_el = el("h3", None, {"className": "faq-subsection__heading"}, children=text(sub))
        items = [f for f in FAQS if f["cat"] == sub]
        item_payloads = [faq_item_payload(item, j) for j, item in enumerate(items)]
        sub_div = el(
            "div",
            str(sub_idx),
            {"className": "faq-subsection"},
            children="[" + heading_el + "," + ",".join(item_payloads) + "]",
        )
        subsection_payloads.append(sub_div)

    lede = (
        '["$","p",null,{"className":"lede","style":{"maxWidth":"60ch"},"children":['
        + text("Direct answers for owners evaluating the playbook. If yours isn\u2019t here, ")
        + ','
        + '["$","a",null,{"href":"/ppp-review","children":"request a complimentary PPP Review"}]'
        + ','
        + text(" and ask it directly.")
        + ']}]'
    )
    eyebrow_el = el(
        "span",
        None,
        {"className": "eyebrow"},
        children=text("Questions about the resources, the book, and the process"),
    )
    h2_el = el(
        "h2",
        None,
        {"className": "mt-4 mb-4"},
        children=text("What CRE owners ask before running this."),
    )
    list_div = el(
        "div",
        None,
        {"className": "faq-list"},
        children="[" + ",".join(subsection_payloads) + "]",
    )
    container = el(
        "div",
        None,
        {"className": "container"},
        children="[" + eyebrow_el + "," + h2_el + "," + lede + "," + list_div + "]",
    )
    section = el(
        "section",
        "69efb8195996bea084142eF1",
        {"className": "faq-section faq-section--paper"},
        children=container,
    )
    return section


def build_jsonld() -> str:
    main_entity = []
    for f in FAQS:
        main_entity.append(
            {
                "@type": "Question",
                "name": f["q"],
                "acceptedAnswer": {"@type": "Answer", "text": f["a_text"]},
            }
        )
    payload = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "name": "PPP /resources FAQ",
        "url": "https://peakpropertyperformance.com/resources",
        "mainEntity": main_entity,
    }
    return '<script type="application/ld+json">' + json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + '</script>'


def main():
    if not FILE.exists():
        sys.exit(f"missing: {FILE}")
    content = FILE.read_text(encoding="utf-8")

    # 1) Insert visible HTML (or replace existing)
    visible_html = build_visible_html()
    if SENTINEL_HTML in content:
        # replace existing FAQ section
        # find the section span and replace it
        start = content.find(SENTINEL_HTML)
        # back up to the opening <section
        sec_open = content.rfind("<section", 0, start + 1)
        sec_close_marker = '</section>'
        # find the matching close — naive: assume our generated section has no nested <section>
        sec_close = content.find(sec_close_marker, sec_open) + len(sec_close_marker)
        content = content[:sec_open] + visible_html + content[sec_close:]
        print("visible: replaced existing FAQ section")
    else:
        # insert immediately before the closing cta-section (Beyond the Book)
        anchor = '<section class="cta-section cta-section--paper">'
        idx = content.find(anchor)
        if idx == -1:
            sys.exit("could not find anchor for visible FAQ insert")
        content = content[:idx] + visible_html + content[idx:]
        print("visible: inserted FAQ section before Beyond-the-Book cta-section")

    # 2) Insert payload section (or replace existing)
    payload_section = build_payload_html()
    if SENTINEL_PAYLOAD in content:
        # replace existing payload section
        start = content.find(SENTINEL_PAYLOAD)
        # back up to the opening [\"$\",\"section\"
        sec_open = content.rfind('[\\"$\\",\\"section\\"', 0, start)
        # depth-counting forward to find matching close
        depth = 0
        i = sec_open
        while i < len(content):
            ch = content[i]
            if ch == "[":
                depth += 1
            elif ch == "]":
                depth -= 1
                if depth == 0:
                    break
            i += 1
        sec_close = i + 1
        # The payload form on disk has actual backslashes — but our generator
        # produces forms WITHOUT extra escaping (since they live in a JS string
        # literal in the file). Wait — re-check: the payload in the file
        # is INSIDE a JS double-quoted string, so " is rendered as \" and the
        # file shows that as backslash-quote. We need to apply that extra
        # escape pass when writing into the file.
        # Our generator produces strings like ["$","section",... which when
        # placed inside the JS string-literal context become \"$\",\"section\"
        # automatically because the surrounding context is a JS literal.
        # Actually — no. The HTML *file content* shows literal backslash-quote
        # pairs because that's what the source file looks like. So to inject
        # into the file we need to backslash-escape every quote in our
        # generator output.
        injected = payload_section.replace("\\", "\\\\").replace('"', '\\"')
        content = content[:sec_open] + injected + content[sec_close:]
        print("payload: replaced existing FAQ section")
    else:
        # find anchor in payload: "$L12" reference, comma-separated.
        # Insert FAQ section between "$L12" and the cta-section that follows.
        # The pattern is: ,"$L12",[\"$\",\"section\",\"69efb8195996bea084142e60\",
        anchor = ',\\"$L12\\",[\\"$\\",\\"section\\",\\"69efb8195996bea084142e60\\"'
        if anchor not in content:
            # Try alternate anchor — sometimes Flight uses different identifiers
            alt = ',\\"$L12\\",['
            if alt not in content:
                sys.exit("could not find payload anchor for FAQ insert")
            idx = content.find(alt) + len(',\\"$L12\\",')
        else:
            idx = content.find(anchor) + len(',\\"$L12\\",')
        # Apply the JS-literal escape: every \ → \\, every " → \"
        injected = payload_section.replace("\\", "\\\\").replace('"', '\\"')
        # Insert FAQ section followed by comma — so we end up with
        # ,"$L12",<FAQ_section>,[cta-section...
        content = content[:idx] + injected + "," + content[idx:]
        print("payload: inserted FAQ section after $L12 publisher-band reference")

    # 3) Insert FAQPage JSON-LD (or replace existing)
    jsonld_tag = build_jsonld()
    if SENTINEL_JSONLD_NAME in content:
        # replace existing FAQPage json-ld
        start = content.find('<script type="application/ld+json">')
        # find the one containing our sentinel
        while start != -1:
            end = content.find("</script>", start) + len("</script>")
            block = content[start:end]
            if SENTINEL_JSONLD_NAME in block:
                content = content[:start] + jsonld_tag + content[end:]
                print("json-ld: replaced existing FAQPage block")
                break
            start = content.find('<script type="application/ld+json">', end)
    else:
        # insert right before </head>
        idx = content.find("</head>")
        if idx == -1:
            sys.exit("missing </head> in resources/index.html")
        content = content[:idx] + jsonld_tag + content[idx:]
        print("json-ld: inserted FAQPage block at end of <head>")

    FILE.write_text(content, encoding="utf-8")
    print(f"wrote {FILE} ({len(content)} bytes)")


if __name__ == "__main__":
    main()
