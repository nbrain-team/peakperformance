"""RSS-triggered podcast page update.

This is the entry point the user asked for (2026-05-18):

> Going forward, the site should use the RSS feed to know when new episodes
> are posted, then resort to the Google folder every time and look for the
> episode folder to see the assets, and then use those assets. If anything
> else is missing, use the RSS feed.

> Episode 36: Assets are in the folder, but it's not in the RSS feed, so
> don't post it yet.

The RSS feed is the GATE: an episode is only published when Anchor's RSS
shows it. Even if assets are sitting in Drive (like Ep 36), it stays off
the site until RSS lists it. This keeps the public site in sync with the
podcast feed and prevents pre-announcing episodes that aren't live yet.

WORKFLOW
========
Each run:

  1. Refresh the Anchor RSS feed (scripts/podcast/_anchor_rss.xml).
  2. Rebuild scripts/podcast/_episode_index.json from RSS + master-episodes.csv.
  3. For every published episode in RSS:
       a. Ensure a local podcast/<slug>/ directory exists.
       b. Check that transcript + show-notes assets are present in the
          local Drive mirror (~/My Drive/AA DOWNLOADS - WD rev 2025-Apr/
          PPP-Podcast-Deliverables/{transcripts,show_notes}/).
       c. If anything is missing, print a "FETCH FROM DRIVE" instruction
          listing the ep_num, drive_folder_id, and file_id of each asset
          that needs to be pulled via the gdrive MCP. The agent then runs
          save_drive_asset.py (or unzips an existing backup) to land it
          in the local mirror, and this script is re-run.
       d. If assets are present, render the page via build_episode_pages.py.
  4. Episodes in master-episodes.csv but NOT in the RSS feed (e.g. Ep 36
     before it's published) are SKIPPED with a one-line note. Their assets
     are kept ready in Drive but the page stays unpublished.

USAGE
=====
    # full pipeline: refresh RSS, build everything that's ready, report gaps
    python3 scripts/podcast/update_podcast.py

    # just report what's pending (no build, no RSS refresh)
    python3 scripts/podcast/update_podcast.py --report-only

    # skip the RSS refresh (use cached _anchor_rss.xml)
    python3 scripts/podcast/update_podcast.py --no-refresh

    # force re-render every page (default: skip pages that already exist
    # and were modified after their source assets)
    python3 scripts/podcast/update_podcast.py --force
"""
from __future__ import annotations
import argparse
import csv
import json
import re
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path
from xml.etree import ElementTree as ET

SCRIPTS = Path(__file__).resolve().parent
ROOT = SCRIPTS.parent.parent
PODCAST_DIR = ROOT / 'podcast'
RSS_PATH = SCRIPTS / '_anchor_rss.xml'
INDEX_PATH = SCRIPTS / '_episode_index.json'

# Two possible Drive-asset roots: the laptop's Google Drive desktop sync
# mirror (preferred locally), and the Render-side cache populated by
# refresh_assets.py. Either or both may exist; functions below try them
# in order.
DELIV_LAPTOP = Path('/Users/billdouglas/My Drive/AA DOWNLOADS - WD rev 2025-Apr/PPP-Podcast-Deliverables')
DELIV_CACHE = SCRIPTS / '_drive_cache'
DELIV_SEARCH_PATHS = [DELIV_LAPTOP, DELIV_CACHE]


def _first_existing(rel_path: str) -> Path | None:
    for base in DELIV_SEARCH_PATHS:
        p = base / rel_path
        if p.exists():
            return p
    return None


MASTER_CSV = _first_existing('master-episodes.csv')
BATCH_CSV = _first_existing('batch-deliverables-summary.csv')
DRIVE_LISTING_PATH = SCRIPTS / '_drive_master_listing.json'

RSS_URL = 'https://anchor.fm/s/1057cecf4/podcast/rss'
DRIVE_ROOT_FOLDER_ID = '1mhA8fDK9uPIn-1IzM-eG_yd5VOfnpWHO'


# ---------------------------------------------------------------------------
# Step 0: refresh Drive assets (transcripts, show notes, thumbnail metadata)
# ---------------------------------------------------------------------------

def refresh_drive_assets(verbose: bool = True) -> bool:
    """Run refresh_assets.py if a Drive service account is available.
    Returns True if the refresh ran, False if no credentials (we then
    fall back to whatever's already in DELIV_LAPTOP / DELIV_CACHE)."""
    import os
    has_creds = (
        os.environ.get('GOOGLE_DRIVE_SA_JSON')
        or os.environ.get('GOOGLE_DRIVE_SA_FILE')
        or (Path.home() / '.config' / 'ppp' / 'drive-sa.json').exists()
    )
    if not has_creds:
        if verbose:
            print('[0/5] No Drive service account configured — skipping Drive refresh.')
            print('      (Will use whatever is already in the local mirror / cache.)')
        return False
    if verbose:
        print('[0/5] Refreshing Drive assets (transcripts, show notes, thumbnails)…')
    out = subprocess.run(
        [sys.executable, str(SCRIPTS / 'refresh_assets.py')],
        capture_output=True, text=True,
    )
    if verbose:
        for line in out.stdout.splitlines():
            if line.strip():
                print(f'      {line.strip()}')
        if out.returncode != 0:
            print(f'      ! exit {out.returncode}')
            print(out.stderr)
    return out.returncode == 0


# ---------------------------------------------------------------------------
# Step 1: refresh RSS feed
# ---------------------------------------------------------------------------

def refresh_rss(verbose: bool = True) -> None:
    if verbose:
        print(f'[1/5] Fetching {RSS_URL} → {RSS_PATH.relative_to(ROOT)}')
    req = urllib.request.Request(RSS_URL, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = resp.read()
    RSS_PATH.write_bytes(data)
    if verbose:
        print(f'      ✓ {len(data):,} bytes')


# ---------------------------------------------------------------------------
# Step 2: rebuild episode index
# ---------------------------------------------------------------------------

def rebuild_index(verbose: bool = True) -> None:
    if verbose:
        print(f'[2/5] Rebuilding {INDEX_PATH.relative_to(ROOT)}')
    out = subprocess.run(
        [sys.executable, str(SCRIPTS / 'build_episode_index.py')],
        check=True, capture_output=True, text=True,
    )
    if verbose:
        # Just show summary line
        for line in out.stdout.splitlines():
            if 'episodes' in line.lower() or 'wrote' in line.lower():
                print(f'      {line.strip()}')


# ---------------------------------------------------------------------------
# Step 3: gap audit (which RSS episodes need new pages and/or Drive assets)
# ---------------------------------------------------------------------------

def slugify(title: str, max_len: int = 80) -> str:
    title = re.sub(r'^Ep[\.\s]*\d+\s*[:\-]?\s*', '', title, flags=re.I).strip()
    s = title.lower()
    s = re.sub(r"['']", '', s)
    s = re.sub(r'[^a-z0-9]+', '-', s)
    s = s.strip('-')
    if len(s) <= max_len:
        return s
    cut = s[:max_len]
    if '-' in cut:
        cut = cut.rsplit('-', 1)[0]
    return cut.strip('-')


def load_master() -> dict[int, dict]:
    out: dict[int, dict] = {}
    if not MASTER_CSV:
        return out
    with MASTER_CSV.open() as f:
        for row in csv.DictReader(f):
            try:
                out[int(row['ep_num'])] = row
            except (KeyError, ValueError):
                continue
    return out


def load_batch() -> dict[int, dict]:
    """Map ep_num → {guest, drive_folder_id, transcript_drive_file_id, ...}.
    The batch deliverables CSV records the actual Drive file IDs for assets."""
    if not BATCH_CSV or not BATCH_CSV.exists():
        return {}
    out: dict[int, dict] = {}
    with BATCH_CSV.open() as f:
        for row in csv.DictReader(f):
            try:
                n = int(row.get('ep_num') or row.get('episode') or 0)
            except ValueError:
                continue
            if n:
                out[n] = row
    return out


def find_transcript(ep_num: int) -> Path | None:
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


def audit(verbose: bool = True):
    """Return (ready, gated, needs_assets, new_slugs) lists describing the state
    of each RSS episode."""
    data = json.loads(INDEX_PATH.read_text())
    eps = data['episodes']
    master = load_master()

    rss_eps = [e for e in eps if e.get('rss_ep_num') is not None]
    rss_ep_nums = {e['rss_ep_num'] for e in rss_eps}

    ready: list[dict] = []     # ep is in RSS, has page (or will create), assets present
    needs_assets: list[dict] = []  # ep is in RSS, page exists, but transcript/show notes missing
    new_slugs: list[dict] = [] # ep is in RSS, no local page yet — we'll create it
    gated: list[dict] = []     # in master CSV but not RSS (e.g. Ep 36) — skip

    for ep in rss_eps:
        n = ep['rss_ep_num']
        slug = ep.get('slug')
        if not slug:
            new_slug = slugify(ep['rss_title'])
            new_slugs.append({'ep_num': n, 'slug': new_slug, 'title': ep['rss_title']})
            slug = new_slug
        transcript = find_transcript(n)
        show_notes = find_show_notes(n)
        missing = []
        if not transcript:
            missing.append('transcript')
        if not show_notes:
            missing.append('show_notes')
        info = {
            'ep_num': n, 'slug': slug, 'title': ep['rss_title'],
            'transcript': transcript, 'show_notes': show_notes,
            'master': master.get(n, {}),
        }
        if missing:
            info['missing'] = missing
            needs_assets.append(info)
        else:
            ready.append(info)

    # Gated: episode subfolder exists in the master Drive folder, but the
    # episode isn't in RSS yet. Source of truth is the cached Drive listing
    # (refreshed via the gdrive MCP — see _drive_master_listing.json).
    drive_listing = {}
    if DRIVE_LISTING_PATH.exists():
        try:
            drive_listing = json.loads(DRIVE_LISTING_PATH.read_text()).get('episodes', {})
        except Exception:
            drive_listing = {}
    for ep_str, info in drive_listing.items():
        try:
            n = int(ep_str)
        except ValueError:
            continue
        if n not in rss_ep_nums:
            title = master.get(n, {}).get('title', '(title unknown — not in master CSV yet)')
            gated.append({
                'ep_num': n,
                'title': title,
                'drive_folder_id': info.get('folder_id', ''),
            })

    if verbose:
        print(f'[3/5] Audit:')
        print(f'      RSS episodes:       {len(rss_eps)}')
        print(f'      Ready to build:     {len(ready)}')
        print(f'      Need new local page:{len(new_slugs)}')
        print(f'      Missing assets:     {len(needs_assets)}')
        print(f'      Gated (not in RSS): {len(gated)}')
    return ready, needs_assets, new_slugs, gated


# ---------------------------------------------------------------------------
# Step 4: build pages + report gaps
# ---------------------------------------------------------------------------

def ensure_page_dir(slug: str) -> Path:
    p = PODCAST_DIR / slug
    p.mkdir(parents=True, exist_ok=True)
    return p


def re_register_new_slugs(new_slugs: list[dict]) -> None:
    """Create page directories with a minimal PodcastEpisode JSON-LD placeholder
    so the index rebuild can join them to the RSS feed by mp3 URL."""
    if not new_slugs:
        return
    # Need the RSS data to look up the mp3 URL for the placeholder
    data = json.loads(INDEX_PATH.read_text())
    by_ep = {e['rss_ep_num']: e for e in data['episodes'] if e.get('rss_ep_num') is not None}
    for entry in new_slugs:
        d = ensure_page_dir(entry['slug'])
        page = d / 'index.html'
        if page.exists() and page.stat().st_size > 5000:
            continue  # real page already there
        rss = by_ep.get(entry['ep_num'], {})
        # Minimal placeholder with the JSON-LD the index-builder reads
        ld = {
            '@type': 'PodcastEpisode',
            'name': rss.get('rss_title', entry['title']),
            'episodeNumber': entry['ep_num'],
            'datePublished': rss.get('rss_pub_iso', ''),
            'duration': rss.get('rss_duration_iso', ''),
            'associatedMedia': {'contentUrl': rss.get('rss_mp3_url', '')},
        }
        page.write_text(
            '<!DOCTYPE html><html><head>'
            f'<title>Ep {entry["ep_num"]} placeholder</title>'
            f'<script type="application/ld+json">{json.dumps(ld)}</script>'
            '</head><body><p>Building&hellip;</p></body></html>'
        )
    rebuild_index(verbose=False)


def build_pages(ep_nums: list[int], verbose: bool = True) -> None:
    if not ep_nums:
        if verbose:
            print('[4/5] Nothing to build.')
        return
    if verbose:
        print(f'[4/5] Building {len(ep_nums)} pages: {ep_nums}')
    eps_arg = ','.join(str(n) for n in ep_nums)
    out = subprocess.run(
        [sys.executable, str(SCRIPTS / 'build_episode_pages.py'), '--eps', eps_arg],
        capture_output=True, text=True,
    )
    if verbose:
        for line in out.stdout.splitlines():
            if line.strip():
                print(f'      {line.strip()}')
        if out.returncode != 0:
            print(f'      ! exit {out.returncode}')
            print(out.stderr)


def print_drive_instructions(needs_assets: list[dict], verbose: bool = True) -> None:
    """Print the MCP fetch instructions for assets the agent needs to pull
    from Drive."""
    if not needs_assets:
        return
    print()
    print('=== Episodes with assets missing from the local Drive mirror ===')
    print('Run: agent fetches each file via gdrive MCP read_file, then saves')
    print('via scripts/podcast/save_drive_asset.py.')
    print()
    for info in needs_assets:
        n = info['ep_num']
        master = info['master']
        folder_url = master.get('drive_folder_url', '<unknown>')
        print(f'  Ep {n} ({info["slug"]}):')
        print(f'    Drive folder: {folder_url}')
        print(f'    Missing:      {", ".join(info["missing"])}')
        print()


def print_gated(gated: list[dict], verbose: bool = True) -> None:
    if not gated:
        return
    print()
    print('=== Gated (assets ready but episode not in RSS yet) ===')
    for info in gated:
        print(f'  Ep {info["ep_num"]}: {info["title"]}')
        print(f'    Drive folder: {info["drive_folder_id"]}')
    print('  (These pages will publish automatically once RSS lists them.)')


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--no-refresh', action='store_true', help='Skip RSS fetch (use cache)')
    ap.add_argument('--report-only', action='store_true', help="Don't build anything, just report")
    ap.add_argument('--force', action='store_true', help='Re-render every ready page')
    args = ap.parse_args()

    if not args.no_refresh and not args.report_only:
        refresh_rss()

    rebuild_index()
    ready, needs_assets, new_slugs, gated = audit()

    # Allocate page directories for new slugs and re-audit so 'ready' picks them up
    if new_slugs and not args.report_only:
        print(f'      Allocating page directories for: {[e["ep_num"] for e in new_slugs]}')
        re_register_new_slugs(new_slugs)
        ready, needs_assets, new_slugs, gated = audit(verbose=False)

    if not args.report_only:
        # Build everything that's ready
        ready_nums = [info['ep_num'] for info in ready]
        if args.force:
            build_pages(ready_nums)
        else:
            # Build only pages whose source assets are newer than the page
            to_build = []
            for info in ready:
                page = PODCAST_DIR / info['slug'] / 'index.html'
                # Heuristic: real episode pages are ≥ 40KB (hero + show notes
                # + transcript). Anything smaller is a stub or an earlier
                # render that ran before the assets were available.
                if not page.exists() or page.stat().st_size < 40000:
                    to_build.append(info['ep_num'])
                    continue
                page_mt = page.stat().st_mtime
                src_mt = max(
                    info['transcript'].stat().st_mtime if info['transcript'] else 0,
                    info['show_notes'].stat().st_mtime if info['show_notes'] else 0,
                )
                if src_mt > page_mt:
                    to_build.append(info['ep_num'])
            build_pages(to_build)

    print_drive_instructions(needs_assets)
    print_gated(gated)

    if not args.report_only:
        print()
        print('Done.')


if __name__ == '__main__':
    main()
