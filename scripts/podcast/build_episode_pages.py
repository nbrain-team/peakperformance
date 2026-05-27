"""Regenerate podcast/<slug>/index.html pages with SEO-optimized show notes + transcript.

ARCHITECTURE (per user directive 2026-05-18)
============================================
1. RSS feed (Anchor) is the TRIGGER — which episodes exist, what's the latest.
   Cached at scripts/podcast/_anchor_rss.xml; refresh with fetch_rss.sh.
2. Per-ep Drive folder is the CANONICAL asset source. Master folder:
       https://drive.google.com/drive/folders/1mhA8fDK9uPIn-1IzM-eG_yd5VOfnpWHO
   Each Ep N subfolder contains transcript .docx, show notes .pdf,
   YouTube thumbnail .jpg, optionally a 1x1 .png override, etc.
3. RSS feed is the FALLBACK for anything not in the Drive folder
   (description, dates, mp3, image, duration).

Per-ep folders are NOT synced to local disk, so transcript/show-notes
extraction is done from the locally-synced flat mirror at
~/My Drive/AA DOWNLOADS - WD rev 2025-Apr/PPP-Podcast-Deliverables/
(which the user maintains as a copy). YouTube thumbnails are fetched
from the public CDN at img.youtube.com (functionally identical to the
Drive-folder copy). Future enhancement: agent-driven MCP fetch of per-ep
folder assets to detect user overrides.

USAGE
=====
    python3 scripts/podcast/build_episode_pages.py            # all eps
    python3 scripts/podcast/build_episode_pages.py --ep 1     # one ep
    python3 scripts/podcast/build_episode_pages.py --eps 1,2,3
"""
from __future__ import annotations
import argparse
import csv
import datetime as dt
import html
import io
import json
import os
import re
import sys
import urllib.request
from pathlib import Path
from xml.etree import ElementTree as ET

sys.path.insert(0, '/Users/billdouglas/Library/Python/3.9/lib/python/site-packages')

import docx
from pdfminer.high_level import extract_text as pdf_extract_text
from PIL import Image


SCRIPTS = Path(__file__).resolve().parent
ROOT = SCRIPTS.parent.parent
PODCAST_DIR = ROOT / 'podcast'
RSS_PATH = SCRIPTS / '_anchor_rss.xml'
INDEX_PATH = SCRIPTS / '_episode_index.json'
DELIV_LAPTOP = Path('/Users/billdouglas/My Drive/AA DOWNLOADS - WD rev 2025-Apr/PPP-Podcast-Deliverables')
DELIV_CACHE = SCRIPTS / '_drive_cache'

# Search both paths for transcripts/show notes/master CSV. The laptop
# mirror is preferred (faster + always available locally) when present,
# but on Render / any non-laptop host only DELIV_CACHE will exist.
DELIV_SEARCH_PATHS = [DELIV_LAPTOP, DELIV_CACHE]

# master-episodes.csv: prefer the laptop mirror copy if present, else
# fall back to a copy that lives alongside the cache.
MASTER_CSV = None
for base in DELIV_SEARCH_PATHS:
    candidate = base / 'master-episodes.csv'
    if candidate.exists():
        MASTER_CSV = candidate
        break
if MASTER_CSV is None:
    MASTER_CSV = DELIV_CACHE / 'master-episodes.csv'  # may not exist; load_master_csv handles missing
DRIVE_THUMBS_PATH = SCRIPTS / '_drive_thumbnails.json'

DRIVE_ROOT_FOLDER_ID = '1mhA8fDK9uPIn-1IzM-eG_yd5VOfnpWHO'
SITE_BASE = 'https://peakpropertyperformance.com'


def load_drive_thumb_overrides() -> dict[int, dict]:
    """Per-episode Drive thumbnail overrides.

    Some episodes (notably newer ones) have FEAT.-branded thumbnails uploaded
    to the per-ep Drive folder but the YouTube channel still shows the generic
    template, so img.youtube.com would serve the wrong art. This map lets us
    point those episodes at the Drive-hosted branded file IDs directly.
    """
    if not DRIVE_THUMBS_PATH.exists():
        return {}
    raw = json.loads(DRIVE_THUMBS_PATH.read_text())
    return {int(k): v for k, v in raw.get('episodes', {}).items()}


def drive_thumb_url(file_id: str, size: str = 'w1280') -> str:
    return f'https://drive.google.com/thumbnail?id={file_id}&sz={size}'


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_index() -> list[dict]:
    return json.loads(INDEX_PATH.read_text())['episodes']


def load_master_csv() -> dict[int, dict]:
    """Read master-episodes.csv. Returns {} if the file doesn't exist
    (on Render the YouTube IDs come from the index instead)."""
    out: dict[int, dict] = {}
    if not MASTER_CSV or not MASTER_CSV.exists():
        return out
    with MASTER_CSV.open() as f:
        for row in csv.DictReader(f):
            try:
                n = int(row['ep_num'])
            except (KeyError, ValueError):
                continue
            out[n] = row
    return out


# ---------------------------------------------------------------------------
# Asset resolution: per-ep Drive folder first, then flat mirror, then RSS
# ---------------------------------------------------------------------------

def find_transcript(ep_num: int) -> Path | None:
    """Locate the transcript .docx for an episode. Searches both the
    laptop's Drive Desktop sync mirror and the cron-job-populated cache."""
    for base in DELIV_SEARCH_PATHS:
        matches = list((base / 'transcripts').glob(f'PPP Ep {ep_num} - Transcript - *.docx'))
        if matches:
            return matches[0]
    return None


def find_show_notes(ep_num: int) -> Path | None:
    for base in DELIV_SEARCH_PATHS:
        matches = list((base / 'show_notes').glob(f'PPP Ep {ep_num} - Show Notes - *.pdf'))
        if matches:
            return matches[0]
    return None


def fetch_thumbnail(youtube_id: str, dest_dir: Path) -> tuple[Path, Path]:
    """Download YouTube maxres thumbnail; produce a 1:1 center crop alongside.
    Returns (path_to_16x9, path_to_1x1). Idempotent."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    p16x9 = dest_dir / 'thumbnail-16x9.jpg'
    p1x1 = dest_dir / 'thumbnail.jpg'
    if not p16x9.exists():
        url = f'https://img.youtube.com/vi/{youtube_id}/maxresdefault.jpg'
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = resp.read()
        # YouTube returns a 120x90 placeholder if maxres isn't available;
        # fall back to hqdefault in that case.
        if len(data) < 5000:
            url = f'https://img.youtube.com/vi/{youtube_id}/hqdefault.jpg'
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = resp.read()
        p16x9.write_bytes(data)
    if not p1x1.exists():
        img = Image.open(p16x9).convert('RGB')
        w, h = img.size
        side = min(w, h)
        left = (w - side) // 2
        top = (h - side) // 2
        cropped = img.crop((left, top, left + side, top + side))
        # Resize to a reasonable web size (max 800)
        if side > 800:
            cropped = cropped.resize((800, 800), Image.LANCZOS)
        cropped.save(p1x1, 'JPEG', quality=88, optimize=True)
    return p16x9, p1x1


# ---------------------------------------------------------------------------
# Content extraction
# ---------------------------------------------------------------------------

def extract_transcript(docx_path: Path) -> dict:
    """Parse a transcript .docx → structured dialogue + meta header.

    Transcripts follow a consistent shape:
      • [Title]
      • [1-paragraph teaser]
      • "Key Topics Covered" + bullet list
      • "Episode Transcript"
      • <Section header>
      • <Speaker>: <utterance>
      • ...
      • "About Peak Property Performance"
      • [boilerplate]
      • Watch this episode on YouTube: <url>
    """
    document = docx.Document(str(docx_path))
    paragraphs = [p.text.strip() for p in document.paragraphs if p.text.strip()]

    key_topics: list[str] = []
    dialogue: list[dict] = []  # each: {kind: 'header'|'turn', text|speaker, body}
    in_topics = False
    in_transcript = False
    in_outro = False
    SPEAKER_RE = re.compile(r'^([A-Z][A-Za-z\.\- ]{1,40}):\s*(.*)$')

    last_speaker = None
    for p in paragraphs:
        if p == 'Key Topics Covered':
            in_topics = True
            continue
        if p == 'Episode Transcript':
            in_topics = False
            in_transcript = True
            continue
        if p == 'About Peak Property Performance':
            in_transcript = False
            in_outro = True
            continue
        if in_topics:
            key_topics.append(p)
            continue
        if in_outro:
            continue  # drop the standard boilerplate
        if not in_transcript:
            continue  # skip header (title + teaser)

        m = SPEAKER_RE.match(p)
        if m and m.group(1) not in {'About', 'Watch'}:
            speaker = m.group(1).strip()
            body = m.group(2).strip()
            dialogue.append({'kind': 'turn', 'speaker': speaker, 'body': body})
            last_speaker = speaker
        else:
            # Section header (e.g. "Understanding the Vision Behind the Podcast")
            # Heuristic: short-ish line, no colon, doesn't start with lower case
            if len(p) < 90 and not p.endswith('.') and not p.endswith('?'):
                dialogue.append({'kind': 'header', 'text': p})
            else:
                # Continuation of previous speaker turn
                if dialogue and dialogue[-1]['kind'] == 'turn':
                    dialogue[-1]['body'] += '\n' + p
                else:
                    dialogue.append({'kind': 'turn', 'speaker': last_speaker or '', 'body': p})

    return {
        'key_topics': key_topics,
        'dialogue': dialogue,
        'total_chars': sum(len(p) for p in paragraphs),
        'paragraph_count': len(paragraphs),
    }


def extract_show_notes(pdf_path: Path) -> dict:
    """Parse a show notes PDF → structured sections."""
    raw = pdf_extract_text(str(pdf_path))
    # PDF artifacts: (cid:127) = bullet
    raw = raw.replace('(cid:127)', '•')
    raw = raw.replace('\u00a0', ' ')
    # Normalize whitespace
    lines = [ln.rstrip() for ln in raw.splitlines()]

    sections: dict[str, list[str]] = {}
    current_section = None
    KNOWN_HEADINGS = [
        'Episode Overview',
        'Quote From the Episode',
        "What You'll Learn",
        'Key Moments',
        'Guest Spotlight',
        'Connect With The Hosts',
        'Operator Resources & Links Mentioned',
        'Calls To Action',
        'Tags',
    ]
    for ln in lines:
        ln_s = ln.strip()
        # Match section headings
        matched = None
        for h in KNOWN_HEADINGS:
            if ln_s == h or ln_s.startswith(h + ' '):
                matched = ln_s
                break
        if matched:
            current_section = matched
            sections.setdefault(current_section, [])
            continue
        if current_section and ln_s:
            sections[current_section].append(ln_s)
        elif current_section and not ln_s and sections[current_section]:
            # blank line within section → paragraph break marker
            sections[current_section].append('')

    def _paragraphs(lines_):
        """Collapse consecutive non-empty lines into paragraphs."""
        out, buf = [], []
        for ln in lines_:
            if ln:
                buf.append(ln)
            else:
                if buf:
                    out.append(' '.join(buf))
                    buf = []
        if buf:
            out.append(' '.join(buf))
        return out

    def _bullets(lines_):
        out = []
        cur = []
        for ln in lines_:
            if ln == '•':
                continue  # standalone bullet marker, no text
            if ln.startswith('•'):
                if cur:
                    out.append(' '.join(cur).strip())
                cur = [ln.lstrip('•').strip()]
            elif ln:
                cur.append(ln)
            else:
                if cur:
                    out.append(' '.join(cur).strip())
                    cur = []
        if cur:
            out.append(' '.join(cur).strip())
        return [b for b in out if b]

    overview = _paragraphs(sections.get('Episode Overview', []))
    learn = _paragraphs(sections.get("What You'll Learn", []))
    moments_raw = _paragraphs(sections.get('Key Moments', []))
    # Key moments lines like "00:00 — Intro"
    moments = []
    for ln in moments_raw:
        m = re.match(r'^(\d{1,2}:\d{2}(?::\d{2})?)\s*[—\-–]\s*(.*)$', ln)
        if m:
            moments.append({'time': m.group(1), 'label': m.group(2).strip()})
    quote_lines = _paragraphs(sections.get('Quote From the Episode', []))
    quote = quote_lines[0] if quote_lines else ''
    # Quote often: '"text..." — Speaker'
    quote_text, quote_attr = quote, ''
    m = re.match(r'^[\u201c"](.*?)[\u201d"]\s*[—\-–]\s*(.+)$', quote)
    if m:
        quote_text = m.group(1).strip()
        quote_attr = m.group(2).strip()

    resources = _paragraphs(sections.get('Operator Resources & Links Mentioned', []))
    tags_lines = sections.get('Tags', [])
    tags = re.findall(r'#[A-Za-z0-9_]+', ' '.join(tags_lines))

    return {
        'overview': overview,
        'what_youll_learn': learn,
        'key_moments': moments,
        'quote_text': quote_text,
        'quote_attr': quote_attr,
        'resources': resources,
        'tags': tags,
    }


# ---------------------------------------------------------------------------
# HTML rendering helpers
# ---------------------------------------------------------------------------

def h(s: str) -> str:
    return html.escape(s, quote=True)


def linkify(text: str) -> str:
    """Convert bare URLs in already-escaped text to <a> links."""
    return re.sub(
        r'(https?://[^\s&<]+)',
        lambda m: f'<a href="{m.group(1)}" target="_blank" rel="noopener">{m.group(1)}</a>',
        text,
    )


def render_iso_duration(hhmmss: str) -> str:
    """Convert '00:32:28' or '32:28' to ISO 8601 duration like PT32M28S."""
    parts = [int(p) for p in hhmmss.split(':')]
    if len(parts) == 3:
        hh, mm, ss = parts
    elif len(parts) == 2:
        hh, mm, ss = 0, parts[0], parts[1]
    else:
        return ''
    out = 'PT'
    if hh:
        out += f'{hh}H'
    if mm or hh:
        out += f'{mm}M'
    out += f'{ss}S'
    return out


def pretty_duration(hhmmss: str) -> str:
    parts = [int(p) for p in hhmmss.split(':')]
    if len(parts) == 3:
        hh, mm, ss = parts
    elif len(parts) == 2:
        hh, mm, ss = 0, parts[0], parts[1]
    else:
        return hhmmss
    if hh:
        return f'{hh}h {mm}m'
    return f'{mm} min'


# ---------------------------------------------------------------------------
# Main per-episode renderer
# ---------------------------------------------------------------------------

NAV_HTML = '''<nav class="nav"><div class="container nav__inner"><a class="nav__brand" href="../../index.html"><span class="nav__brandmark">PPP</span>Peak Property Performance®</a><div class="nav__links"><a class="nav__link" href="../../book/index.html">Book</a><a class="nav__link" href="../index.html">Podcast</a><a class="nav__link" href="../../5c-framework/index.html">5C™ Framework</a><a class="nav__link" href="../../about/index.html">About</a><div class="nav__dropdown"><span class="nav__link nav__dropdown-trigger" role="button" tabindex="0" aria-haspopup="true">By Role</span><div class="nav__dropdown-menu"><a class="nav__link" href="../../for-owners/index.html">For Owners</a><a class="nav__link" href="../../for-asset-managers/index.html">For Asset Managers</a><a class="nav__link" href="../../for-property-managers/index.html">For Property Managers</a><a class="nav__link" href="../../for-it-managers/index.html">For IT Managers</a></div></div><div class="nav__dropdown"><span class="nav__link nav__dropdown-trigger" role="button" tabindex="0" aria-haspopup="true">Resources</span><div class="nav__dropdown-menu"><a class="nav__link" href="../../resources/index.html">Free Downloads</a><a class="nav__link" href="../../glossary/index.html">PPP Glossary</a><a class="nav__link" href="../../faq/index.html">FAQ</a><a class="nav__link" href="../../vendor-contract-audit/index.html">Vendor Contract Audit</a><a class="nav__link" href="../../ppp-review/index.html">Request a PPP Review</a></div></div><a class="btn btn-primary btn-sm" href="../../book/index.html">Get the Book</a></div></div></nav>'''

FOOTER_HTML = '''<footer class="footer"><div class="container"><div class="footer__grid"><div><a class="footer__brand" href="../../index.html"><span class="nav__brandmark">PPP</span>Peak Property Performance®</a><p class="footer__tagline">Amazon Best Seller. The CRE strategy playbook for owners, operators, and the leaders building the future of the industry.</p></div><div><div class="footer__col-heading">Read &amp; Listen</div><a class="footer__link" href="../../book/index.html">The PPP Book</a><a class="footer__link" href="../index.html">The PPP Podcast</a><a class="footer__link" href="../../be-on-the-show/index.html">Be on the Show</a></div><div><div class="footer__col-heading">By Role</div><a class="footer__link" href="../../for-owners/index.html">For CRE Owners</a><a class="footer__link" href="../../for-asset-managers/index.html">For Asset Managers</a><a class="footer__link" href="../../for-it-managers/index.html">For IT Managers</a><a class="footer__link" href="../../for-property-managers/index.html">For Property Managers</a></div><div><div class="footer__col-heading">Get Started</div><a class="footer__link" href="../../5c-framework/index.html">5C™ Framework</a><a class="footer__link" href="../../resources/index.html">Free Resources</a><a class="footer__link" href="../../faq/index.html">FAQ</a><a class="footer__link" href="../../ppp-review/index.html">Request a PPP Review</a><a class="footer__link" href="../../about/index.html">About</a></div></div><div class="footer__publisher"><img src="../../api/media/file/fast-company-press.webp" alt="Fast Company Press"/><div class="footer__publisher-text"><strong>Published by Fast Company Press</strong><span>An imprint dedicated to ideas that move business forward.</span></div></div><div class="footer__bottom"><span>© 2026 Peak Property Performance®. All rights reserved.</span><span><a href="../../privacy/index.html" style="color:rgba(245,240,228,0.7)">Privacy Policy</a> · <a href="../../terms/index.html" style="color:rgba(245,240,228,0.7)">Terms of Use</a> · <a href="../../cookie-policy/index.html" style="color:rgba(245,240,228,0.7)" data-cc-settings>Cookie Settings</a></span><span>A program of <a href="https://opticwise.com/" target="_blank" rel="noopener" style="color:rgba(245,240,228,0.7)">OpticWise</a></span></div></div></footer>'''

THREE_WAYS_HTML = '''<section class="cta-section cta-section--dark three-ways-blocks"><div class="container"><span class="eyebrow no-rule" style="justify-content:center;display:flex">Get Started</span><h2 class="mt-4 mb-4">Three ways in.</h2><p class="lede three-ways-blocks__lede" style="max-width:52ch;margin-inline:auto">Whether you&#x27;re scouting, training camp, or game time — there&#x27;s a way to start today.</p><div class="three-ways-blocks__cta-rows"><div class="three-ways-blocks__cta-row three-ways-blocks__cta-row--primary"><a class="btn btn-primary btn-lg" href="../../book/index.html#retailers">Get the book</a><a class="btn btn-primary btn-lg" href="../../book/index.html#audiobook-retailers">Listen to the book</a><a class="btn btn-primary btn-lg" href="../../podcast/index.html">Listen to the podcast</a></div><div class="three-ways-blocks__cta-row three-ways-blocks__cta-row--secondary"><a class="btn btn-lg three-ways-blocks__cta-review" href="../../ppp-review/index.html">Request PPP Review</a></div></div></div></section>'''


def render_recent_episodes(slug: str, all_eps: list[dict]) -> str:
    """Sidebar list of 4 most recent episodes (excluding current)."""
    eps = [e for e in all_eps if e.get('slug') and e['slug'] != slug and e['rss_ep_num'] is not None]
    eps.sort(key=lambda e: e['rss_pub_date'], reverse=True)
    items = []
    for ep in eps[:4]:
        items.append(
            f'<li style="margin-bottom:var(--space-3)">'
            f'<a style="color:var(--text);font-family:var(--font-display);font-weight:600;font-size:var(--fs-body-sm)" '
            f'href="../{h(ep["slug"])}/index.html">{h(ep["rss_title"])}</a></li>'
        )
    return f'<div class="aside-card"><h4>Recent Episodes</h4><ul style="margin-top:var(--space-3)">{"".join(items)}</ul></div>'


def render_show_notes_html(sn: dict) -> str:
    parts = []

    if sn['overview']:
        parts.append('<h2 class="rich-content__h2">Episode Overview</h2>')
        for p in sn['overview']:
            parts.append(f'<p>{h(p)}</p>')

    if sn['quote_text']:
        attr = f'<cite>— {h(sn["quote_attr"])}</cite>' if sn['quote_attr'] else ''
        parts.append(
            f'<blockquote class="episode-quote">'
            f'<p>“{h(sn["quote_text"])}”</p>{attr}</blockquote>'
        )

    if sn['what_youll_learn']:
        parts.append('<h2 class="rich-content__h2">What you’ll learn</h2>')
        parts.append('<ul class="rich-content__list">')
        for item in sn['what_youll_learn']:
            parts.append(f'<li>{h(item)}</li>')
        parts.append('</ul>')

    if sn['key_moments']:
        parts.append('<h2 class="rich-content__h2">Key moments</h2>')
        parts.append('<ul class="episode-chapters">')
        for m in sn['key_moments']:
            parts.append(
                f'<li><span class="episode-chapters__time">{h(m["time"])}</span>'
                f'<span class="episode-chapters__label">{h(m["label"])}</span></li>'
            )
        parts.append('</ul>')

    if sn['resources']:
        parts.append('<h2 class="rich-content__h2">Resources mentioned</h2>')
        parts.append('<ul class="rich-content__list">')
        for r in sn['resources']:
            parts.append(f'<li>{linkify(h(r))}</li>')
        parts.append('</ul>')

    return '\n'.join(parts)


def render_transcript_html(tr: dict) -> str:
    """Render the transcript inside a <details> expander."""
    parts = ['<details class="episode-transcript"><summary class="episode-transcript__toggle">'
             '<span>Read the full transcript</span>'
             '<span class="episode-transcript__hint">'
             f'{tr["total_chars"]:,} characters · auto-generated, lightly cleaned'
             '</span></summary><div class="episode-transcript__body">']
    for item in tr['dialogue']:
        if item['kind'] == 'header':
            parts.append(f'<h3 class="episode-transcript__section">{h(item["text"])}</h3>')
        else:
            speaker = item.get('speaker') or ''
            body = item['body'].replace('\n', '<br>')
            sp_html = f'<strong class="episode-transcript__speaker">{h(speaker)}:</strong> ' if speaker else ''
            parts.append(f'<p class="episode-transcript__turn">{sp_html}{h(body) if not speaker else ""}'
                         f'{body.replace(chr(10), "<br>") if speaker else ""}</p>')
    parts.append('</div></details>')
    # The above was getting hacky; render cleaner version below
    return _render_transcript_clean(tr)


def _render_transcript_clean(tr: dict) -> str:
    parts = [
        '<details class="episode-transcript"><summary class="episode-transcript__toggle">'
        '<span class="episode-transcript__label">Read the full transcript</span>'
        f'<span class="episode-transcript__meta">{tr["total_chars"]:,} characters · auto-generated, lightly cleaned</span>'
        '</summary><div class="episode-transcript__body">'
    ]
    for item in tr['dialogue']:
        if item['kind'] == 'header':
            parts.append(f'<h3 class="episode-transcript__section">{h(item["text"])}</h3>')
        else:
            speaker = (item.get('speaker') or '').strip()
            body_html = h(item['body']).replace('\n', '<br>')
            if speaker:
                parts.append(
                    f'<p class="episode-transcript__turn">'
                    f'<strong class="episode-transcript__speaker">{h(speaker)}:</strong> '
                    f'{body_html}</p>'
                )
            else:
                parts.append(f'<p class="episode-transcript__turn">{body_html}</p>')
    parts.append('</div></details>')
    return '\n'.join(parts)


def _render_contact_sections(slug: str) -> str:
    """Render Connect with Guest + Connect with Hosts HTML blocks.

    Guest data comes from scripts/guest-data.json. If no entry found for slug,
    only the hosts block is returned.
    """
    import pathlib
    guest_data_path = pathlib.Path(__file__).resolve().parent.parent / 'guest-data.json'
    guests = []
    if guest_data_path.exists():
        import json as _json
        guests = _json.loads(guest_data_path.read_text(encoding='utf-8'))

    hosts_html = (
        '<div class="episode-connect">\n'
        '<h3 class="episode-connect__heading">Connect With The Hosts</h3>\n'
        '<div class="episode-connect__person">\n'
        '<p class="episode-connect__name">Bill Douglas (Host)</p>\n'
        '<ul class="episode-connect__links">\n'
        '<li>LinkedIn: <a href="https://www.linkedin.com/in/billdouglas/" target="_blank" rel="noopener">linkedin.com/in/billdouglas</a></li>\n'
        '<li>Email: <a href="mailto:bill.douglas@opticwise.com">bill.douglas@opticwise.com</a></li>\n'
        '<li>OpticWise: <a href="https://opticwise.com" target="_blank" rel="noopener">opticwise.com</a></li>\n'
        '</ul>\n</div>\n'
        '<div class="episode-connect__person">\n'
        '<p class="episode-connect__name">Drew Hall (Co-Host)</p>\n'
        '<ul class="episode-connect__links">\n'
        '<li>LinkedIn: <a href="https://www.linkedin.com/in/drewhall33/" target="_blank" rel="noopener">linkedin.com/in/drewhall33</a></li>\n'
        '<li>Email: <a href="mailto:drew.hall@opticwise.com">drew.hall@opticwise.com</a></li>\n'
        '<li>OpticWise: <a href="https://opticwise.com" target="_blank" rel="noopener">opticwise.com</a></li>\n'
        '</ul>\n</div>\n</div>'
    )

    entry = next((g for g in guests if g.get('slug') == slug), None)
    if not entry or entry.get('is_hosts_only') or entry.get('skip'):
        return hosts_html

    name = entry.get('guest_name', '')
    title = entry.get('guest_title', '')
    linkedin = entry.get('linkedin', '')
    email = entry.get('email', '')
    website = entry.get('website', '')
    phone = entry.get('phone', '')
    other = entry.get('other_contact', '')

    lines = ['<div class="episode-connect">',
             '<h3 class="episode-connect__heading">Connect With The Guest</h3>',
             '<div class="episode-connect__person">',
             f'<p class="episode-connect__name">{name}</p>']
    if title:
        lines.append(f'<p class="episode-connect__role">{title}</p>')
    lines.append('<ul class="episode-connect__links">')
    if linkedin:
        display = linkedin.replace("https://www.", "").replace("https://", "").rstrip("/")
        lines.append(f'<li>LinkedIn: <a href="{linkedin}" target="_blank" rel="noopener">{display}</a></li>')
    if email:
        lines.append(f'<li>Email: <a href="mailto:{email}">{email}</a></li>')
    if website:
        href = website if website.startswith("http") else "https://" + website
        display_url = href.replace("https://www.", "").replace("https://", "").replace("http://", "").rstrip("/")
        lines.append(f'<li>Website: <a href="{href}" target="_blank" rel="noopener">{display_url}</a></li>')
    if phone:
        lines.append(f'<li>Phone: {phone}</li>')
    if other:
        lines.append(f'<li>{other}</li>')
    lines.extend(['</ul>', '</div>', '</div>'])

    return '\n'.join(lines) + '\n' + hosts_html


def description_first_para(html_desc: str) -> str:
    """Get plain-text version of the RSS HTML description, first paragraph only."""
    text = re.sub(r'<[^>]+>', ' ', html_desc or '')
    text = re.sub(r'\s+', ' ', text).strip()
    # Cut at 'Today's guest:' if present (we surface that separately)
    text = re.split(r"Today['’]s guest:", text, 1)[0].strip()
    return text


def description_meta(html_desc: str, max_len: int = 158) -> str:
    text = description_first_para(html_desc)
    if len(text) <= max_len:
        return text
    return text[: max_len - 1].rsplit(' ', 1)[0] + '…'


def description_meta_aeo(title: str, sn_overview: list[str], html_desc: str, max_len: int = 160) -> str:
    """AI-citable meta description: prefer show notes overview, then title-derived."""
    if sn_overview:
        text = sn_overview[0]
        text = re.sub(r'\s+', ' ', text).strip()
        if len(text) <= max_len:
            return text
        return text[: max_len - 1].rsplit(' ', 1)[0] + '…'
    return f'Bill Douglas and Drew Hall discuss {title.lower()} on the Peak Property Performance® Podcast.'[: max_len]


def guest_linkedin_from_desc(html_desc: str) -> str:
    m = re.search(r'https?://(?:www\.)?linkedin\.com/in/[^\s"<]+', html_desc or '')
    return m.group(0) if m else ''


def render_episode(ep: dict, all_eps: list[dict], master: dict[int, dict], drive_thumb_overrides: dict[int, dict] | None = None) -> str:
    drive_thumb_overrides = drive_thumb_overrides or {}
    ep_num = ep['rss_ep_num']
    slug = ep['slug']
    title = ep['rss_title']
    pub_iso = ep['rss_pub_iso']
    pub_date = ep['rss_pub_date']
    duration_hhmmss = ep['rss_duration_hhmmss']
    duration_iso = render_iso_duration(duration_hhmmss)
    duration_pretty = pretty_duration(duration_hhmmss)
    mp3_url = ep['rss_mp3_url']
    desc_html = ep['rss_description_html']
    desc_plain = description_first_para(desc_html)
    meta_desc_legacy = description_meta(desc_html)
    page_url = f'{SITE_BASE}/podcast/{slug}'
    canonical_title = f'{title} | Peak Property Performance® Podcast'

    youtube_id = master.get(ep_num, {}).get('youtube_video_id', '')
    youtube_url = master.get(ep_num, {}).get('youtube_url', '')
    canonical_full_title = master.get(ep_num, {}).get('title') or title

    # Asset extraction
    transcript_path = find_transcript(ep_num)
    show_notes_path = find_show_notes(ep_num)

    tr = extract_transcript(transcript_path) if transcript_path else {
        'key_topics': [], 'dialogue': [], 'total_chars': 0, 'paragraph_count': 0
    }
    sn = extract_show_notes(show_notes_path) if show_notes_path else {
        'overview': [], 'what_youll_learn': [], 'key_moments': [],
        'quote_text': '', 'quote_attr': '', 'resources': [], 'tags': [],
    }

    # Thumbnail (Drive-hosted override → local YouTube crop → RSS image)
    page_dir = PODCAST_DIR / slug
    drive_override = drive_thumb_overrides.get(ep_num)
    if drive_override:
        thumb_local_1x1 = drive_thumb_url(drive_override['id_1x1'], 'w800')
        thumb_local_16x9 = drive_thumb_url(drive_override['id_16x9'], 'w1280')
        thumb_abs_16x9 = thumb_local_16x9
    elif youtube_id:
        fetch_thumbnail(youtube_id, page_dir)
        thumb_local_1x1 = './thumbnail.jpg'
        thumb_local_16x9 = './thumbnail-16x9.jpg'
        thumb_abs_16x9 = f'{SITE_BASE}/podcast/{slug}/thumbnail-16x9.jpg'
    else:
        thumb_local_1x1 = ep.get('rss_image') or ''
        thumb_local_16x9 = thumb_local_1x1
        thumb_abs_16x9 = ep.get('rss_image') or ''

    # JSON-LD blocks
    org_jsonld = json.dumps({
        '@context': 'https://schema.org',
        '@type': 'Organization',
        '@id': f'{SITE_BASE}/#organization',
        'name': 'Peak Property Performance®',
        'alternateName': 'PPP',
        'url': SITE_BASE,
        'logo': f'{SITE_BASE}/api/media/file/ppp-logo.webp',
        'parentOrganization': {'@type': 'Organization', 'name': 'OpticWise', 'url': 'https://opticwise.com'},
    }, ensure_ascii=False)
    breadcrumb_jsonld = json.dumps({
        '@context': 'https://schema.org',
        '@type': 'BreadcrumbList',
        '@id': f'{page_url}#breadcrumbs',
        'itemListElement': [
            {'@type': 'ListItem', 'position': 1, 'name': 'Home', 'item': SITE_BASE + '/'},
            {'@type': 'ListItem', 'position': 2, 'name': 'Podcast', 'item': f'{SITE_BASE}/podcast'},
            {'@type': 'ListItem', 'position': 3, 'name': title, 'item': page_url},
        ],
    }, ensure_ascii=False)

    # PodcastEpisode JSON-LD (enriched)
    transcript_text_block = ''
    if tr['dialogue']:
        # Build a single plain-text concatenation for the schema 'transcript' field
        chunks = []
        for it in tr['dialogue']:
            if it['kind'] == 'turn':
                if it.get('speaker'):
                    chunks.append(f'{it["speaker"]}: {it["body"]}')
                else:
                    chunks.append(it['body'])
        transcript_text_block = '\n\n'.join(chunks)

    podcast_episode = {
        '@context': 'https://schema.org',
        '@type': 'PodcastEpisode',
        '@id': f'{page_url}#episode',
        'name': title,
        'url': page_url,
        'datePublished': pub_iso,
        'duration': duration_iso,
        'description': desc_plain,
        'image': thumb_abs_16x9,
        'episodeNumber': ep_num,
        'associatedMedia': {'@type': 'MediaObject', 'contentUrl': mp3_url},
        'partOfSeries': {
            '@type': 'PodcastSeries',
            'name': 'Peak Property Performance®',
            'url': f'{SITE_BASE}/podcast',
        },
        'author': [
            {'@type': 'Person', 'name': 'Bill Douglas', 'sameAs': 'https://www.linkedin.com/in/billdouglas/'},
            {'@type': 'Person', 'name': 'Drew Hall', 'sameAs': 'https://www.linkedin.com/in/drewhall33/'},
        ],
    }
    if transcript_text_block:
        podcast_episode['transcript'] = transcript_text_block
    if youtube_url:
        podcast_episode['video'] = {'@type': 'VideoObject', 'name': title, 'embedUrl': f'https://www.youtube.com/embed/{youtube_id}', 'thumbnailUrl': thumb_abs_16x9, 'uploadDate': pub_iso, 'description': desc_plain, 'contentUrl': youtube_url}
    podcast_episode_jsonld = json.dumps(podcast_episode, ensure_ascii=False)

    # Hero section
    eyebrow = f'Episode {ep_num} · {duration_pretty}'
    if pub_date:
        try:
            d = dt.datetime.fromisoformat(pub_date)
            eyebrow += f' · {d.strftime("%b %-d, %Y")}'
        except ValueError:
            pass

    meta_desc = description_meta_aeo(title, sn.get('overview', []), desc_html)
    show_notes_html = render_show_notes_html(sn)
    transcript_html = _render_transcript_clean(tr) if tr['dialogue'] else ''
    contact_sections_html = _render_contact_sections(slug)
    recent_html = render_recent_episodes(slug, all_eps)

    # YouTube facade (lightweight click-to-play)
    youtube_facade = ''
    if youtube_id:
        youtube_facade = (
            f'<div class="episode-video"><a class="episode-video__poster" '
            f'href="{youtube_url}" target="_blank" rel="noopener" '
            f'aria-label="Watch on YouTube">'
            f'<img src="{thumb_local_16x9}" alt="{h(title)} — watch on YouTube" '
            f'width="1280" height="720" loading="lazy">'
            f'<span class="episode-video__play" aria-hidden="true">▶</span>'
            f'<span class="episode-video__label">Watch on YouTube</span>'
            f'</a></div>'
        )

    audio_player = f'<div class="audio-player"><audio controls preload="metadata" src="{mp3_url}"></audio></div>' if mp3_url else ''

    # Subscribe row
    subscribe_row = (
        '<div class="subscribe-row mt-5">'
        '<span class="subscribe-row__label">Listen on</span>'
        '<a class="subscribe-btn" href="https://open.spotify.com/show/3TLMly7c1TNWeMUyZDVyhQ" target="_blank" rel="noopener">Spotify</a>'
        '<a class="subscribe-btn" href="https://podcasts.apple.com/us/podcast/peak-property-performance/id1817250978" target="_blank" rel="noopener">Apple Podcasts</a>'
        '<a class="subscribe-btn" href="https://www.youtube.com/@PeakPropertyPerformance" target="_blank" rel="noopener">YouTube</a>'
        '<a class="subscribe-btn" href="https://www.iheart.com/podcast/1333-peak-property-performance-290758788/" target="_blank" rel="noopener">iHeart</a>'
        '<a class="subscribe-btn" href="https://anchor.fm/s/1057cecf4/podcast/rss" target="_blank" rel="noopener">RSS Feed</a>'
        '</div>'
    )

    # Assemble
    html_doc = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="preload" as="image" href="../../api/media/file/fast-company-press.webp">
<link rel="preload" as="image" href="{thumb_local_1x1}">
<link rel="stylesheet" href="../../_next/static/css/f3145fbd800cc712.css" data-precedence="next">
<link rel="stylesheet" href="../../public/css/ppp-additions.css">
<link rel="stylesheet" href="../../public/css/cookie-consent.css">
<link rel="icon" type="image/x-icon" href="../../public/favicon.ico">
<link rel="icon" type="image/png" sizes="32x32" href="../../public/favicon-32x32.png">
<link rel="icon" type="image/png" sizes="16x16" href="../../public/favicon-16x16.png">
<link rel="apple-touch-icon" sizes="180x180" href="../../public/apple-touch-icon.png">
<link rel="manifest" href="../../public/site.webmanifest">
<meta name="theme-color" content="#1B3526">
<link rel="canonical" href="{page_url}">
<title>{h(canonical_title)}</title>
<meta name="description" content="{h(meta_desc)}">
<meta property="og:type" content="article">
<meta property="og:title" content="{h(title)} | Peak Property Performance® Podcast">
<meta property="og:description" content="{h(meta_desc)}">
<meta property="og:url" content="{page_url}">
<meta property="og:image" content="{thumb_abs_16x9}">
<meta property="og:site_name" content="Peak Property Performance®">
<meta property="article:published_time" content="{pub_iso}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{h(title)}">
<meta name="twitter:description" content="{h(meta_desc)}">
<meta name="twitter:image" content="{thumb_abs_16x9}">
<script type="application/ld+json">{org_jsonld}</script>
<script type="application/ld+json">{breadcrumb_jsonld}</script>
<script type="application/ld+json">{podcast_episode_jsonld}</script>
</head>
<body>
{NAV_HTML}
<main>
<section class="episode-page__hero">
<div class="container">
<div class="hero__inner">
<div>
<a class="eyebrow" href="../index.html">← All Episodes</a>
<h1 class="hero__heading mt-4">{h(title)}</h1>
<p class="hero__lede mt-3">{h(eyebrow)}</p>
{subscribe_row}
</div>
<div>
<img src="{thumb_local_1x1}" alt="{h(title)}" width="800" height="800" style="border-radius:8px;box-shadow:0 12px 36px rgba(20, 33, 26, 0.40)">
</div>
</div>
</div>
</section>
<section>
<div class="container">
<div class="episode-page__layout">
<article>
{youtube_facade}
{audio_player}
<div class="rich-content">
{show_notes_html}
{contact_sections_html}
{transcript_html}
</div>
</article>
<aside class="episode-page__sidebar">
<div class="aside-card" style="background:var(--bg-dark);color:var(--text-on-dark);border-color:var(--bg-dark)">
<h4 style="color:var(--ppp-paper)">Get the Book.</h4>
<p style="color:rgba(245, 240, 228, 0.78);font-size:var(--fs-body-sm);margin-block:var(--space-3)">The full playbook this conversation is built on.</p>
<a class="btn btn-primary" style="width:100%" href="../../book/index.html">View Retailers</a>
</div>
<div class="aside-card" style="background:var(--ppp-yellow-sun);border-color:var(--ppp-yellow-sun)">
<h4 style="color:var(--ppp-darkest-green)">Run the play on one building.</h4>
<p style="color:var(--ppp-darkest-green);font-size:var(--fs-body-sm);margin-block:var(--space-3)">Request a complimentary PPP Review. We'll run a Data &amp; Digital Infrastructure Audit on one of your buildings and leave you with a one-pager you can act on.</p>
<a class="btn btn-secondary" style="width:100%;color:var(--ppp-darkest-green);border-color:var(--ppp-darkest-green)" href="../../ppp-review/index.html">Request a PPP Review</a>
</div>
{recent_html}
</aside>
</div>
</div>
</section>
{THREE_WAYS_HTML}
</main>
{FOOTER_HTML}
</body>
</html>
'''
    return html_doc


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--ep', type=int, help='Build a single episode by number')
    ap.add_argument('--eps', type=str, help='Comma-separated list of episode numbers')
    ap.add_argument('--dry-run', action='store_true', help='Render but do not write to disk')
    args = ap.parse_args()

    all_eps = load_index()
    master = load_master_csv()
    drive_thumb_overrides = load_drive_thumb_overrides()

    # Filter
    targets = []
    if args.ep is not None:
        targets = [args.ep]
    elif args.eps:
        targets = [int(x.strip()) for x in args.eps.split(',') if x.strip()]
    else:
        targets = sorted({e['rss_ep_num'] for e in all_eps if e.get('rss_ep_num')})

    summary = []
    for ep_num in targets:
        ep = next((e for e in all_eps if e['rss_ep_num'] == ep_num), None)
        if not ep:
            print(f'! ep {ep_num}: not in index')
            continue
        if not ep.get('slug'):
            print(f'! ep {ep_num}: no local slug (needs new page). Skipping.')
            continue
        try:
            doc = render_episode(ep, all_eps, master, drive_thumb_overrides)
        except Exception as e:
            print(f'! ep {ep_num} ({ep["slug"]}): render failed → {e!r}')
            continue
        target = PODCAST_DIR / ep['slug'] / 'index.html'
        if args.dry_run:
            print(f'  ep {ep_num}: would write {len(doc):,} bytes to {target}')
        else:
            target.write_text(doc)
            print(f'✓ ep {ep_num}: wrote {len(doc):,} bytes to {target.relative_to(ROOT)}')
        summary.append({'ep': ep_num, 'slug': ep['slug'], 'bytes': len(doc)})

    print(f'\nDone: {len(summary)} episodes rendered.')


if __name__ == '__main__':
    main()
