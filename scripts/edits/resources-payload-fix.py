# -*- coding: utf-8 -*-
"""Add Free Downloads card-grid section to the React Flight payload of
/resources/index.html. The visible HTML was already updated; without
this the section would be removed during React hydration."""

FILE = "resources/index.html"

NEW_SECTION_PAYLOAD = (
    '["$","section","69efb8195996bea084142eFD",{"className":"card-grid-section card-grid-section--paper","children":["$","div",null,{"className":"container","children":['
        '["$","span",null,{"className":"eyebrow","children":"Free Downloads"}],'
        '["$","h2",null,{"className":"mt-4 mb-4","children":"Free tools for operators."}],'
        "[\"$\",\"p\",null,{\"className\":\"lede\",\"style\":{\"maxWidth\":\"60ch\"},\"children\":\"Worksheets, references, and the operator's dictionary from the Amazon Best Seller. Use them. Adapt them. Run them on your buildings.\"}],"
        '["$","div",null,{"className":"card-grid card-grid--3","children":['
            '["$","div","0",{"className":"card card--gated","children":['
                '["$","h3",null,{"className":"card__heading","children":"The 5C™ Quick-Start Worksheet"}],'
                "[\"$\",\"p\",null,{\"className\":\"card__body\",\"children\":\"A 30-minute self-assessment for one of your buildings. Five questions mapped to the five C's, scored on a 1-5 grid. You get a Champion / Contender / Catching Up / Cold Start rating with the three plays to run next.\"}],"
                '["$","a",null,{"className":"card__cta","href":"#starter-kit","children":"Get the Worksheet →"}]'
            ']}],'
            '["$","div","1",{"className":"card","children":['
                '["$","h3",null,{"className":"card__heading","children":"The Vendor Contract Audit Checklist"}],'
                '["$","p",null,{"className":"card__body","children":"The 12 clauses every CRE owner should demand from their tech vendors — data export rights, admin credentials, API access, migration, and IP. Print-ready. Bring it to your next contract negotiation."}],'
                '["$","a",null,{"className":"card__cta","href":"/public/downloads/ppp-vendor-contract-checklist.pdf","children":"Download Free →"}]'
            ']}],'
            '["$","div","2",{"className":"card","children":['
                '["$","h3",null,{"className":"card__heading","children":"The PPP Glossary"}],'
                '["$","p",null,{"className":"card__body","children":"Every term in the playbook — 5C™, BoT®, Champion, data and digital infrastructure, owner-controlled, and more — defined in plain language for executive conversations."}],'
                '["$","a",null,{"className":"card__cta","href":"/glossary","children":"Open the Glossary →"}]'
            ']}]'
        ']}]'
    ']}]}]'
)

EDITS = [
    {
        "label": "#26 insert Free Downloads section into payload — before $L11 starterKit",
        "payload": (
            ',["$","$L11","69efb8195996bea084142e58",{"id":"69efb8195996bea084142e58","eyebrow":"Free Download","heading":"The PPP Starter Kit"',
            ',' + NEW_SECTION_PAYLOAD + ',["$","$L11","69efb8195996bea084142e58",{"id":"69efb8195996bea084142e58","eyebrow":"Free Download","heading":"The PPP Starter Kit"',
        ),
    },
]
