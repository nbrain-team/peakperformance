#!/usr/bin/env python3
"""
Inject 'Connect with the Guest' and 'Connect with the Hosts' sections
into each podcast episode page.

Placement: After </ul> that closes "Resources mentioned" (before the
<details class="episode-transcript"> block), or if no transcript, at the
end of .rich-content.

For hosts-only episodes (no guest): only inject the hosts block.
"""

import json
import os
import re
import sys

WORKSPACE = "/Users/billdouglas/My Drive/Cursor/ppp-html"

HOSTS_HTML = """<div class="episode-connect">
<h3 class="episode-connect__heading">Connect With The Hosts</h3>
<div class="episode-connect__person">
<p class="episode-connect__name">Bill Douglas (Host)</p>
<ul class="episode-connect__links">
<li>LinkedIn: <a href="https://www.linkedin.com/in/billdouglas/" target="_blank" rel="noopener">linkedin.com/in/billdouglas</a></li>
<li>Email: <a href="mailto:bill.douglas@opticwise.com">bill.douglas@opticwise.com</a></li>
<li>OpticWise: <a href="https://opticwise.com" target="_blank" rel="noopener">opticwise.com</a></li>
</ul>
</div>
<div class="episode-connect__person">
<p class="episode-connect__name">Drew Hall (Co-Host)</p>
<ul class="episode-connect__links">
<li>LinkedIn: <a href="https://www.linkedin.com/in/drewhall33/" target="_blank" rel="noopener">linkedin.com/in/drewhall33</a></li>
<li>Email: <a href="mailto:drew.hall@opticwise.com">drew.hall@opticwise.com</a></li>
<li>OpticWise: <a href="https://opticwise.com" target="_blank" rel="noopener">opticwise.com</a></li>
</ul>
</div>
</div>"""


def build_guest_html(guest):
    """Build the 'Connect with the Guest' HTML block."""
    name = guest.get("guest_name", "")
    title = guest.get("guest_title", "")
    linkedin = guest.get("linkedin", "")
    email = guest.get("email", "")
    website = guest.get("website", "")
    phone = guest.get("phone", "")
    other = guest.get("other_contact", "")

    lines = []
    lines.append('<div class="episode-connect">')
    lines.append('<h3 class="episode-connect__heading">Connect With The Guest</h3>')
    lines.append('<div class="episode-connect__person">')
    lines.append(f'<p class="episode-connect__name">{name}</p>')
    if title:
        lines.append(f'<p class="episode-connect__role">{title}</p>')
    lines.append('<ul class="episode-connect__links">')

    if linkedin:
        display = linkedin.replace("https://www.", "").replace("https://", "").rstrip("/")
        lines.append(f'<li>LinkedIn: <a href="{linkedin}" target="_blank" rel="noopener">{display}</a></li>')
    if email:
        lines.append(f'<li>Email: <a href="mailto:{email}">{email}</a></li>')
    if website:
        href = website
        if not href.startswith("http"):
            href = "https://" + href
        display_url = href.replace("https://www.", "").replace("https://", "").replace("http://www.", "").replace("http://", "").rstrip("/")
        lines.append(f'<li>Website: <a href="{href}" target="_blank" rel="noopener">{display_url}</a></li>')
    if phone:
        lines.append(f'<li>Phone: {phone}</li>')
    if other:
        lines.append(f'<li>{other}</li>')

    lines.append('</ul>')
    lines.append('</div>')
    lines.append('</div>')
    return "\n".join(lines)


def inject_into_html(html, guest_block, hosts_block):
    """Insert the contact blocks before the transcript <details> or at end of rich-content."""
    combined = guest_block + "\n" + hosts_block if guest_block else hosts_block

    # Try to insert before <details class="episode-transcript">
    marker = '<details class="episode-transcript">'
    if marker in html:
        return html.replace(marker, combined + "\n" + marker)

    # Fallback: insert before closing </div> of .rich-content
    # Find the last </div> before </article>
    marker2 = '</div>\n</article>'
    if marker2 in html:
        return html.replace(marker2, combined + "\n" + marker2, 1)

    # Another fallback for minified HTML
    marker3 = '</div></article>'
    if marker3 in html:
        return html.replace(marker3, combined + "</div></article>", 1)

    print(f"  WARNING: Could not find insertion point", file=sys.stderr)
    return html


def already_has_contact(html):
    """Check if contact sections already exist."""
    return 'episode-connect' in html


def main():
    data_file = os.path.join(WORKSPACE, "scripts", "guest-data.json")
    if not os.path.exists(data_file):
        print(f"ERROR: {data_file} not found. Create it first.", file=sys.stderr)
        sys.exit(1)

    with open(data_file, "r") as f:
        guests = json.load(f)

    for entry in guests:
        slug = entry["slug"]
        is_hosts_only = entry.get("is_hosts_only", False)
        skip = entry.get("skip", False)

        if skip:
            print(f"SKIP: {slug}")
            continue

        filepath = os.path.join(WORKSPACE, "podcast", slug, "index.html")
        if not os.path.exists(filepath):
            print(f"NOT FOUND: {filepath}", file=sys.stderr)
            continue

        with open(filepath, "r", encoding="utf-8") as f:
            html = f.read()

        if already_has_contact(html):
            print(f"ALREADY DONE: {slug}")
            continue

        guest_block = "" if is_hosts_only else build_guest_html(entry)
        new_html = inject_into_html(html, guest_block, HOSTS_HTML)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(new_html)

        label = "hosts-only" if is_hosts_only else entry.get("guest_name", "?")
        print(f"DONE: {slug} ({label})")


if __name__ == "__main__":
    main()
