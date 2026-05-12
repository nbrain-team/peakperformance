# Item #35 — "infrastructure" language audit

**Source:** `PPP_Sandbox_Content_Review_v3.md` item #35
**Rule:** PPP voice should always be "**data and digital infrastructure**" (or "data & digital infrastructure"). Bare "infrastructure" is OK only when the modifier disambiguates ("physical infrastructure", "vendor-controlled infrastructure", etc.).

**What this is:** Every standalone or partial "infrastructure" mention in PPP-voice copy across the site, grouped by what you should probably do with it.

**Generated:** May 12, 2026 (Batch 3 prep)

---

## Bucket 1 — PPP voice, should probably expand

These are written in OUR voice (not external quotes) and use "digital infrastructure" or similar without the "data and" prefix. The spec says expand these.

### `/index.html` — home page

**Hero/thesis area (`thesis__sub`):**

> "Data ownership + digital infrastructure ownership + AI = actionable intelligence."

This is the home page thesis line. Per the rule, should become:

> "Data ownership + **data and digital infrastructure** ownership + AI = actionable intelligence."

But the line already has "data ownership" in front, so the repetition reads awkwardly. **Editorial call:** leave as-is and treat "digital infrastructure ownership" as an acceptable variant (your spec says "Digital backbone" is acceptable when context clearly references data & digital infrastructure — this case fits).

**Open Graph / meta-description range:**

> "...transforming commercial properties through data ownership and digital infrastructure — with implementation playbooks..."

Same case — "data ownership and digital infrastructure" reads cleanly. **Suggested:** leave, or change to "data ownership and digital infrastructure stewardship" if you want to differentiate.

---

### `/about/index.html` — about page

**Hero hook line:**

> "Decades of operating CRE technology — translated into a playbook any owner can run. We didn't write a manifesto. We wrote plays you can run on Monday morning."

(no "infrastructure" mention here directly — this came up in my grep but is a clean line)

**Conviction text:**

> "...who want control of the asset behind the asset — the data, the digital infrastructure, the systems that determine NOI, AI readiness, and exit math."

The phrasing "the data, the digital infrastructure, the systems" is editorial — three nouns in apposition. **Suggested:** leave. Expanding to "the data, the data and digital infrastructure, the systems" would be jarring.

**Drew Hall bio:**

> "He's spent his career in the field-level realities of digital infrastructure — the gap between what vendors promise and what actually runs at 2am..."

**Suggested:** change to "**field-level realities of data and digital infrastructure**" — Drew's bio is the strongest place to lock the brand phrase since he's the operator whose authority on the topic the site is asserting.

---

### `/resources/index.html` — FAQ section

**FAQ Q7 ("Right Butt, Wrong Seat"):**

> "...Property management and digital infrastructure are different positions."

This appears verbatim in both the FAQ HTML and the React payload. **Editorial call:** this is a tight rhetorical pairing ("property management" vs "digital infrastructure" as two job functions). Expanding to "property management and data and digital infrastructure are different positions" hurts rhythm. **Suggested:** leave, or rewrite as "Property management and **data-and-digital-infrastructure stewardship** are different positions."

---

## Bucket 2 — External quotes / endorsements (DO NOT edit)

These are quoted speech from other people. The brand voice rule applies to PPP-authored copy, not to others quoting in their own voice.

### `/book/index.html` — praise wall pull quotes

> "Digital infrastructure separates market leaders from the competition." — Praise wall quote
> "Digital infrastructure isn't just about efficiency — it's about competitive advantage." — Praise wall quote
> "This book cuts through the hype to deliver a practical digital infrastructure framework that drives NOI." — Praise wall quote
> "One of the real estate industry's greatest arbitrages is digital infrastructure. These strategies allow you to see buildings in a whole new way." — Praise wall quote

**All four are direct quotes from CRE leaders.** Their voice is theirs. Do not edit.

### `/resources/index.html` — FAQ Q10 (the Dealpath citation)

> "...98% of institutional CRE investors say improving their firm's **data infrastructure** is a top priority..."

This is paraphrased from the 2025/2026 Dealpath report. The report uses "data infrastructure" specifically. Citing it correctly means keeping the exact term they used. Do not edit.

---

## Bucket 3 — Episode titles / podcast metadata (DO NOT edit)

### `/podcast/index.html` — episode titles & URLs

- "Rethinking Digital Infrastructure: Driving Tenant Experience and Value in..."
- "Beyond PropTech: Why Digital Infrastructure and Data Control Matter for Your Building"
- URL slugs: `/rethinking-digital-infrastructure-...`, `/beyond-proptech-why-digital-infrastructure-...`

These are external episode titles (set when the episode was recorded/published) and the URL slugs that index them. Don't edit — URLs would break inbound links, episode titles are part of the public catalog.

---

## Bucket 4 — Already-correct phrasing my heuristic flagged (FALSE POSITIVES)

Auto-grep flagged these but they're already in approved forms:

- `/about/index.html`: "we design, implement, and operate **managed data & digital infrastructure services**" ✓ correct
- `/ppp-review/index.html`: section eyebrow says **"Request a Data & Digital Infrastructure Review"** ✓ correct
- `/be-on-the-show/index.html`: "...if you have something sharp to say about AI, data, or **digital infrastructure** in commercial real estate, we want to hear from you" — this is a list of topics (AI / data / digital infrastructure), distinct items. Acceptable as written.
- `/resources/index.html`: "vendor-controlled infrastructure" and "owner-controlled infrastructure" — these use the modifier-disambiguated pattern that the spec explicitly allows.
- `/glossary/index.html`: many matches in glossary definitions where "data and digital infrastructure" IS the term being defined (the canonical entry). All clean.

---

## Bucket 5 — SIC® definitional usage

`/glossary/index.html`, `/about/index.html`, etc.:

> "**SIC® (Security, Infrastructure, and Connectivity)**"

This is the SIC® acronym expansion. The "Infrastructure" here is part of a registered trademark expansion — do not edit.

---

## Recommended actions (your call)

| Where | Current | Proposed change | Decision |
|---|---|---|---|
| `/about/index.html` — Drew Hall bio | "field-level realities of digital infrastructure" | "field-level realities of **data and digital infrastructure**" | ☐ approve / ☐ skip |
| `/resources/index.html` — FAQ Q7 | "Property management and digital infrastructure are different positions" | "Property management and **data-and-digital-infrastructure stewardship** are different positions" — OR rewrite for rhythm | ☐ approve / ☐ skip / ☐ rewrite |
| `/index.html` — home thesis | "Data ownership + digital infrastructure ownership + AI = actionable intelligence" | Leave as variant (already has "data" in front; expanding reads redundant) | ☐ approve leave-as-is |
| `/about/index.html` — conviction text | "the data, the digital infrastructure, the systems..." | Leave (three-noun apposition; expansion breaks rhythm) | ☐ approve leave-as-is |
| `/index.html` — OG description | "...through data ownership and digital infrastructure..." | Leave (already has "data" upstream in the same phrase) | ☐ approve leave-as-is |

---

## How to apply changes

When you've decided, give me the list and I'll make the edits. If the change is small (1–2 fixes), I'll do a StrReplace directly. If it's bigger, I'll write a build script with the changes as a single source of truth.

**Note:** any change to `/resources/index.html` FAQ content needs to update three places: visible HTML, React Flight payload (`dangerouslySetInnerHTML`), and the FAQPage JSON-LD `acceptedAnswer.text` field. The `scripts/build/insert-resources-faq.py` script handles all three from one source — that's the cleanest way to amend.
