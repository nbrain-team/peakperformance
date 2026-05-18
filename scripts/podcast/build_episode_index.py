"""Build a single authoritative episode index by joining 3 sources:

  1. _anchor_rss.xml             (canonical title, description, mp3, pubDate, duration, episode#)
  2. thumbnail-manifest.csv      (ep_num → YouTube video id + Drive folder id)
  3. existing podcast/<slug>/    (local slug + previously-known episodeNumber)

Output: scripts/podcast/_episode_index.json
"""
from __future__ import annotations
import csv
import datetime as dt
import json
import os
import re
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

SCRIPTS = Path(__file__).resolve().parent
ROOT = SCRIPTS.parent.parent
RSS_PATH = SCRIPTS / '_anchor_rss.xml'
MANIFEST_PATH = Path('/Users/billdouglas/My Drive/AA DOWNLOADS - WD rev 2025-Apr/PPP-Podcast-Deliverables/thumbnail-manifest.csv')
PODCAST_DIR = ROOT / 'podcast'

NS = {
    'itunes': 'http://www.itunes.com/dtds/podcast-1.0.dtd',
    'content': 'http://purl.org/rss/1.0/modules/content/',
    'dc': 'http://purl.org/dc/elements/1.1/',
}


def parse_rss() -> list[dict]:
    tree = ET.parse(RSS_PATH)
    root = tree.getroot()
    channel = root.find('channel')
    eps = []
    for item in channel.findall('item'):
        title_raw = (item.findtext('title') or '').strip()
        # Prefer the title-parsed episode number — Anchor's <itunes:episode> tag has
        # known bugs (Ep 3 → 4, Ep 17 → 19) that we don't want to propagate.
        m = re.match(r'^Ep[\.\s]*\s*(\d+)\s*[:\-]?\s*(.*)$', title_raw, re.I)
        if m:
            ep_num = int(m.group(1))
            clean_title = m.group(2).strip()
        else:
            ep_num = None
            clean_title = title_raw
        if ep_num is None:
            ep_num_itunes = item.findtext('itunes:episode', namespaces=NS)
            if ep_num_itunes and ep_num_itunes.strip().isdigit():
                ep_num = int(ep_num_itunes)
        desc = (item.findtext('description') or '').strip()
        pub = item.findtext('pubDate') or ''
        try:
            pub_dt = dt.datetime.strptime(pub, '%a, %d %b %Y %H:%M:%S %Z')
        except ValueError:
            pub_dt = dt.datetime.strptime(pub.rsplit(' ', 1)[0], '%a, %d %b %Y %H:%M:%S')
        enc = item.find('enclosure')
        mp3 = enc.get('url') if enc is not None else ''
        dur = item.findtext('itunes:duration', namespaces=NS) or ''
        img_el = item.find('itunes:image', namespaces=NS)
        img = img_el.get('href') if img_el is not None else ''
        guid = item.findtext('guid') or ''
        eps.append({
            'rss_ep_num': ep_num,
            'rss_title_raw': title_raw,
            'rss_title': clean_title,
            'rss_description_html': desc,
            'rss_pub_iso': pub_dt.replace(tzinfo=dt.timezone.utc).isoformat(),
            'rss_pub_date': pub_dt.date().isoformat(),
            'rss_mp3_url': mp3,
            'rss_duration_hhmmss': dur,
            'rss_image': img,
            'rss_guid': guid,
        })
    eps.sort(key=lambda e: (e['rss_ep_num'] if e['rss_ep_num'] is not None else 999))
    return eps


def parse_manifest() -> dict[int, dict]:
    out: dict[int, dict] = {}
    with MANIFEST_PATH.open() as f:
        rdr = csv.DictReader(f)
        for row in rdr:
            n = int(row['ep_num'])
            drive_folder_id = row['drive_folder_url'].rstrip('/').rsplit('/', 1)[-1]
            out[n] = {
                'drive_folder_id': drive_folder_id,
                'drive_folder_url': row['drive_folder_url'],
                'youtube_video_id': row['youtube_video_id'],
                'youtube_url': row['youtube_url'],
                'youtube_thumb_maxres': row['thumbnail_url_maxres'],
                'youtube_thumb_hq': row['thumbnail_url_hq'],
            }
    return out


def parse_local_slugs() -> list[dict]:
    out = []
    for slug in sorted(os.listdir(PODCAST_DIR)):
        if slug == 'index.html':
            continue
        page = PODCAST_DIR / slug / 'index.html'
        if not page.is_file():
            continue
        s = page.read_text()
        m = re.search(r'<script type="application/ld\+json">(\{[^<]*"@type": "PodcastEpisode"[^<]*\})</script>', s)
        title = ep_num = date = duration = mp3 = ''
        if m:
            try:
                data = json.loads(m.group(1))
                title = data.get('name', '')
                ep_num = data.get('episodeNumber')
                date = (data.get('datePublished') or '')[:10]
                duration = data.get('duration', '')
                am = data.get('associatedMedia') or {}
                mp3 = am.get('contentUrl', '')
            except Exception:
                pass
        out.append({
            'slug': slug,
            'local_old_ep_num': ep_num,
            'local_title': title,
            'local_date': date,
            'local_duration': duration,
            'local_mp3_url': mp3,
        })
    return out


def join(eps_rss, mani, locals_):
    # match RSS ↔ local by mp3 URL or pubDate; then attach manifest by ep_num
    by_mp3 = {l['local_mp3_url']: l for l in locals_ if l['local_mp3_url']}
    by_date = {}
    for l in locals_:
        if l['local_date']:
            by_date.setdefault(l['local_date'], []).append(l)

    used_slugs = set()
    rows = []
    for ep in eps_rss:
        local = by_mp3.get(ep['rss_mp3_url'])
        if not local:
            # date fallback
            cands = by_date.get(ep['rss_pub_date'], [])
            if len(cands) == 1:
                local = cands[0]
            elif cands:
                # title-similarity fallback among same-date candidates
                want = re.sub(r'[^a-z0-9]+', '', ep['rss_title'].lower())[:40]
                best = max(cands, key=lambda c: sum(
                    1 for w in want if w in re.sub(r'[^a-z0-9]+', '', (c['local_title'] or '').lower())
                ))
                local = best
        row = {**ep}
        if local:
            row['slug'] = local['slug']
            row['local_old_ep_num'] = local['local_old_ep_num']
            row['local_title'] = local['local_title']
            row['local_date'] = local['local_date']
            row['local_duration'] = local['local_duration']
            used_slugs.add(local['slug'])
        else:
            row['slug'] = None
            row['local_old_ep_num'] = None
            row['local_title'] = None
            row['local_date'] = None
            row['local_duration'] = None
        if ep['rss_ep_num'] and ep['rss_ep_num'] in mani:
            row.update(mani[ep['rss_ep_num']])
        rows.append(row)

    # also report locals that did not match any RSS item (trailer + anything orphaned)
    orphans = [l for l in locals_ if l['slug'] not in used_slugs]
    return rows, orphans


def main():
    rss = parse_rss()
    mani = parse_manifest()
    locals_ = parse_local_slugs()
    rows, orphans = join(rss, mani, locals_)

    out = {
        'episodes': rows,
        'local_orphans': orphans,
        'generated_at': dt.datetime.utcnow().isoformat() + 'Z',
    }
    (SCRIPTS / '_episode_index.json').write_text(json.dumps(out, indent=2))

    print(f'\nRSS items: {len(rss)}')
    print(f'Manifest entries: {len(mani)}')
    print(f'Local pages: {len(locals_)}')
    print(f'Joined episodes: {len(rows)}')
    print(f'Unmatched local pages (expected: trailer):', [o["slug"] for o in orphans])

    print(f'\n{"ep":>3}  {"date":<10}  {"slug":<70}  {"oldEp":<5}  drive_folder_id')
    print('-' * 130)
    for r in rows:
        ep_display = str(r["rss_ep_num"]) if r["rss_ep_num"] is not None else 'TRL'
        old_display = str(r["local_old_ep_num"]) if r["local_old_ep_num"] is not None else '-'
        slug_display = r["slug"] or '(NO LOCAL PAGE)'
        print(
            f'{ep_display:>3}  {r["rss_pub_date"]:<10}  '
            f'{slug_display:<70}  '
            f'{old_display:<5}  '
            f'{r.get("drive_folder_id", "")}'
        )


if __name__ == '__main__':
    main()
