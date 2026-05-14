"""End-to-end runner: fetch -> transcribe -> draft show notes -> upload.

Each step is idempotent; re-running only does work for episodes that don't
already have outputs in the right place. The upload step is skipped
automatically if no Google credentials are configured.

Usage:
  python -m scripts.podcast_pipeline.run_all          # all episodes flagged in audit
  python -m scripts.podcast_pipeline.run_all 12 13    # specific episodes
  python -m scripts.podcast_pipeline.run_all --no-upload
"""

from __future__ import annotations

import os
import sys

from . import draft_shownotes, fetch_audio, transcribe, upload_to_drive


def _parse(argv: list[str]) -> tuple[list[int], bool]:
    do_upload = "--no-upload" not in argv
    nums: list[int] = []
    for a in argv:
        if a.startswith("--"):
            continue
        try:
            nums.append(int(a))
        except ValueError:
            pass
    return nums, do_upload


def main(argv: list[str]) -> None:
    nums, do_upload = _parse(argv)

    print("==> 1/4  fetch audio")
    fetch_audio.fetch(nums or None)

    print("==> 2/4  transcribe")
    transcribe.run(nums or None)

    print("==> 3/4  draft show notes")
    draft_shownotes.run(nums or None)

    if not do_upload:
        print("==> 4/4  upload skipped (--no-upload)")
        return

    has_creds = (
        os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        or os.environ.get("GOOGLE_OAUTH_USER_TOKEN_JSON")
    )
    if not has_creds:
        print("==> 4/4  upload skipped (no Google credentials configured)")
        return

    print("==> 4/4  upload to Drive")
    upload_to_drive.run(nums or None, do_transcripts=True, do_shownotes=True)


if __name__ == "__main__":
    main(sys.argv[1:])
