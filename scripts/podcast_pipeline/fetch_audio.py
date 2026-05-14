"""Download canonical Audioversion.mp3 for each episode that needs a transcript.

Outputs land in scripts/podcast_pipeline/work/audio/PPP-Episode-NN.mp3
(gitignored). Read-only Drive scope is sufficient.

Usage:
  python -m scripts.podcast_pipeline.fetch_audio          # all that need it
  python -m scripts.podcast_pipeline.fetch_audio 12 13    # specific episodes
"""

from __future__ import annotations

import sys
from pathlib import Path

from .drive_client import download_file, drive_service, find_audio_file
from .episodes import episodes_needing_transcripts, load_episodes

WORK_DIR = Path(__file__).resolve().parent / "work" / "audio"


def fetch(episode_numbers: list[int] | None = None) -> list[Path]:
    eps = load_episodes()
    if episode_numbers:
        wanted = set(episode_numbers)
        targets = [e for e in eps if e.number in wanted]
    else:
        targets = episodes_needing_transcripts()
    if not targets:
        print("Nothing to fetch.")
        return []

    service = drive_service(write=False)
    out: list[Path] = []
    for ep in targets:
        local = WORK_DIR / f"PPP-Episode-{ep.padded}.mp3"
        if local.is_file() and local.stat().st_size > 0:
            print(f"[skip] Ep {ep.padded} already downloaded ({local.name})")
            out.append(local)
            continue
        f = find_audio_file(service, ep.folder_id)
        if not f:
            print(f"[miss] Ep {ep.padded} — no MP3 in {ep.folder_name!r}")
            continue
        size_mb = int(f.get("size") or 0) / 1_000_000
        print(f"[get ] Ep {ep.padded} <- {f['name']} ({size_mb:.1f} MB)")
        download_file(service, f["id"], local)
        out.append(local)
    return out


def _parse_args(argv: list[str]) -> list[int]:
    nums: list[int] = []
    for a in argv:
        try:
            nums.append(int(a))
        except ValueError:
            pass
    return nums


if __name__ == "__main__":
    fetch(_parse_args(sys.argv[1:]))
