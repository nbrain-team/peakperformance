"""Refresh the local Drive asset cache from the master podcast Drive folder.

This is the script that replaces the agent-driven MCP calls + the
user's local Google Drive Desktop sync. It walks the master folder,
finds every per-episode subfolder, and downloads/exports the assets
the build pipeline needs into scripts/podcast/_drive_cache/.

Layout produced:

    scripts/podcast/_drive_cache/
        transcripts/
            PPP Ep 1 - Transcript - Lane Taylor.docx
            PPP Ep 2 - Transcript - Solo episode.docx
            …
        show_notes/
            PPP Ep 1 - Show Notes - Lane Taylor.pdf
            …

It also (re)writes two metadata files in scripts/podcast/:

    _drive_master_listing.json     # ep_num -> folder_id, modifiedTime
    _drive_thumbnails.json         # ep_num -> {id_1x1, id_16x9, source_file}

build_episode_pages.py is taught (separately) to look in _drive_cache/
in addition to the laptop mirror, so this script's output is the
authoritative asset source on Render.

Usage:
    python3 scripts/podcast/refresh_assets.py            # full refresh
    python3 scripts/podcast/refresh_assets.py --eps 34,35
    python3 scripts/podcast/refresh_assets.py --dry-run  # discovery only
"""
from __future__ import annotations
import argparse
import datetime as dt
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from drive_client import (
    DriveClient,
    parse_episode_number,
    find_transcript_file,
    find_show_notes_file,
    discover_thumbnails,
)

SCRIPTS = Path(__file__).resolve().parent
CACHE_DIR = SCRIPTS / '_drive_cache'
TRANSCRIPTS_DIR = CACHE_DIR / 'transcripts'
SHOW_NOTES_DIR = CACHE_DIR / 'show_notes'

MASTER_FOLDER_ID = '1mhA8fDK9uPIn-1IzM-eG_yd5VOfnpWHO'

MASTER_LISTING_PATH = SCRIPTS / '_drive_master_listing.json'
THUMBNAILS_PATH = SCRIPTS / '_drive_thumbnails.json'

DOCX_MIME = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
PDF_MIME = 'application/pdf'
GDOC_MIME = 'application/vnd.google-apps.document'


# ---------------------------------------------------------------------------
# Folder discovery
# ---------------------------------------------------------------------------

def discover_episode_folders(drive: DriveClient) -> dict[int, dict]:
    """Walk the master folder; return ep_num → {folder_id, name, modifiedTime}."""
    out: dict[int, dict] = {}
    for f in drive.list_subfolders(MASTER_FOLDER_ID):
        ep = parse_episode_number(f['name'])
        if ep is None:
            continue
        prev = out.get(ep)
        # If two folders map to the same ep number, keep the most recently
        # modified (covers cases where a stray "Ep 16" folder exists).
        if prev is None or f.get('modifiedTime', '') > prev.get('modifiedTime', ''):
            out[ep] = {
                'folder_id': f['id'],
                'name': f['name'],
                'modifiedTime': f.get('modifiedTime', ''),
            }
    return out


# ---------------------------------------------------------------------------
# Per-episode asset fetch
# ---------------------------------------------------------------------------

def refresh_episode(drive: DriveClient, ep_num: int, folder_id: str, dry_run: bool) -> dict:
    """Pull transcript, show notes, and thumbnail metadata for one ep.

    Returns a summary dict.
    """
    files = drive.list_folder(folder_id)

    summary: dict = {
        'ep': ep_num,
        'folder_id': folder_id,
        'transcript': None,
        'show_notes': None,
        'thumbnails': None,
        'errors': [],
    }

    # Transcript ---------------------------------------------------------
    t = find_transcript_file(files)
    if t:
        suffix = '.docx'
        dest = TRANSCRIPTS_DIR / t['name']
        if not dest.name.lower().endswith('.docx'):
            dest = TRANSCRIPTS_DIR / (dest.stem + suffix)
        try:
            if dry_run:
                summary['transcript'] = {'name': t['name'], 'would_write': str(dest)}
            else:
                if t['mimeType'] == GDOC_MIME:
                    drive.export_doc(t['id'], DOCX_MIME, dest)
                else:
                    drive.download_file(t['id'], dest)
                summary['transcript'] = {'name': t['name'], 'path': str(dest.relative_to(SCRIPTS.parent.parent))}
        except Exception as e:
            summary['errors'].append(f'transcript: {e!r}')

    # Show notes ---------------------------------------------------------
    sn = find_show_notes_file(files)
    if sn:
        suffix = '.pdf'
        dest = SHOW_NOTES_DIR / sn['name']
        if not dest.name.lower().endswith('.pdf'):
            dest = SHOW_NOTES_DIR / (dest.stem + suffix)
        try:
            if dry_run:
                summary['show_notes'] = {'name': sn['name'], 'would_write': str(dest)}
            else:
                if sn['mimeType'] == GDOC_MIME:
                    drive.export_doc(sn['id'], PDF_MIME, dest)
                else:
                    drive.download_file(sn['id'], dest)
                summary['show_notes'] = {'name': sn['name'], 'path': str(dest.relative_to(SCRIPTS.parent.parent))}
        except Exception as e:
            summary['errors'].append(f'show_notes: {e!r}')

    # Thumbnails ---------------------------------------------------------
    thumbs = discover_thumbnails(files, ep_num=ep_num)
    if thumbs:
        summary['thumbnails'] = thumbs

    return summary


# ---------------------------------------------------------------------------
# Metadata-file writing
# ---------------------------------------------------------------------------

def write_master_listing(folders: dict[int, dict]) -> None:
    payload = {
        '_comment': (
            'Auto-refreshed by scripts/podcast/refresh_assets.py. Maps '
            'ep_num to the per-episode Drive folder. Used by '
            'update_podcast.py to detect episodes that exist in Drive '
            'but not yet in the RSS feed (those stay gated).'
        ),
        '_master_folder_id': MASTER_FOLDER_ID,
        '_master_folder_url': f'https://drive.google.com/drive/folders/{MASTER_FOLDER_ID}',
        '_refreshed_at': dt.datetime.utcnow().replace(microsecond=0).isoformat() + 'Z',
        'episodes': {
            str(ep): {'folder_id': info['folder_id'], 'modified': info.get('modifiedTime', '')}
            for ep, info in sorted(folders.items())
        },
    }
    MASTER_LISTING_PATH.write_text(json.dumps(payload, indent=2) + '\n')


def write_thumbnails(thumbs_by_ep: dict[int, dict]) -> None:
    payload = {
        '_comment': (
            'Auto-refreshed by scripts/podcast/refresh_assets.py. For each '
            'episode the script picks the best thumbnail in that folder '
            'using this priority: (1) explicit 1 by 1.png + 16 by 9.png '
            "pair, (2) 'PPP Ep N - YouTube Thumbnail.jpg' (16:9, browser "
            'CSS center-crops to 1:1 on the listing card to show the '
            'guest), (3) any other branded image with "thumbnail" in '
            'the name (largest first). For episodes 1-23 the YouTube '
            'thumbnail is preferred because the older PNGs are just '
            'text-overlay (no guest face) versions.'
        ),
        '_url_template': 'https://drive.google.com/thumbnail?id={id}&sz={size}',
        'episodes': {
            str(ep): thumb for ep, thumb in sorted(thumbs_by_ep.items())
        },
    }
    THUMBNAILS_PATH.write_text(json.dumps(payload, indent=2) + '\n')


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--eps', type=str, help='Comma-separated ep numbers to refresh (default: all)')
    ap.add_argument('--dry-run', action='store_true', help='Discover only; do not download')
    ap.add_argument('--no-write-metadata', action='store_true',
                    help='Skip rewriting _drive_master_listing.json / _drive_thumbnails.json')
    args = ap.parse_args()

    try:
        drive = DriveClient.from_env()
    except RuntimeError as e:
        print(f'! {e}')
        print('  refresh_assets requires GOOGLE_DRIVE_SA_JSON or GOOGLE_DRIVE_SA_FILE.')
        sys.exit(2)

    print(f'→ Discovering episode folders in master Drive folder…')
    folders = discover_episode_folders(drive)
    print(f'  Found {len(folders)} episode folders (eps {min(folders) if folders else "—"}…{max(folders) if folders else "—"})')

    if args.eps:
        wanted = {int(x.strip()) for x in args.eps.split(',') if x.strip()}
        folders = {k: v for k, v in folders.items() if k in wanted}
        print(f'  Filtered to: {sorted(folders)}')

    TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
    SHOW_NOTES_DIR.mkdir(parents=True, exist_ok=True)

    thumbs_by_ep: dict[int, dict] = {}
    for ep in sorted(folders):
        info = folders[ep]
        print(f'→ Ep {ep}: {info["name"]}  ({info["folder_id"]})')
        summary = refresh_episode(drive, ep, info['folder_id'], dry_run=args.dry_run)
        if summary['transcript']:
            print(f'    transcript: {summary["transcript"]["name"]}')
        else:
            print(f'    transcript: NONE')
        if summary['show_notes']:
            print(f'    show notes: {summary["show_notes"]["name"]}')
        else:
            print(f'    show notes: NONE')
        if summary['thumbnails']:
            thumbs_by_ep[ep] = summary['thumbnails']
            print(f'    thumbnails: {summary["thumbnails"]["source_file"]}')
        else:
            print(f'    thumbnails: NONE')
        for err in summary['errors']:
            print(f'    ! {err}')

    if not args.no_write_metadata and not args.eps:
        write_master_listing(folders)
        write_thumbnails(thumbs_by_ep)
        print()
        print(f'✓ Wrote {MASTER_LISTING_PATH.relative_to(SCRIPTS.parent.parent)}')
        print(f'✓ Wrote {THUMBNAILS_PATH.relative_to(SCRIPTS.parent.parent)}')
    elif args.eps and not args.no_write_metadata:
        # Partial refresh: merge into existing files instead of clobbering.
        if MASTER_LISTING_PATH.exists():
            existing = json.loads(MASTER_LISTING_PATH.read_text())
            for ep, info in folders.items():
                existing['episodes'][str(ep)] = {'folder_id': info['folder_id'], 'modified': info.get('modifiedTime', '')}
            existing['_refreshed_at'] = dt.datetime.utcnow().replace(microsecond=0).isoformat() + 'Z'
            MASTER_LISTING_PATH.write_text(json.dumps(existing, indent=2) + '\n')
            print(f'✓ Merged into {MASTER_LISTING_PATH.relative_to(SCRIPTS.parent.parent)}')
        if THUMBNAILS_PATH.exists() and thumbs_by_ep:
            existing = json.loads(THUMBNAILS_PATH.read_text())
            for ep, t in thumbs_by_ep.items():
                existing['episodes'][str(ep)] = t
            THUMBNAILS_PATH.write_text(json.dumps(existing, indent=2) + '\n')
            print(f'✓ Merged into {THUMBNAILS_PATH.relative_to(SCRIPTS.parent.parent)}')


if __name__ == '__main__':
    main()
