"""Decode a base64 blob from the gdrive MCP and write it into the right
location in the local podcast mirror.

Usage (interactive, agent-driven):

  cat my_b64_blob.txt | python3 scripts/podcast/save_drive_asset.py \
      --ep 25 --kind transcript --guest "Tadros Abdelmalek"

Asset locations follow the conventions of the locally-synced mirror:
  transcripts/PPP Ep {N} - Transcript - {guest}.docx
  show_notes/PPP Ep {N} - Show Notes - {guest}.pdf

Thumbnails go directly into the per-episode page directory:
  podcast/{slug}/thumbnail-{kind}.{ext}
"""
from __future__ import annotations
import argparse
import base64
import sys
from pathlib import Path

DELIV = Path('/Users/billdouglas/My Drive/AA DOWNLOADS - WD rev 2025-Apr/PPP-Podcast-Deliverables')


def target_path(ep: int, kind: str, guest: str | None, slug: str | None, ext: str | None) -> Path:
    if kind == 'transcript':
        assert guest, '--guest is required for transcripts'
        return DELIV / 'transcripts' / f'PPP Ep {ep} - Transcript - {guest}.docx'
    if kind == 'show_notes':
        assert guest, '--guest is required for show_notes'
        return DELIV / 'show_notes' / f'PPP Ep {ep} - Show Notes - {guest}.pdf'
    if kind == 'thumbnail-1x1':
        assert slug, '--slug is required for thumbnails'
        ext = ext or 'png'
        return Path('podcast') / slug / f'thumbnail.{ext}'
    if kind == 'thumbnail-16x9':
        assert slug, '--slug is required for thumbnails'
        ext = ext or 'jpg'
        return Path('podcast') / slug / f'thumbnail-16x9.{ext}'
    raise ValueError(f'Unknown kind: {kind!r}')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--ep', type=int, required=True)
    ap.add_argument('--kind', required=True,
                    choices=['transcript', 'show_notes', 'thumbnail-1x1', 'thumbnail-16x9'])
    ap.add_argument('--guest', default=None,
                    help='Guest name (for transcripts/show_notes filenames)')
    ap.add_argument('--slug', default=None,
                    help='Episode slug (for thumbnails)')
    ap.add_argument('--ext', default=None,
                    help='File extension override for thumbnails')
    ap.add_argument('--b64-file', default=None,
                    help='Read base64 from this file (otherwise stdin)')
    args = ap.parse_args()

    if args.b64_file:
        b64 = Path(args.b64_file).read_text()
    else:
        b64 = sys.stdin.read()
    b64 = ''.join(b64.split())  # strip whitespace/newlines
    blob = base64.b64decode(b64)

    dest = target_path(args.ep, args.kind, args.guest, args.slug, args.ext)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(blob)
    print(f'✓ Wrote {len(blob):,} bytes to {dest}')


if __name__ == '__main__':
    main()
