#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build /glossary/index.html from the canonical PPP term list.

Source of truth: PPP_Resources_Content_Deliverables_v3.md (Deliverable 2).
Run from repo root:  python3 scripts/build/build-glossary.py

This regenerates glossary/index.html in full. Edit GLOSSARY below to change
content, then re-run. The visible HTML and the DefinedTermSet JSON-LD are
generated from the same source so they never drift.
"""

import html
import json
import re
from pathlib import Path

OUT = Path("glossary/index.html")

# Each entry: (display_term, plain_term_for_schema, definition_html, plain_definition_for_schema)
# Plain forms strip cross-reference markup so JSON-LD stays clean.
# Order: numerals first, then alphabetical (case-insensitive).

GLOSSARY = [
    (
        "5C™ Framework",
        "5C Framework",
        'The five strategic plays that take property data from fragmented to compounding: <strong><a href="#term-clarify">Clarify</a></strong>, <strong><a href="#term-connect">Connect</a></strong>, <strong><a href="#term-collect">Collect</a></strong>, <strong><a href="#term-coordinate">Coordinate</a></strong>, <strong><a href="#term-control">Control</a></strong>. The framework is sequential — Clarify before Connect, Collect before Coordinate, and so on — because each stage depends on the foundation built by the one before. The 5C™ Framework is a trademark of OpticWise and is the strategic backbone of <em>Peak Property Performance®</em>. <span class="glossary-seealso">See also: <a href="#term-champion">Champion</a>.</span>',
        "The five strategic plays that take property data from fragmented to compounding: Clarify, Connect, Collect, Coordinate, Control. The framework is sequential — each stage depends on the foundation built by the one before. The 5C Framework is a trademark of OpticWise and the strategic backbone of Peak Property Performance.",
    ),
    (
        "5S® UX",
        "5S UX",
        'The user experience standard every OpticWise deployment is measured against: <strong>Seamless Mobility · Security · Stability (resilience) · Speed · Service.</strong> Non-negotiable. Privacy is a separate canonical stance — never as part of 5S®. The 5S® UX is what the tenant experiences. Behind it is <strong><a href="#term-sic">SIC®</a></strong> (the engineering discipline) and <strong><a href="#term-bot">BoT®</a></strong> (the consolidated connectivity foundation). <span class="glossary-seealso">5S® is a registered trademark of OpticWise.</span>',
        "The user experience standard every OpticWise deployment is measured against: Seamless Mobility, Security, Stability (resilience), Speed, Service. Non-negotiable. Privacy is a separate canonical stance, never part of 5S. 5S UX is what the tenant experiences; behind it is SIC (the engineering discipline) and BoT (the consolidated connectivity foundation).",
    ),
    (
        "AI readiness",
        "AI readiness",
        'The state in which a portfolio\u2019s data and digital infrastructure has been governed, normalized, and access-controlled to the point that any decision engine, large language model, or autonomous system can act on it under owner permissions. AI readiness is the outcome of running the <strong><a href="#term-5c-framework">5C™ Framework</a></strong> end-to-end. It is not achieved by buying AI products. It is achieved by building the foundation those products require.',
        "The state in which a portfolio's data and digital infrastructure has been governed, normalized, and access-controlled to the point that any decision engine, LLM, or autonomous system can act on it under owner permissions. AI readiness is the outcome of running the 5C Framework end-to-end. Not achieved by buying AI products; achieved by building the foundation those products require.",
    ),
    (
        "Backplane",
        "Backplane",
        'The owner-controlled network design that runs underneath every system in a building or portfolio. A single backplane, repeated property-to-property, is the precondition for portfolio-level intelligence. Without it, every building solves its own problems and the portfolio never compounds. <span class="glossary-seealso">See also: <a href="#term-connect">Connect</a>, <a href="#term-bot">BoT®</a>, <a href="#term-owner-controlled">Owner-controlled</a>.</span>',
        "The owner-controlled network design that runs underneath every system in a building or portfolio. A single backplane, repeated property-to-property, is the precondition for portfolio-level intelligence.",
    ),
    (
        "Big Three Plays",
        "Big Three Plays",
        'The three operational levers that produce the most reliable NOI uplift for CRE owners when run against an owner-controlled data plane: <strong>utilities, insurance, and occupancy</strong>. The Big Three Plays Diagnostic is the OpticWise first-call sales tool that surfaces the accountability-to-visibility gap in one conversation. Realistic compounded effect: $500–$600 per door per year (multifamily) or $0.60–$0.90 per RSF per year (multi-tenant office) — see <strong><a href="#term-locked-noi-benchmarks">Locked NOI Benchmarks</a></strong>.',
        "The three operational levers that produce the most reliable NOI uplift for CRE owners when run against an owner-controlled data plane: utilities, insurance, and occupancy. Realistic compounded effect: $500–$600 per door per year (multifamily) or $0.60–$0.90 per RSF per year (multi-tenant office).",
    ),
    (
        "BoT® (Building of Things®)",
        "BoT (Building of Things)",
        'OpticWise\u2019s owner-controlled approach to data and digital infrastructure that consolidates and governs building connectivity so every device or system can run on a single, secure, segmented foundation. BoT® is engineered to <strong><a href="#term-sic">SIC®</a></strong> standards and delivers <strong><a href="#term-5s-ux">5S® UX</a></strong>. Often saves hundreds of thousands of dollars in build costs and several thousand dollars per month in operating costs. <span class="glossary-seealso">See also: <a href="#term-layer-1">Layer 1</a>.</span>',
        "OpticWise's owner-controlled approach to data and digital infrastructure that consolidates and governs building connectivity so every device or system can run on a single, secure, segmented foundation. Engineered to SIC standards and delivers 5S UX.",
    ),
    (
        "Champion",
        "Champion",
        "The outcome state of running the <strong><a href=\"#term-5c-framework\">5C™ Framework</a></strong> across a portfolio: intelligence that compounds across buildings rather than living inside any single one. Champion isn\u2019t a one-time achievement — it\u2019s a steady-state where standardization, governance, and owner control produce results that improve year over year without proportional increases in staffing or vendor spend. The book\u2019s eighth chapter is named for it.",
        "The outcome state of running the 5C Framework across a portfolio: intelligence that compounds across buildings rather than living inside any single one. A steady-state where standardization, governance, and owner control produce results that improve year over year without proportional increases in staffing or vendor spend.",
    ),
    (
        "Clarify",
        "Clarify",
        'The first play in the <strong><a href="#term-5c-framework">5C™ Framework</a></strong>. Defining success metrics, mapping data and credential ownership, identifying operational and financial leakage, and documenting what\u2019s trustworthy and portable. Clarify is the diagnostic pass that produces the artifact every later play builds on. Most owners skip it. The ones who don\u2019t, win. <span class="glossary-seealso">In OpticWise engagements, Clarify maps to the <a href="#term-ppp-review">PPP Review / PPP Audit™</a>.</span>',
        "The first play in the 5C Framework. Defining success metrics, mapping data and credential ownership, identifying operational and financial leakage, and documenting what's trustworthy and portable. The diagnostic pass that produces the artifact every later play builds on.",
    ),
    (
        "Collect",
        "Collect",
        'The third play in the <strong><a href="#term-5c-framework">5C™ Framework</a></strong>. Capturing and normalizing high-fidelity, usable data into a consistent, reusable model across the portfolio. Collect is what turns raw vendor data into something an analyst, executive, or AI system can act on without bespoke per-building translation. <span class="glossary-seealso">In OpticWise engagements, Collect lives in <a href="#term-layer-1">Layer 1 — Managed Data &amp; Digital Infrastructure</a>.</span>',
        "The third play in the 5C Framework. Capturing and normalizing high-fidelity, usable data into a consistent, reusable model across the portfolio. Turns raw vendor data into something an analyst, executive, or AI system can act on without bespoke per-building translation.",
    ),
    (
        "Connect",
        "Connect",
        'The second play in the <strong><a href="#term-5c-framework">5C™ Framework</a></strong>. Establishing secure, owner-controlled connectivity that repeats property-to-property. Connect is the network and infrastructure layer — the <strong><a href="#term-backplane">backplane</a></strong> that every later play depends on. The hardest play to retrofit, which is why it follows Clarify and precedes Collect. <span class="glossary-seealso">In OpticWise engagements, Connect maps to <a href="#term-bot">BoT®</a> delivered under <a href="#term-sic">SIC®</a> standards.</span>',
        "The second play in the 5C Framework. Establishing secure, owner-controlled connectivity that repeats property-to-property. The network and infrastructure layer — the backplane that every later play depends on.",
    ),
    (
        "Control",
        "Control",
        'The fifth and final play in the <strong><a href="#term-5c-framework">5C™ Framework</a></strong>. Enabling any decision engine, workflow, or large language model to act on owner data under owner-defined permissions. Control is where <strong><a href="#term-ai-readiness">AI readiness</a></strong> becomes operational. Without it, AI deployments either fail, leak data, or operate outside the owner\u2019s risk tolerance. <span class="glossary-seealso">In OpticWise engagements, Control lives in <a href="#term-portfolio-brain">Portfolio Brain™</a> built on <a href="#term-property-brain">Property Brain™</a>.</span>',
        "The fifth and final play in the 5C Framework. Enabling any decision engine, workflow, or LLM to act on owner data under owner-defined permissions. Where AI readiness becomes operational.",
    ),
    (
        "Coordinate",
        "Coordinate",
        'The fourth play in the <strong><a href="#term-5c-framework">5C™ Framework</a></strong>. Governing identity, access, privacy, lineage, retention, and rules of use across every system and every vendor. Coordinate is the legal, policy, and operational layer that lets owners enforce data sovereignty without becoming a bottleneck. <span class="glossary-seealso">In OpticWise engagements, Coordinate lives in <a href="#term-property-brain">Property Brain™</a> and <a href="#term-portfolio-brain">Portfolio Brain™</a>.</span>',
        "The fourth play in the 5C Framework. Governing identity, access, privacy, lineage, retention, and rules of use across every system and every vendor. The legal, policy, and operational layer that lets owners enforce data sovereignty without becoming a bottleneck.",
    ),
    (
        "Data and digital infrastructure",
        "Data and digital infrastructure",
        "The combined layer of networks, sensors, systems, software, and data flows that runs a commercial building. The phrase is deliberate — \u201cinfrastructure\u201d alone refers to physical building systems (HVAC, plumbing, structural). \u201cData and digital infrastructure\u201d names the layer that\u2019s been growing inside CRE for two decades without ever being treated as an asset class. The central thesis of <em>Peak Property Performance®</em> is that this layer is now the determining factor in NOI, AI readiness, and asset valuation.",
        "The combined layer of networks, sensors, systems, software, and data flows that runs a commercial building. Distinct from physical infrastructure (HVAC, plumbing, structural). The central thesis of Peak Property Performance is that this layer is now the determining factor in NOI, AI readiness, and asset valuation.",
    ),
    (
        "Data ownership",
        "Data ownership",
        'The legal and operational state in which all data generated by or about a property is owned by the property owner, not the vendor platforms that happen to collect it. Data ownership is contractual (clauses in vendor agreements), operational (admin credentials, export rights), and technical (formats and systems that allow portability). <span class="glossary-seealso">See also: <a href="#term-vendor-lock-in">Vendor lock-in</a>, <a href="#term-owner-controlled">Owner-controlled</a>.</span>',
        "The legal and operational state in which all data generated by or about a property is owned by the property owner, not the vendor platforms that happen to collect it. Contractual, operational, and technical.",
    ),
    (
        "Data plane",
        "Data plane",
        'The unified, governed layer where all property and portfolio data is captured, normalized, and stored under owner control. The data plane sits inside <strong><a href="#term-layer-2">Layer 2</a></strong> as part of <strong><a href="#term-property-brain">Property Brain™</a></strong> → <strong><a href="#term-portfolio-brain">Portfolio Brain™</a></strong>. Without a unified data plane, AI deployments fragment, vendor systems can\u2019t be compared, and portfolio intelligence stalls.',
        "The unified, governed layer where all property and portfolio data is captured, normalized, and stored under owner control. Sits inside Layer 2 as part of Property Brain to Portfolio Brain.",
    ),
    (
        "Decision Stack Session",
        "Decision Stack Session",
        'An OpticWise engagement format that maps a single property\u2019s operational decisions — who\u2019s accountable, what data exists, where the leakage is, and what plays would close the gap. The Decision Stack Session is one of two paths into an OpticWise relationship (the other being a <strong><a href="#term-ppp-review">PPP Review / PPP Audit™</a></strong>).',
        "An OpticWise engagement format that maps a single property's operational decisions: who's accountable, what data exists, where the leakage is, and what plays would close the gap. One of two paths into an OpticWise relationship.",
    ),
    (
        "Diligence Discount Thesis",
        "Diligence Discount Thesis",
        'The canonical OpticWise thesis that when a property trades, recoverable NOI the seller wasn\u2019t capturing becomes a price negotiation lever for the buyer. <em>Price = NOI × cap rate.</em> Owning your data and digital infrastructure isn\u2019t only an operating story — it\u2019s a diligence story. <span class="glossary-seealso">See also: <a href="#term-diligence-premium">Diligence premium</a>.</span>',
        "When a property trades, recoverable NOI the seller wasn't capturing becomes a price negotiation lever for the buyer. Price = NOI × cap rate. Owning your data and digital infrastructure isn't only an operating story; it's a diligence story.",
    ),
    (
        "Diligence premium",
        "Diligence premium",
        'The increase in transaction value, insurance favorability, and operational risk profile that a property or portfolio earns by being able to produce verifiable operational data on demand. A property with documented data and digital infrastructure governance commands better terms in acquisition, refinancing, insurance underwriting, and exit. The diligence premium is one of the highest-leverage financial outcomes of running the <strong><a href="#term-5c-framework">5C™ Framework</a></strong>. <span class="glossary-seealso">See also: <a href="#term-diligence-discount-thesis">Diligence Discount Thesis</a>.</span>',
        "The increase in transaction value, insurance favorability, and operational risk profile that a property or portfolio earns by being able to produce verifiable operational data on demand. Better terms in acquisition, refinancing, insurance underwriting, and exit.",
    ),
    (
        "ElasticISP®",
        "ElasticISP",
        "OpticWise\u2019s ISP-agnostic connectivity model. The data and digital infrastructure runs on whichever circuits make sense for the property — diverse providers, diverse paths, redundancy by design — without locking the owner into a single carrier or a bulk revenue-share contract. Typically involves dual-circuit redundancy at the <strong><a href=\"#term-mpoe\">MPOE</a></strong>, with the ability to swap or add providers without rewiring the building. <span class=\"glossary-seealso\">ElasticISP® is a registered trademark of OpticWise.</span>",
        "OpticWise's ISP-agnostic connectivity model. Diverse providers, diverse paths, redundancy by design — without locking the owner into a single carrier or bulk revenue-share contract.",
    ),
    (
        "Foundation",
        "Foundation",
        "In PPP terminology, the data and digital infrastructure layer that underlies every other operating decision at a property. The book\u2019s first conviction is that <em>foundations precede intelligence</em> — AI, automation, and optimization investments only produce returns if the foundation has been built and governed. Foundation is also the operational answer to \u201cwhere do we start?\u201d — Clarify the foundation, then Connect, then everything else.",
        "The data and digital infrastructure layer that underlies every other operating decision at a property. Foundations precede intelligence — AI, automation, and optimization investments only produce returns if the foundation has been built and governed.",
    ),
    (
        "Layer 1 — Managed Data &amp; Digital Infrastructure",
        "Layer 1 — Managed Data & Digital Infrastructure",
        'The owner-controlled foundation in the OpticWise two-layer model. Layer 1 covers design, implementation, and operations of the data and digital infrastructure across CRE facilities and portfolios. Engineered under <strong><a href="#term-sic">SIC®</a></strong> standards. Repeatable property-to-property. Governance baked in. Performance held high without burdening on-site engineers or property managers. <span class="glossary-seealso">See also: <a href="#term-bot">BoT®</a>, <a href="#term-elasticisp">ElasticISP®</a>, <a href="#term-5s-ux">5S® UX</a>.</span>',
        "The owner-controlled foundation in the OpticWise two-layer model. Design, implementation, and operations of the data and digital infrastructure across CRE facilities and portfolios. Engineered under SIC standards. Repeatable property-to-property. Governance baked in.",
    ),
    (
        "Layer 2 — Owner-Controlled Intelligence Layer",
        "Layer 2 — Owner-Controlled Intelligence Layer",
        'The intelligence layer in the OpticWise two-layer model. Layer 2 is <strong><a href="#term-property-brain">Property Brain™</a></strong> → <strong><a href="#term-portfolio-brain">Portfolio Brain™</a></strong> — a vendor-agnostic and LLM-agnostic data plane + trust plane that lets any decision engine, any vendor platform, any LLM act under owner permissions. Standardize once at one property; intelligence compounds across the portfolio.',
        "The intelligence layer in the OpticWise two-layer model. Property Brain to Portfolio Brain — a vendor-agnostic and LLM-agnostic data plane plus trust plane that lets any decision engine act under owner permissions.",
    ),
    (
        "Locked NOI Benchmarks",
        "Locked NOI Benchmarks",
        'The canonical, conservative NOI uplift figures OpticWise publishes for what owners can realistically expect from running the <strong><a href="#term-big-three-plays">Big Three Plays</a></strong> on an owner-controlled data plane:<ul><li><strong>Multifamily:</strong> $500–$600 per door per year</li><li><strong>Multi-tenant office:</strong> $0.60–$0.90 per RSF per year</li></ul>These are ranges, not point estimates. The realized number for any specific property depends on asset profile, occupancy posture, and how much of the Big Three Plays the owner can actually action.',
        "Conservative NOI uplift figures from running the Big Three Plays on an owner-controlled data plane: multifamily $500–$600 per door per year, multi-tenant office $0.60–$0.90 per RSF per year. Ranges, not point estimates.",
    ),
    (
        "Mandatory Discovery Questions",
        "Mandatory Discovery Questions",
        "The OpticWise canonical set of questions for any first-call qualification conversation with a CRE owner or asset manager: (1) what outcomes are you accountable for, (2) where do you have the least control, (3) is there a third-party PM and what\u2019s non-negotiable for them, (4) when do low-voltage/OT decisions lock and who owns integration accountability, (5) what asset types dominate the next 12–24 months, (6) if you had monthly plays — not dashboards — what three decisions would you improve?",
        "OpticWise's canonical first-call qualification questions for a CRE owner or asset manager. Six questions covering accountability, control gaps, PM relationships, OT decision timing, asset mix, and the three decisions monthly plays would improve.",
    ),
    (
        "MPOE (Minimum Point of Entry)",
        "MPOE (Minimum Point of Entry)",
        'The physical location where carrier services enter a building. The MPOE is where <strong><a href="#term-elasticisp">ElasticISP®</a></strong> terminates ISP circuits and where the owner-vs-carrier ownership question becomes concrete. If the carrier owns the equipment in your MPOE, they own the network in your building. If you own it, you own it.',
        "The physical location where carrier services enter a building. Where ElasticISP terminates ISP circuits and where owner-vs-carrier ownership becomes concrete.",
    ),
    (
        "NOI growth (in the PPP context)",
        "NOI growth (in the PPP context)",
        'Net Operating Income growth driven specifically by data and digital infrastructure decisions, as distinct from rent increases, occupancy improvements, or capital expenditure efficiencies. PPP\u2019s argument is that there is a fourth NOI lever most owners have left untouched: the operational efficiency, energy management, tenant experience, and vendor cost gains made possible by owner-controlled infrastructure and well-governed data. <span class="glossary-seealso">See also: <a href="#term-locked-noi-benchmarks">Locked NOI Benchmarks</a>, <a href="#term-big-three-plays">Big Three Plays</a>.</span>',
        "Net Operating Income growth driven specifically by data and digital infrastructure decisions — distinct from rent increases, occupancy improvements, or CapEx efficiencies. A fourth NOI lever most owners have left untouched.",
    ),
    (
        "Operator",
        "Operator",
        "In PPP terminology, anyone responsible for running CRE properties at the operational level — owners, asset managers, property managers, IT leaders, and the executives accountable for their performance. The book is written for operators, not consultants. The phrase \u201coperator voice\u201d describes the difference between writing about CRE technology and writing from inside it.",
        "Anyone responsible for running CRE properties at the operational level — owners, asset managers, property managers, IT leaders, and the executives accountable for their performance. The book is written for operators, not consultants.",
    ),
    (
        "OT (Operational Technology)",
        "OT (Operational Technology)",
        "The technology that runs the physical operations of a building — BMS (building management systems), access control, elevators, video surveillance, parking systems, energy management. OT is distinct from IT (information technology), which runs the tenants\u2019 computing environment. The book\u2019s argument is that most CRE owners have given OT to vendors by default while keeping IT in-house. Owner-controlled OT is the precondition for everything else in the playbook.",
        "The technology that runs the physical operations of a building — BMS, access control, elevators, surveillance, parking, energy management. Distinct from IT, which runs tenants' computing. Owner-controlled OT is the precondition for everything else in the playbook.",
    ),
    (
        "Owner-controlled",
        "Owner-controlled",
        'The defining adjective of the PPP playbook. An owner-controlled system, network, contract, or data layer is one where the property owner — not the vendor, not the consultant, not the platform — holds the credentials, the rights, and the ability to act. The opposite of owner-controlled is <strong>vendor-controlled</strong> or <strong><a href="#term-vendor-lock-in">vendor-locked</a></strong>. Most CRE technology is the latter by default; the playbook is about making it the former by design.',
        "The defining adjective of the PPP playbook. A system, network, contract, or data layer where the property owner holds the credentials, the rights, and the ability to act. The opposite is vendor-controlled or vendor-locked.",
    ),
    (
        "Peak Property Performance®",
        "Peak Property Performance",
        "The book. The podcast. The playbook. Published by Fast Company Press in 2026. Amazon Best Seller. Co-authored by Bill Douglas (CEO, OpticWise) and Drew Hall, with Ryan R. Goble. Forewords by Dorit Fischer (NAI Shames Makovsky) and Zain Jaffer (Blue Field Capital / Zain Ventures Family Office). The brand under which the 5C™ Framework is taught to the broader CRE community.",
        "The book, the podcast, and the playbook. Published by Fast Company Press in 2026. Amazon Best Seller. Co-authored by Bill Douglas and Drew Hall, with Ryan R. Goble. Forewords by Dorit Fischer and Zain Jaffer. The brand under which the 5C Framework is taught to the broader CRE community.",
    ),
    (
        "Plays",
        "Plays",
        'The unit of action in the PPP playbook. A play is a specific, executable move — not a strategy, not a philosophy, not a recommendation. The <strong><a href="#term-5c-framework">5C™ Framework</a></strong> is five plays. The \u201cMonday morning\u201d framing refers to plays you can actually run on Monday — not initiatives, not roadmaps, not transformations.',
        "The unit of action in the PPP playbook. A specific, executable move — not a strategy, not a philosophy, not a recommendation. The 5C Framework is five plays. The 'Monday morning' framing refers to plays you can actually run on Monday.",
    ),
    (
        "Portfolio Brain™",
        "Portfolio Brain",
        'The portfolio-level outcome of standardizing <strong><a href="#term-property-brain">Property Brain™</a></strong> across multiple properties. Intelligence compounds across the portfolio instead of restarting at every address. The vendor- and LLM-agnostic data plane and trust plane that allows any decision engine to act across the entire portfolio under owner permissions. <span class="glossary-seealso">Portfolio Brain™ is a trademark of OpticWise.</span>',
        "The portfolio-level outcome of standardizing Property Brain across multiple properties. Intelligence compounds across the portfolio instead of restarting at every address.",
    ),
    (
        "Portfolio compounding",
        "Portfolio compounding",
        "The outcome of running the <strong><a href=\"#term-5c-framework\">5C™ Framework</a></strong> across multiple properties rather than one. Single-building improvements are linear; each one solved separately. Portfolio compounding is geometric — the standardization, normalized data, and governance from one building become assets that improve every other building added to the system. <strong><a href=\"#term-champion\">Champion</a></strong> is the steady-state of portfolio compounding.",
        "The outcome of running the 5C Framework across multiple properties rather than one. Single-building improvements are linear; portfolio compounding is geometric — standardization, normalized data, and governance from one building become assets that improve every other building.",
    ),
    (
        "PPP Audit™ / PPP Review",
        "PPP Audit / PPP Review",
        'The complimentary entry-point engagement OpticWise offers to CRE owners. One building, one working session, clear deliverables. Surfaces ownership, leakage, and the practical path to control. Maps directly to <strong><a href="#term-clarify">Clarify</a></strong> in the <strong><a href="#term-5c-framework">5C™ Framework</a></strong>. Deliverables include a Property Data Map, a Control Gap Analysis, and a prioritized Roadmap. Typically 45–90 minutes of live time with the owner\u2019s team, plus analysis and deliverable prep.',
        "The complimentary entry-point engagement OpticWise offers to CRE owners. One building, one working session, clear deliverables. Maps directly to Clarify in the 5C Framework. Deliverables: Property Data Map, Control Gap Analysis, prioritized Roadmap. Typically 45–90 minutes live with the owner's team plus analysis prep.",
    ),
    (
        "Property Brain™",
        "Property Brain",
        'A vendor- and LLM-agnostic Property Intelligence Layer — a governed data plane + trust plane that makes each property capable of autonomous activities and intelligence. Property Brain™ is the per-property layer of the OpticWise two-layer model. Standardize it once at one property and <strong>Property Brain™ becomes <a href="#term-portfolio-brain">Portfolio Brain™</a></strong>. <span class="glossary-seealso">Property Brain™ is a trademark of OpticWise.</span>',
        "A vendor- and LLM-agnostic Property Intelligence Layer — a governed data plane plus trust plane that makes each property capable of autonomous activities and intelligence. Standardize once at one property and Property Brain becomes Portfolio Brain.",
    ),
    (
        "Property Intelligence → Portfolio Intelligence",
        "Property Intelligence to Portfolio Intelligence",
        "The OpticWise tagline and core operating arc. Property Intelligence is what you have when one building runs the playbook well. Portfolio Intelligence is what you have when that same standard is replicated across every building in your portfolio. The arc is the entire reason the OpticWise two-layer model exists — to turn what works at one building into something that works across all of them, with the data and digital infrastructure as the compounding asset.",
        "The OpticWise tagline and core operating arc. Property Intelligence is what you have when one building runs the playbook well. Portfolio Intelligence is what you have when that same standard is replicated across every building in your portfolio.",
    ),
    (
        "Right Butt, Wrong Seat",
        "Right Butt, Wrong Seat",
        'A canonical OpticWise framework — borrowed from baseball and football — describing the common CRE pattern where the wrong role is making the technology decisions. The Property Manager (PM) runs day-to-day building operations; picking the technology stack requires a different skill set and a different timeframe. When the PM is the decision-maker on tech, outcomes optimize for the PM\u2019s day rather than the asset manager\u2019s hold period. The \u201cright butt\u201d is the asset manager or owner accountable for NOI growth, debt service, refinancing terms, and exit math. The \u201cwrong seat\u201d is the PM chair when used for strategic technology decisions. <span class="glossary-seealso">See also: <a href="#term-skybox-principle">Skybox Principle</a>.</span>',
        "A canonical OpticWise framework — borrowed from baseball and football — describing the CRE pattern where the wrong role is making the technology decisions. The 'right butt' is the asset manager or owner accountable for NOI growth, debt service, refinancing, and exit. The 'wrong seat' is the PM chair when used for strategic technology decisions.",
    ),
    (
        "SIC® (Security, Infrastructure, and Connectivity)",
        "SIC (Security, Infrastructure, and Connectivity)",
        'OpticWise\u2019s core network design philosophy and the engineering discipline behind <strong><a href="#term-layer-1">Layer 1</a></strong>. Governs how every property is designed, deployed, hardened, monitored, and operated so the data and digital infrastructure performs as an owner-controlled asset, not a vendor-controlled liability. SIC® is <strong>owner-controlled, vendor-agnostic, ISP-agnostic, first-tier equipment only, resilient by design.</strong> <span class="glossary-seealso">SIC® is a registered trademark of OpticWise.</span>',
        "OpticWise's core network design philosophy and the engineering discipline behind Layer 1. Owner-controlled, vendor-agnostic, ISP-agnostic, first-tier equipment only, resilient by design.",
    ),
    (
        "Skybox Principle",
        "Skybox Principle",
        'The OpticWise framing of the owner/asset manager perspective: they should be leading from the skybox, not the field. Owners and asset managers are accountable for capital allocation, hold-period economics, and exit math — not for day-to-day building operations. The Skybox Principle is the reason <strong><a href="#term-right-butt-wrong-seat">Right Butt, Wrong Seat</a></strong> matters: the skybox view of asset performance over hold periods is fundamentally different from the field-level view of any given Tuesday\u2019s tickets and operations.',
        "The OpticWise framing of the owner/asset manager perspective: leading from the skybox, not the field. Owners and asset managers are accountable for capital allocation, hold-period economics, and exit math — not day-to-day building operations.",
    ),
    (
        "Trust plane",
        "Trust plane",
        "The governance layer in <strong><a href=\"#term-property-brain\">Property Brain™</a></strong> and <strong><a href=\"#term-portfolio-brain\">Portfolio Brain™</a></strong> that determines who and what can act on the data plane, under what permissions, with what audit trail. The trust plane is what makes <strong><a href=\"#term-layer-2\">Layer 2</a></strong> vendor- and LLM-agnostic — any decision engine can be plugged in, but every action passes through governance the owner controls.",
        "The governance layer in Property Brain and Portfolio Brain that determines who and what can act on the data plane, under what permissions, with what audit trail. What makes Layer 2 vendor- and LLM-agnostic.",
    ),
    (
        "Vendor-agnostic",
        "Vendor-agnostic",
        "A system, design, or contract structured so that vendors are interchangeable — not because the owner doesn\u2019t have preferences, but because the architecture doesn\u2019t depend on any single vendor\u2019s platform, schema, or pricing. Vendor-agnostic is a design choice. Most CRE technology becomes vendor-locked by accident; vendor-agnostic happens on purpose.",
        "A system, design, or contract structured so that vendors are interchangeable. Architecture doesn't depend on any single vendor's platform, schema, or pricing. A design choice — most CRE technology becomes vendor-locked by accident; vendor-agnostic happens on purpose.",
    ),
    (
        "Vendor lock-in",
        "Vendor lock-in",
        'The condition in which a CRE owner cannot reasonably switch vendors without significant operational disruption, contractual penalty, or data loss. Vendor lock-in is the single largest hidden tax on CRE portfolios — paid in unfavorable renewal terms, in slow innovation adoption, and in lost negotiating leverage. The opposite of vendor lock-in is <strong><a href="#term-owner-controlled">owner-controlled</a></strong> infrastructure. Breaking lock-in is the first and most important step in claiming the strategic value of data and digital infrastructure.',
        "The condition in which a CRE owner cannot reasonably switch vendors without significant operational disruption, contractual penalty, or data loss. The single largest hidden tax on CRE portfolios — paid in unfavorable renewal terms, in slow innovation adoption, and in lost negotiating leverage.",
    ),
]


def slugify(term: str) -> str:
    s = term.lower()
    # strip trademark/registered marks
    for ch in ("™", "®", "©"):
        s = s.replace(ch, "")
    # ascii substitutions
    s = s.replace("→", "to").replace("—", "-").replace("–", "-").replace("&amp;", "and")
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"\s+", "-", s.strip())
    s = re.sub(r"-+", "-", s)
    return s


NAV = (
    '<nav class="nav"><div class="container nav__inner">'
    '<a class="nav__brand" href="../index.html"><span class="nav__brandmark">PPP</span>Peak Property Performance®</a>'
    '<div class="nav__links">'
    '<a class="nav__link" href="../book/index.html">Book</a>'
    '<a class="nav__link" href="../podcast/index.html">Podcast</a>'
    '<a class="nav__link" href="../5c-framework/index.html">5C™ Framework</a>'
    '<a class="nav__link" href="../about/index.html">About</a>'
    '<div class="nav__dropdown"><span class="nav__link nav__dropdown-trigger" role="button" tabindex="0" aria-haspopup="true">By Role</span>'
    '<div class="nav__dropdown-menu">'
    '<a class="nav__link" href="../for-owners/index.html">For Owners</a>'
    '<a class="nav__link" href="../for-asset-managers/index.html">For Asset Managers</a>'
    '<a class="nav__link" href="../for-property-managers/index.html">For Property Managers</a>'
    '<a class="nav__link" href="../for-it-managers/index.html">For IT Managers</a>'
    "</div></div>"
    '<a class="nav__link" href="../resources/index.html">Resources</a>'
    '<a class="btn btn-primary btn-sm" href="../book/index.html">Get the Book</a>'
    "</div></div></nav>"
)

FOOTER = (
    '<footer class="footer"><div class="container">'
    '<div class="footer__grid">'
    '<div><a class="footer__brand" href="../index.html"><span class="nav__brandmark">PPP</span>Peak Property Performance®</a>'
    '<p class="footer__tagline">Amazon Best Seller. The CRE strategy playbook for owners, operators, and the leaders building the future of the industry.</p></div>'
    '<div><div class="footer__col-heading">Read &amp; Listen</div>'
    '<a class="footer__link" href="../book/index.html">The PPP Book</a>'
    '<a class="footer__link" href="../podcast/index.html">The PPP Podcast</a>'
    '<a class="footer__link" href="../be-on-the-show/index.html">Be on the Show</a></div>'
    '<div><div class="footer__col-heading">By Role</div>'
    '<a class="footer__link" href="../for-owners/index.html">For CRE Owners</a>'
    '<a class="footer__link" href="../for-asset-managers/index.html">For Asset Managers</a>'
    '<a class="footer__link" href="../for-it-managers/index.html">For IT Managers</a>'
    '<a class="footer__link" href="../for-property-managers/index.html">For Property Managers</a></div>'
    '<div><div class="footer__col-heading">Get Started</div>'
    '<a class="footer__link" href="../5c-framework/index.html">5C™ Framework</a>'
    '<a class="footer__link" href="../resources/index.html">Free Resources</a>'
    '<a class="footer__link" href="../ppp-review/index.html">Request a PPP Review</a>'
    '<a class="footer__link" href="../about/index.html">About</a></div>'
    "</div>"
    '<div class="footer__publisher"><img src="../api/media/file/fast-company-press.webp" alt="Fast Company Press"/>'
    '<div class="footer__publisher-text"><strong>Published by Fast Company Press</strong>'
    "<span>An imprint dedicated to ideas that move business forward.</span></div></div>"
    '<div class="footer__bottom">'
    "<span>© 2026 Peak Property Performance®. All rights reserved.</span>"
    '<span>A program of <a href="https://opticwise.com/" target="_blank" rel="noopener" style="color:rgba(245,240,228,0.7)">OpticWise</a></span>'
    "</div></div></footer>"
)


def build_jsonld() -> str:
    """DefinedTermSet JSON-LD with one DefinedTerm per glossary entry."""
    has = []
    for term, plain_term, _, plain_def in GLOSSARY:
        slug = slugify(term)
        has.append(
            {
                "@type": "DefinedTerm",
                "@id": f"https://peakpropertyperformance.com/glossary#term-{slug}",
                "name": plain_term,
                "description": plain_def,
                "inDefinedTermSet": "https://peakpropertyperformance.com/glossary",
                "url": f"https://peakpropertyperformance.com/glossary#term-{slug}",
            }
        )
    payload = {
        "@context": "https://schema.org",
        "@type": "DefinedTermSet",
        "@id": "https://peakpropertyperformance.com/glossary",
        "name": "The PPP Playbook Glossary",
        "description": "Glossary of terms used across the Peak Property Performance® book, podcast, and OpticWise engagements.",
        "url": "https://peakpropertyperformance.com/glossary",
        "publisher": {"@type": "Organization", "name": "OpticWise", "url": "https://opticwise.com"},
        "hasDefinedTerm": has,
    }
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def build_entries_html() -> str:
    parts = []
    for term, _, definition_html, _ in GLOSSARY:
        slug = slugify(term)
        parts.append(
            f'<div class="glossary-entry" id="term-{slug}">'
            f'<dt class="glossary-term">{term}</dt>'
            f'<dd class="glossary-def">{definition_html}</dd>'
            f"</div>"
        )
    return "<dl class=\"glossary-list\">" + "".join(parts) + "</dl>"


def build_toc_html() -> str:
    items = []
    for term, _, _, _ in GLOSSARY:
        slug = slugify(term)
        items.append(f'<a class="glossary-toc__link" href="#term-{slug}">{term}</a>')
    return '<nav class="glossary-toc" aria-label="Glossary index">' + "".join(items) + "</nav>"


HEAD = (
    '<!DOCTYPE html><html lang="en"><head>'
    '<meta charSet="utf-8"/>'
    '<meta name="viewport" content="width=device-width, initial-scale=1"/>'
    '<title>The PPP Playbook Glossary | Peak Property Performance®</title>'
    '<meta name="description" content="The PPP Playbook Glossary — every term that runs the playbook, defined in plain language for executive conversations. From Peak Property Performance®, the Amazon Best Seller."/>'
    '<meta property="og:title" content="The PPP Playbook Glossary — Peak Property Performance®"/>'
    '<meta property="og:description" content="Every term in the playbook — 5C™, BoT®, SIC®, 5S® UX, Property Brain™, Champion — defined in plain language for executive conversations."/>'
    '<meta property="og:type" content="website"/>'
    '<meta property="og:url" content="https://peakpropertyperformance.com/glossary"/>'
    '<meta property="og:image" content="https://peakpropertyperformance.com/public/images/og-image.png"/>'
    '<meta property="og:image:width" content="1200"/>'
    '<meta property="og:image:height" content="630"/>'
    '<meta name="twitter:card" content="summary_large_image"/>'
    '<meta name="twitter:image" content="https://peakpropertyperformance.com/public/images/og-image.png"/>'
    '<link rel="stylesheet" href="../_next/static/css/f3145fbd800cc712.css" data-precedence="next"/>'
    '<link rel="stylesheet" href="../public/css/ppp-additions.css"/>'
    '<link rel="stylesheet" href="https://use.typekit.net/REPLACE_WITH_KIT_ID.css"/>'
    '<link rel="icon" type="image/x-icon" href="../public/favicon.ico"/>'
    '<link rel="icon" type="image/png" sizes="32x32" href="../public/favicon-32x32.png"/>'
    '<link rel="icon" type="image/png" sizes="16x16" href="../public/favicon-16x16.png"/>'
    '<link rel="apple-touch-icon" sizes="180x180" href="../public/apple-touch-icon.png"/>'
    '<link rel="manifest" href="../public/site.webmanifest"/>'
    '<meta name="theme-color" content="#1B3526"/>'
)

JSONLD_TAG = '<script type="application/ld+json">{}</script>'.format(build_jsonld())


def build_page() -> str:
    body = (
        '<body>'
        + NAV
        + '<main>'
        + '<section class="hero hero--paper"><div class="container">'
        + '<span class="eyebrow">The PPP Playbook Glossary</span>'
        + '<h1 class="hero__heading mt-4">Every term that runs the playbook.</h1>'
        + '<p class="hero__lede mt-3">Defined in plain language for executive conversations. From <em>Peak Property Performance®</em> — Amazon Best Seller, Fast Company Press.</p>'
        + '</div></section>'
        + '<section class="glossary-section"><div class="container">'
        + '<p class="glossary-intro">These are the terms used across the book, the podcast, and OpticWise engagements. Each definition is written for owners, asset managers, and executives — not engineers. If you can read an entry once and use the term correctly in a board meeting, the entry has done its job. <strong>Bold terms</strong> have their own entries elsewhere in the glossary. <em>Italic terms</em> are referenced but not defined separately.</p>'
        + build_toc_html()
        + build_entries_html()
        + '</div></section>'
        + '<section class="cta-section cta-section--paper"><div class="container">'
        + '<span class="eyebrow no-rule" style="justify-content:center;display:flex">Apply the glossary</span>'
        + '<h2 class="mt-4 mb-4">Apply the glossary.</h2>'
        + '<p class="lede" style="max-width:60ch;margin-inline:auto">Run a complimentary PPP Review on one of your buildings. We&#x27;ll walk through it with you and identify where each of these terms applies — and where the gaps are.</p>'
        + '<div class="cta__buttons"><a class="btn btn-primary btn-lg" href="../ppp-review/index.html">Request a PPP Review</a></div>'
        + '</div></section>'
        + '</main>'
        + FOOTER
        + '</body></html>'
    )
    return HEAD + JSONLD_TAG + "</head>" + body


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(build_page(), encoding="utf-8")
    print(f"Wrote {OUT} — {len(GLOSSARY)} terms")


if __name__ == "__main__":
    main()
