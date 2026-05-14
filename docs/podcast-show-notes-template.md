# Peak Property Performance — Show Notes Template

This is the canonical structure for every episode's show-notes Google Doc going
forward. It mirrors the format already in use for Ep 26–35 (see Ep 27, 30, 32,
34 as exemplars). Roxanna writes against this for older episodes; the
`scripts/podcast_pipeline/draft_shownotes.py` script drafts against the same
structure from a transcript so a human can refine and approve.

**Doc title in Drive:** `PPP Episode NN — Show notes` (two-digit, e.g. `08`).
One doc per episode — the prior `Copy YT` second doc is no longer required.

---

## Required structure

```markdown
**[Episode title — punchy, headline-style]**

## **[Hook question — pulled from the guest's pain point or the episode's promise]**

In this episode of Peak Property Performance, Bill Douglas and Drew Hall sit
down with [Guest name], [Guest title at Company], to break down how operators
can improve [outcome 1], [outcome 2], and [outcome 3].

This conversation covers real operational lessons, including what works, what
fails, and how experienced operators [domain-specific framing — one short
sentence].

---

### **What You'll Learn**

* **[Bullet 1 — bold the lead phrase]** — short clarifying clause
* **[Bullet 2]**
* **[Bullet 3]**
* **[Bullet 4]**
* **[Bullet 5]**

---

### **Key Moments**

00:00 — Episode introduction
[MM:SS] — [Moment description]
[MM:SS] — [Moment description]
[MM:SS] — [Moment description]
[MM:SS] — [Moment description]
[MM:SS] — [Moment description]
[MM:SS] — Rapid fire questions ("Extra Floor")

---

### **Connect With Our Guest**

**[Guest Name]**
[Guest Title], [Company]
LinkedIn: [LinkedIn URL]
Email: [optional]
Company Website: [optional]

---

### **Connect With The Hosts**

**Bill Douglas (Host)**

* LinkedIn: https://www.linkedin.com/in/billdouglas/
* Email: bill.douglas@opticwise.com
* OpticWise: https://www.opticwise.com

**Drew Hall (Co-Host)**

* LinkedIn: https://www.linkedin.com/in/drewhall33/
* Email: drew.hall@opticwise.com
* OpticWise: https://www.opticwise.com

---

### **Operator Resources**

OpticWise
https://opticwise.com

Peak Property Performance — Best Selling Book & Podcast
https://www.peakpropertyperformance.com/

---

### **About the Peak Property Performance Podcast**

The Peak Property Performance Podcast explores how commercial real estate
owners and operators improve performance through digital clarity, data
discipline, and better decision-making. Conversations focus on real-world
execution and experience shares, not product promotion.

---

### **Industry Tags**

#CommercialRealEstate
#AssetManagement
#PropertyOperations
#CRE
#PeakPropertyPerformance
#Multifamily
#PropTech
#RealEstateInvesting
```

---

## Variants

**Solo / hosts-only episodes** (e.g. Ep 27): replace the guest paragraph with a
single sentence — *"In this episode of Peak Property Performance, Bill Douglas
and Drew Hall break down…"* — and add this line just above **Connect With The
Hosts**:

> *Note: This episode is a special update — no external guest; hosts only.*

Omit the **Connect With Our Guest** section.

**Two-guest episodes** (e.g. Ep 3): list both guests under the same section,
each with their own LinkedIn line.

---

## Authoring rules

1. **Bold leading phrases** in the *What You'll Learn* bullets — the bold
   portion is what scans on YouTube/Apple/Spotify.
2. **Timestamps in `Key Moments`** use `MM:SS` separated from the description by
   ` — ` (em dash with spaces). Five to seven moments is the norm.
3. **Always end with the Rapid Fire / Extra Floor line** when the recording has
   it.
4. **Hashtags stay in the standard set** unless the episode has a strong
   topical hook (then add 1–2 specific tags at the end).
5. **No external promotions or product pitches** in the body — keep guest
   company links in the dedicated guest section only.
6. **Guest email is optional** — include it only when the guest has explicitly
   said it can be public.

---

## Naming standards (Drive)

| Asset | Drive name (Doc) or filename (binary) |
|---|---|
| Show notes doc | `PPP Episode NN — Show notes` |
| Transcript doc/file | `PPP Episode NN — Transcript` (Doc) **or** `PPP-Episode-NN-Transcript.txt` |
| Master audio | `PPP-Episode-NN-Audioversion.mp3` |
| Main video | `PPP-Episode-NN-Main.mp4` |
| Thumbnail (16×9) | `PPP-Episode-NN-Thumbnail-16x9.png` |
| Thumbnail (1×1) | `PPP-Episode-NN-Thumbnail-1x1.png` |

Two-digit episode numbers (`08`, not `8`) so alphabetical sorting matches
episode order. Drop ops-only docs (logins, internal notes) from episode
folders.
