"""Publish OpticWise Insights blog posts for newly built PPP episodes.

Called from update_podcast.py after episode pages are built. For each
episode that has a page but no corresponding OW Insights post, runs
the generate-ppp-blog-posts.ts script (in the opticwise repo) to
create and publish the blog post.

This script is a bridge: it calls the Node.js generation script from
the Python pipeline, passing the episode numbers that need posts.

Usage:
    python3 scripts/podcast/publish_ow_insights.py --eps 1,2,3
    python3 scripts/podcast/publish_ow_insights.py --all-missing

Requires OPENAI_API_KEY in the environment for content generation.
"""
from __future__ import annotations
import argparse
import json
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
ROOT = SCRIPTS.parent.parent
INDEX_PATH = SCRIPTS / '_episode_index.json'
PODCAST_DIR = ROOT / 'podcast'

OW_REPO = Path.home() / 'My Drive' / 'Cursor' / 'OWnet' / 'opticwise'
OW_SCRIPT = OW_REPO / 'ow' / 'scripts' / 'generate-ppp-blog-posts.ts'
TSX_BIN = OW_REPO / 'ow' / 'node_modules' / '.bin' / 'tsx'
OW_HTML = Path.home() / 'My Drive' / 'Cursor' / 'opticwise-html'


def find_missing_posts() -> list[int]:
    """Return episode numbers that have a PPP page but no OW Insights post."""
    if not INDEX_PATH.exists():
        return []
    idx = json.loads(INDEX_PATH.read_text())
    missing = []
    for ep in idx['episodes']:
        num = ep.get('rss_ep_num')
        if not num or num < 1:
            continue
        slug = ep.get('slug')
        if not slug:
            continue
        page = PODCAST_DIR / slug / 'index.html'
        if not page.exists() or page.stat().st_size < 40000:
            continue
        ow_post = OW_HTML / 'insights' / f'ppp-{slug}' / 'index.html'
        if not ow_post.exists():
            missing.append(num)
    return sorted(missing)


def run_generate(ep_nums: list[int]) -> bool:
    """Run the OW generate script for the given episodes."""
    if not TSX_BIN.exists():
        print(f'  ERROR: tsx not found at {TSX_BIN}')
        print(f'  Run "cd {OW_REPO / "ow"} && npm install" first.')
        return False
    if not OW_SCRIPT.exists():
        print(f'  ERROR: Generation script not found at {OW_SCRIPT}')
        return False

    eps_str = ','.join(str(n) for n in ep_nums)
    print(f'  Generating OW Insights posts for episodes: {eps_str}')

    result = subprocess.run(
        [str(TSX_BIN), str(OW_SCRIPT), '--generate', '--episodes', eps_str],
        capture_output=True, text=True,
        cwd=str(OW_REPO / 'ow'),
    )
    for line in result.stdout.splitlines():
        if line.strip():
            print(f'    {line.strip()}')
    if result.returncode != 0:
        print(f'  ! Generate failed (exit {result.returncode})')
        if result.stderr:
            print(result.stderr[:500])
        return False
    return True


def run_publish(ep_nums: list[int]) -> bool:
    """Run the OW publish script for the given episodes."""
    print(f'  Publishing OW Insights posts for episodes: {",".join(str(n) for n in ep_nums)}')

    result = subprocess.run(
        [str(TSX_BIN), str(OW_SCRIPT), '--publish', '--episodes',
         ','.join(str(n) for n in ep_nums)],
        capture_output=True, text=True,
        cwd=str(OW_REPO / 'ow'),
    )
    for line in result.stdout.splitlines():
        if line.strip():
            print(f'    {line.strip()}')
    if result.returncode != 0:
        print(f'  ! Publish failed (exit {result.returncode})')
        if result.stderr:
            print(result.stderr[:500])
        return False
    return True


def main():
    ap = argparse.ArgumentParser()
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument('--eps', type=str, help='Comma-separated episode numbers')
    group.add_argument('--all-missing', action='store_true',
                       help='Generate posts for all episodes missing an OW post')
    ap.add_argument('--generate-only', action='store_true',
                    help='Generate content JSON only; skip publish')
    args = ap.parse_args()

    if args.all_missing:
        ep_nums = find_missing_posts()
        if not ep_nums:
            print('[OW Insights] All episodes already have Insights posts.')
            return
        print(f'[OW Insights] Found {len(ep_nums)} episodes without Insights posts: {ep_nums}')
    else:
        ep_nums = [int(n) for n in args.eps.split(',') if n.strip()]

    if not ep_nums:
        print('[OW Insights] No episodes to process.')
        return

    ok = run_generate(ep_nums)
    if not ok:
        return

    if not args.generate_only:
        run_publish(ep_nums)

    print('[OW Insights] Done.')


if __name__ == '__main__':
    main()
