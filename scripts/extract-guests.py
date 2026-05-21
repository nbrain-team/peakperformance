#!/usr/bin/env python3
"""
Extract guest names and contact info from episode HTML pages.
Outputs guest-data.json for use by inject-contact-sections.py.
"""

import json
import os
import re
import html

WORKSPACE = "/Users/billdouglas/My Drive/Cursor/ppp-html"
PODCAST_DIR = os.path.join(WORKSPACE, "podcast")

HOSTS = {"Bill", "Drew", "Bill Douglas", "Drew Hall"}
SECTION_HEADERS = {
    "AI and Automation", "Anticipatory Service", "Case Studies", "Case Study",
    "Challenges in CRE", "Clarify", "Data Strategy", "Digital Infrastructure",
    "Digital Transformation", "EV Charging", "Embracing Change", "Extra Floor",
    "Financial Impacts", "Leadership Mindset", "Looking Ahead",
    "Modular Construction", "Preparing for the Next C", "Solo episode",
    "The Extra Floor", "Tracking Lead Sources", "Transitioning to Collect",
}


def decode_html(text):
    return html.unescape(text)


def extract_speakers(content):
    """Find all unique speaker names from the transcript."""
    pattern = r'episode-transcript__speaker">([^<:]+):'
    speakers = set()
    for m in re.finditer(pattern, content):
        name = decode_html(m.group(1)).strip()
        if name not in HOSTS and name not in SECTION_HEADERS:
            speakers.add(name)
    return speakers


def extract_contact_section(content):
    """Extract the last ~2000 chars of the transcript to find contact info."""
    transcript_match = re.search(
        r'<details class="episode-transcript">(.*?)</details>',
        content, re.DOTALL
    )
    if not transcript_match:
        return ""
    transcript = transcript_match.group(1)
    # Get last portion where contact info typically is
    return transcript[-4000:] if len(transcript) > 4000 else transcript


def find_linkedin(text, guest_name):
    """Search for LinkedIn URLs in text."""
    patterns = [
        r'linkedin\.com/in/[a-zA-Z0-9_-]+/?',
        r'LinkedIn[^<]*?linkedin\.com[^<]*',
    ]
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            url = m.group(0)
            if not url.startswith("http"):
                url = "https://www." + url
            return url.rstrip("/")
    return ""


def find_website(text, guest_name):
    """Search for website URLs (non-LinkedIn, non-social)."""
    # Look for explicit website mentions
    patterns = [
        r'(?:website|site|check out|visit)\s+(?:is\s+)?(?:at\s+)?([a-zA-Z0-9][a-zA-Z0-9.-]+\.[a-z]{2,}(?:/[^\s<"]*)?)',
        r'([a-zA-Z0-9][a-zA-Z0-9-]+\.(?:com|io|co|net|org)(?:/[^\s<"]*)?)',
    ]
    exclude = ['linkedin.com', 'peakpropertyperformance.com', 'opticwise.com',
               'youtube.com', 'spotify.com', 'apple.com', 'anchor.fm',
               'iheart.com', 'google.com', 'cloudfront.net']

    websites = []
    for p in patterns:
        for m in re.finditer(p, text, re.IGNORECASE):
            url = m.group(1) if m.lastindex else m.group(0)
            url = url.strip().rstrip(".,;)")
            if not any(e in url.lower() for e in exclude):
                websites.append(url)

    return websites[0] if websites else ""


def find_email(text):
    """Search for email addresses."""
    pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-z]{2,}'
    exclude = ['bill.douglas@opticwise.com', 'drew.hall@opticwise.com']
    for m in re.finditer(pattern, text):
        email = m.group(0)
        if email.lower() not in exclude:
            return email
    return ""


def find_phone(text):
    """Search for phone numbers."""
    pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
    m = re.search(pattern, text)
    return m.group(0) if m else ""


def process_episode(slug):
    """Process a single episode and return guest data."""
    filepath = os.path.join(PODCAST_DIR, slug, "index.html")
    if not os.path.exists(filepath):
        return None

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    speakers = extract_speakers(content)

    if not speakers:
        # Hosts-only episode
        return {
            "slug": slug,
            "guest_name": "",
            "guest_title": "",
            "linkedin": "",
            "email": "",
            "website": "",
            "phone": "",
            "other_contact": "",
            "is_hosts_only": True,
            "skip": slug == "coming-soon-peak-property-performance-with-bill-douglas-drew-hall",
        }

    guest_name = sorted(speakers)[0] if len(speakers) == 1 else ", ".join(sorted(speakers))

    contact_text = extract_contact_section(content)
    plain_contact = re.sub(r'<[^>]+>', ' ', contact_text)
    plain_contact = decode_html(plain_contact)

    linkedin = find_linkedin(plain_contact, guest_name)
    email = find_email(plain_contact)
    website = find_website(plain_contact, guest_name)
    phone = find_phone(plain_contact)

    return {
        "slug": slug,
        "guest_name": guest_name,
        "guest_title": "",
        "linkedin": linkedin,
        "email": email,
        "website": website,
        "phone": phone,
        "other_contact": "",
        "is_hosts_only": False,
        "skip": False,
    }


def main():
    episodes = []
    for entry in sorted(os.listdir(PODCAST_DIR)):
        if os.path.isdir(os.path.join(PODCAST_DIR, entry)):
            result = process_episode(entry)
            if result:
                episodes.append(result)
                status = "hosts-only" if result["is_hosts_only"] else result["guest_name"]
                print(f"  {entry}: {status}")

    output_path = os.path.join(WORKSPACE, "scripts", "guest-data.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(episodes, f, indent=2, ensure_ascii=False)

    print(f"\nWrote {len(episodes)} episodes to {output_path}")


if __name__ == "__main__":
    main()
