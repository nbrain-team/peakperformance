# Weekly Client Updates

### 2026-05-11 — OpticWise PPP Review form embeds wired into all marketing pages

- Added the canonical, full-page **PPP Review form embed** on `/ppp-review`, replacing the placeholder "Please use the form below" section so the page now renders the actual CRM-connected lead form (eyebrow: *Request a Data & Digital Infrastructure Review*; heading: *Tell us about the building you'd like reviewed*).
- Added the compact **Run the Play** CTA form embed at the bottom of every primary marketing page so visitors can submit a review request without leaving the page they're reading:
  - Homepage (`/`)
  - 5C Framework (`/5c-framework`)
  - For Owners (`/for-owners`)
  - For Asset Managers (`/for-asset-managers`)
  - For Property Managers (`/for-property-managers`)
  - For IT Managers (`/for-it-managers`)
  - About (`/about`)
- All embeds use the standard `data-opticwise-form="ppp-review"` attribute with consistent eyebrow / heading / description copy so the CRM can attribute every submission to the page it came from while presenting a single, unified form everywhere.
- Visual styling is unchanged — embeds reuse the existing dark CTA section layout (`cta-section cta-section--dark`) and narrow container styles so the form sits where the previous CTA buttons sat.
- Both the static HTML and the Next.js data-flight payload were updated so the embed survives client-side hydration and isn't overwritten on page load.

**Action item / open question for the client:** The OpticWise embed loader script (the JS that turns each `data-opticwise-form` div into a live form) is not yet referenced in the static mirror. We need the official OpticWise loader URL — or confirmation of which form provider (HubSpot, Formspree, Pardot, etc.) we should wire up — so we can complete the connection between the page and the CRM.
