#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Item #1 [P0] from PPP_Sandbox_Content_Review_v3.md / Punch List P0-1:

Wire up the /ppp-review form on a static mirror of the Render-hosted site.

Strategy (post Bill's clarification 2026-05-14):
  - PRIMARY: the OWnet form embed
        <div data-opticwise-form="ppp-review"></div>
        <script src="https://ownet.opticwise.com/forms/embed.js" defer></script>
    This is the same loader pattern used everywhere else on production.
    OWnet's embed.js injects the form and handles its own submit + success.

  - FALLBACK: a hand-built HTML form, hidden by default, revealed by a
    small detector script if the OWnet loader fails (script 404, host
    unreachable, CSP block, or embed simply doesn't render within 6s).
    Fallback submits via mailto:bill@opticwise.com so leads don't get
    dropped during an OWnet outage. The fallback also renders a custom
    inline success state (heading + What-happens-next steps + 3 CTAs +
    OpticWise attribution).

Patches BOTH visible HTML and the React Flight payload's
`dangerouslySetInnerHTML.__html` field so hydration doesn't strip it.

Idempotent: if the form is already present, the script reports and exits.

Run from repo root:  python3 scripts/build/build-ppp-review-form.py
"""

import re
from pathlib import Path

FILE = Path("ppp-review/index.html")

# ---- Form markup ---------------------------------------------------------
# Single source of truth. We render this directly into the visible HTML and
# encode it for the payload's dangerouslySetInnerHTML.__html value.
FORM_HTML = '''<div data-opticwise-form="ppp-review" id="ppp-review-embed-mount"></div><div class="ppp-review-fallback" id="ppp-review-fallback" hidden><p class="ppp-review-fallback__note" role="status">Our secure form loader is taking longer than expected. You can submit directly below — your details will open in your mail client and reach us within 1 business day.</p><form id="ppp-review-form" class="ppp-review-form" novalidate>
<input type="hidden" name="source" value="ppp"/>
<input type="hidden" name="type" value="ppp-review"/>
<div class="form-field"><label for="ppp-review-name">Full Name <span class="form-req" aria-hidden="true">*</span></label><input type="text" id="ppp-review-name" name="name" required autocomplete="name"/></div>
<div class="form-field"><label for="ppp-review-email">Email Address <span class="form-req" aria-hidden="true">*</span></label><input type="email" id="ppp-review-email" name="email" required autocomplete="email"/></div>
<div class="form-field"><label for="ppp-review-phone">Phone Number <span class="form-req" aria-hidden="true">*</span></label><input type="tel" id="ppp-review-phone" name="phone" required autocomplete="tel"/></div>
<div class="form-field"><label for="ppp-review-property-name">Property Name <span class="form-req" aria-hidden="true">*</span></label><input type="text" id="ppp-review-property-name" name="property-name" required/></div>
<div class="form-field"><label for="ppp-review-property-type">What kind of CRE property? <span class="form-req" aria-hidden="true">*</span></label><select id="ppp-review-property-type" name="property-type" required><option value="">Select one</option><option value="office">Office</option><option value="multifamily">Multi-family Residential</option><option value="mixed-use">Mixed-use</option><option value="retail">Retail</option><option value="industrial">Industrial</option><option value="hospitality">Hospitality</option><option value="healthcare">Healthcare</option><option value="other">Other</option></select></div>
<div class="form-field"><label for="ppp-review-role">Your Role <span class="form-req" aria-hidden="true">*</span></label><select id="ppp-review-role" name="role" required><option value="">Select one</option><option value="owner-operator">Owner / Operator</option><option value="asset-manager">Asset Manager</option><option value="property-manager">Property Manager</option><option value="it-tech-leader">IT / Tech Leader</option><option value="acquisition-investment">Acquisition / Investment</option><option value="other">Other</option></select></div>
<div class="form-field"><label for="ppp-review-description">Detailed Request</label><textarea id="ppp-review-description" name="description" rows="5" placeholder="Tell us anything specific about the building or what you are hoping to learn from the review."></textarea></div>
<div class="form-field form-field--checkbox"><label class="checkbox-label"><input type="checkbox" name="terms-accepted" required/><span>By submitting, I agree to the <a href="https://opticwise.com/terms" target="_blank" rel="noopener">Terms &amp; Conditions</a> and <a href="https://opticwise.com/privacy-policy" target="_blank" rel="noopener">Privacy Policy</a>.</span></label></div>
<div class="form-error" id="ppp-review-error" role="alert" hidden></div>
<button type="submit" class="btn btn-primary btn-lg">Request a PPP Review</button>
<p class="form-note">We respond within 1 business day.</p>
</form><div class="form-success" id="ppp-review-success" hidden><h3>Got it. We&#x27;ll be in touch within 1 business day.</h3><p class="form-success__intro">Your request is queued for the OpticWise team. Here&#x27;s what happens next.</p><ol class="form-success__steps"><li><strong>We read your note today.</strong> A real human on the OpticWise team — not a bot — reviews what you sent.</li><li><strong>We schedule a 45-minute Clarify pass</strong> on the building you described. Owner-controlled. No software pitch. No rip-and-replace.</li><li><strong>You leave with a one-pager</strong> mapping who owns what, where your data lives, and the top three plays you can run on Monday.</li></ol><p class="form-success__cta-lede">While you wait — explore the playbook in action.</p><div class="form-success__actions"><a href="../podcast/index.html" class="btn btn-secondary">Listen to the Podcast →</a><a href="../book/index.html" class="btn btn-secondary">Get the Book →</a><a href="../5c-framework/index.html" class="btn btn-secondary">Explore the 5C™ Framework →</a></div><p class="form-success__attribution">Peak Property Performance® is a program of <a href="https://opticwise.com" target="_blank" rel="noopener">OpticWise</a> — the owner-controlled standard for CRE data and digital infrastructure.</p></div></div>'''

# The form-mount wrapper is the outer div React expects to mount into.
FORM_BLOCK_VISIBLE = f'<div class="ppp-review-form-mount">{FORM_HTML}</div>'


def encode_for_payload_innerhtml(html: str) -> str:
    """Encode HTML for embedding inside the dangerouslySetInnerHTML.__html
    JSON value, which itself lives inside a JS double-quoted string in the
    Flight payload. Empirically observed encoding (matches Next.js output):

      Original   →   In-file bytes
      "          →   \\\\\\"   (4 chars: 3 backslashes + 1 quote)
      \\          →   \\\\\\\\        (4 chars: 4 backslashes)
      <          →   \\u003c   (1 backslash + u003c — a JS unicode escape)
      >          →   \\u003e
      &          →   \\u0026
      other      →   unchanged

    The chain of transforms: JSON-encode (esc \\ and "), then JS-string-encode
    that JSON (esc \\ and " again), THEN apply the JS-unicode-escape pass for
    the HTML-meta characters (<, >, &). The unicode-escape pass goes last so
    its backslashes are NOT double-escaped — they're JS unicode escape
    syntax, not JSON content, so JS evaluates them to literal <, >, & at
    parse time, after which the JSON parser sees those characters literally.
    """
    s = html
    # JSON encode
    s = s.replace("\\", "\\\\")
    s = s.replace('"', '\\"')
    # JS-string encode (apply to JSON output)
    s = s.replace("\\", "\\\\")
    s = s.replace('"', '\\"')
    # JS unicode escapes for HTML meta chars (single backslash, not double)
    s = s.replace("<", "\\u003c")
    s = s.replace(">", "\\u003e")
    s = s.replace("&", "\\u0026")
    return s


# ---- Body-end scripts ---------------------------------------------------
# These live in separate <script> tags at body-end so they survive React
# hydration of the dangerouslySetInnerHTML block (script tags inside dSIH
# do not run).
#
# Three scripts emitted, in order:
#   1. OWnet embed loader (primary form) — external script with `defer`
#   2. Embed fallback detector — reveals the hidden fallback form if the
#      OWnet embed doesn't render within 6 seconds, or if the loader errors
#   3. Fallback submit handler — handles the mailto: path for the hand-built
#      form when the embed is unavailable
SUBMIT_HANDLER_SCRIPT = r'''<!-- ppp-review:scripts:start -->
<script src="https://ownet.opticwise.com/forms/embed.js" defer onerror="window.__pppOwnetFail&&window.__pppOwnetFail('script-error')"></script>
<script>
/*
  PPP Review form — OWnet embed fallback detector.

  Strategy:
    - Primary form is the OWnet embed (<div data-opticwise-form="ppp-review">),
      loaded by https://ownet.opticwise.com/forms/embed.js above.
    - If the script 404s, the host is unreachable, or the embed simply
      doesn't inject anything into its mount within EMBED_TIMEOUT_MS,
      reveal the hidden hand-built fallback form below so leads aren't dropped.
    - The detector is idempotent — calling it after a successful embed is a no-op.
*/
(function () {
  "use strict";
  var EMBED_TIMEOUT_MS = 6000;
  var revealed = false;

  function embedRendered(mount) {
    if (!mount) return false;
    if (mount.children.length > 0) return true;
    return !!mount.querySelector("form, iframe, input, [data-ow-form]");
  }

  function revealFallback(reason) {
    if (revealed) return;
    var mount = document.getElementById("ppp-review-embed-mount");
    var fallback = document.getElementById("ppp-review-fallback");
    if (!mount || !fallback) return;
    if (embedRendered(mount)) return;
    revealed = true;
    mount.style.display = "none";
    fallback.hidden = false;
    try { console.warn("[ppp-review] OWnet embed not detected; revealing fallback form. Reason:", reason); } catch (e) {}
  }
  window.__pppOwnetFail = revealFallback;

  function scheduleBackstop() {
    setTimeout(function () { revealFallback("timeout"); }, EMBED_TIMEOUT_MS);
  }
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", scheduleBackstop);
  } else {
    scheduleBackstop();
  }
})();
</script>
<script>
/*
  PPP Review form — fallback submit handler.

  Only fires if the OWnet embed (ownet.opticwise.com/forms/embed.js) failed
  to load or render and the hidden #ppp-review-fallback form was revealed
  by the detector above. The hand-built form posts via mailto: to
  bill@opticwise.com so a lead is never dropped when the embed host is down.

  Capture-phase submit delegation is used so the handler binds before any
  default form behaviour or future framework hydration intervenes.

  Long mailto URLs fail silently in many clients; the detailed-request field
  is truncated iteratively until the URL fits MAILTO_MAX_LEN.
*/
(function () {
  "use strict";

  var MAILTO_MAX_LEN = 1950;

  function collectFields(form) {
    var data = new FormData(form);
    var fields = {};
    data.forEach(function (value, key) {
      fields[key] = value;
    });
    return fields;
  }

  function buildBody(fields, descLimit) {
    var raw = fields.description || "(none provided)";
    var desc = raw;
    if (desc.length > descLimit) {
      desc = raw.slice(0, descLimit) + "\n[truncated — URL length limit; paste full details from the page if needed]";
    }
    return [
      "PPP REVIEW REQUEST",
      "",
      "Name:          " + (fields.name || ""),
      "Email:         " + (fields.email || ""),
      "Phone:         " + (fields.phone || ""),
      "Property name: " + (fields["property-name"] || ""),
      "Property type: " + (fields["property-type"] || ""),
      "Role:          " + (fields.role || ""),
      "",
      "Detailed request:",
      desc,
      "",
      "---",
      "Submitted via peakpropertyperformance.com/ppp-review",
      "Source: " + (fields.source || "") + " / Type: " + (fields.type || ""),
    ].join("\n");
  }

  function mailtoUrlForFields(fields) {
    var subject =
      "mailto:bill@opticwise.com?subject=" +
      encodeURIComponent(
        "PPP Review request from " + (fields.name || "site visitor")
      ) +
      "&body=";
    var descLimit = 6000;
    var url;
    for (;;) {
      url = subject + encodeURIComponent(buildBody(fields, descLimit));
      if (url.length <= MAILTO_MAX_LEN || descLimit <= 120) {
        break;
      }
      descLimit = Math.floor(descLimit * 0.55);
    }
    return url;
  }

  function onSubmitCapture(e) {
    var form = e.target;
    if (!form || form.id !== "ppp-review-form") {
      return;
    }

    var errorBox = document.getElementById("ppp-review-error");
    var success = document.getElementById("ppp-review-success");
    if (!errorBox || !success) {
      return;
    }

    e.preventDefault();
    e.stopPropagation();

    errorBox.hidden = true;
    errorBox.textContent = "";

    if (!form.checkValidity()) {
      form.reportValidity();
      return;
    }

    try {
      var fields = collectFields(form);
      window.location.href = mailtoUrlForFields(fields);
      form.hidden = true;
      success.hidden = false;
      success.scrollIntoView({ behavior: "smooth", block: "start" });
    } catch (err) {
      errorBox.hidden = false;
      errorBox.textContent =
        "Something went wrong submitting the form. Please email bill@opticwise.com directly with your details.";
    }
  }

  document.addEventListener("submit", onSubmitCapture, true);
})();
</script>
<!-- ppp-review:scripts:end -->'''


# ---- Patch logic ---------------------------------------------------------

OLD_VISIBLE = '<div class="ppp-review-form-mount"><div data-opticwise-form="ppp-review"></div></div>'

# OLD_PAYLOAD derived from OLD_VISIBLE via the same encoder, so the lookup
# pattern can never drift from the encoder's output format.
OLD_PAYLOAD = None  # computed in main() after encode_for_payload_innerhtml is defined

# Match the entire body-end script block between the sentinel HTML comments
# emitted at the top and bottom of SUBMIT_HANDLER_SCRIPT. Also matches the
# legacy single-handler block by its old comment header so an upgrade run
# from an earlier output is idempotent.
SUBMIT_SCRIPT_RE = re.compile(
    r"(?:<!-- ppp-review:scripts:start -->[\s\S]*?<!-- ppp-review:scripts:end -->"
    r"|<script>\s*/\*\s*\n\s*PPP Review form — submit handler\.[\s\S]*?</script>)",
    re.MULTILINE,
)


def main():
    if not FILE.exists():
        raise SystemExit(f"missing: {FILE}")

    content = FILE.read_text(encoding="utf-8")
    visible_done = False
    payload_done = False
    script_done = False

    # Single source of truth: the lookup pattern is whatever the encoder
    # produces for the original mount markup. Removes any chance of drift
    # between the regex and the actual file content.
    global OLD_PAYLOAD
    OLD_PAYLOAD = encode_for_payload_innerhtml(OLD_VISIBLE)

    # Idempotency check: if the embed mount + fallback form are already
    # present (the post-upgrade shape), skip the visible patch.
    has_new_shape = (
        'id="ppp-review-embed-mount"' in content
        and 'id="ppp-review-form"' in content
    )
    if has_new_shape:
        print("Form already present in visible HTML (embed+fallback shape) — skipping visible patch.")
    elif OLD_VISIBLE in content:
        content = content.replace(OLD_VISIBLE, FORM_BLOCK_VISIBLE, 1)
        visible_done = True
        print("✓ Visible HTML: replaced form mount with full form")
    else:
        print(f"⚠ Visible HTML: could not find expected mount markup\n   expected: {OLD_VISIBLE[:80]}…")

    # Payload patch
    payload_form_html = encode_for_payload_innerhtml(FORM_BLOCK_VISIBLE)
    if 'id=\\\\\"ppp-review-form\\\\\"' in content:
        print("Form already present in payload — skipping payload patch.")
    elif OLD_PAYLOAD in content:
        content = content.replace(OLD_PAYLOAD, payload_form_html, 1)
        payload_done = True
        print("✓ Payload: replaced form mount with encoded full form")
    else:
        # Try a slightly more lenient match (in case escape pattern differs)
        # Search for the literal mount inside dangerouslySetInnerHTML
        m = re.search(r'\\u003cdiv class=\\\\"ppp-review-form-mount\\\\"\\u003e.*?\\u003c/div\\u003e\\u003c/div\\u003e', content)
        if m:
            content = content[: m.start()] + payload_form_html + content[m.end():]
            payload_done = True
            print("✓ Payload: replaced form mount (lenient match) with encoded full form")
        else:
            print(f"⚠ Payload: could not find form mount in dangerouslySetInnerHTML")

    # Submit handler script — insert or replace before </body>
    script_m = SUBMIT_SCRIPT_RE.search(content)
    body_close = content.rfind("</body>")
    if script_m:
        content = content[: script_m.start()] + SUBMIT_HANDLER_SCRIPT + content[script_m.end() :]
        script_done = True
        print("✓ Submit handler script replaced")
    elif body_close != -1:
        content = content[:body_close] + SUBMIT_HANDLER_SCRIPT + content[body_close:]
        script_done = True
        print("✓ Submit handler script inserted before </body>")
    else:
        print("⚠ Could not find </body> to insert submit handler script")

    FILE.write_text(content, encoding="utf-8")
    print(f"\nFinal: visible={'Y' if visible_done else '-'}  payload={'Y' if payload_done else '-'}  script={'Y' if script_done else '-'}")
    print(f"Wrote {FILE} ({len(content)} bytes)")


if __name__ == "__main__":
    main()
