# -*- coding: utf-8 -*-
"""Add Free Downloads card-grid section to the React Flight payload of
/resources/index.html. The visible HTML was already updated; without
this the section would be removed during React hydration."""

FILE = "resources/index.html"

NEW_SECTION_PAYLOAD = (
    '["$","section","69efb8195996bea084142eFD",{"className":"card-grid-section card-grid-section--paper","children":["$","div",null,{"className":"container","children":['
        '["$","span",null,{"className":"eyebrow","children":"Free Downloads"}],'
        '["$","h2",null,{"className":"mt-4 mb-4","children":"Free tools for operators."}],'
        '["$","p",null,{"className":"lede","style":{"maxWidth":"60ch"},"children":"Worksheets and references from the Amazon Best Seller. Use them. Adapt them. Run them on your buildings."}],'
        '["$","div",null,{"className":"card-grid card-grid--2","children":['
            '["$","div","2",{"className":"card","children":['
                '["$","h3",null,{"className":"card__heading","children":"PPP Audit Worksheet"}],'
                "[\"$\",\"p\",null,{\"className\":\"card__body\",\"children\":\"Start the Clarify pass on one of your buildings yourself. Map ownership, identify what's portable, document what's trustworthy.\"}],"
                '["$","a",null,{"className":"card__cta","href":"/public/downloads/ppp-audit-worksheet.pdf","children":"Download →"}]'
            ']}],'
            '["$","div","3",{"className":"card card--gated","children":['
                '["$","h3",null,{"className":"card__heading","children":"Sample DDIA Report (Redacted)"}],'
                '["$","p",null,{"className":"card__body","children":"Redacted. So you can see what a PPP Review actually delivers before you ask for one. Email-gated."}],'
                '["$","a",null,{"className":"card__cta","href":"#starter-kit","children":"Get the Sample →"}]'
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
