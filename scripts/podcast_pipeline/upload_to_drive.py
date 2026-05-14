"""Upload (or refresh) transcripts and show-notes drafts into Drive folders.

Requires Drive WRITE scope (drive.file or drive). Read-only credentials will
fail here on purpose — see README for the scope upgrade workflow.

Behavior:
  - Transcript: uploads `PPP-Episode-NN-Transcript.txt` as a plain text file
    so the producer can keep diffing it cheaply.
  - Show notes: uploads `PPP Episode NN — Show notes` as a Google Doc
    (Markdown is converted on the fly so editors get a real Doc to refine).

If a file with the same name already exists in the target folder, the
existing file is updated in place (preserving its file ID and link).

Usage:
  python -m scripts.podcast_pipeline.upload_to_drive               # everything ready
  python -m scripts.podcast_pipeline.upload_to_drive 12 13         # specific episodes
  python -m scripts.podcast_pipeline.upload_to_drive --transcripts # only transcripts
  python -m scripts.podcast_pipeline.upload_to_drive --shownotes   # only show notes
"""

from __future__ import annotations

import sys
from pathlib import Path

from .drive_client import drive_service, upload_as_google_doc, upload_text_file
from .episodes import load_episodes

PIPE_DIR = Path(__file__).resolve().parent
WORK_TRANSCRIPTS = PIPE_DIR / "work" / "transcripts"
WORK_NOTES = PIPE_DIR / "work" / "show_notes"


def _filter(args: list[str]) -> tuple[list[int], bool, bool]:
    do_tx = "--shownotes" not in args
    do_sn = "--transcripts" not in args
    nums: list[int] = []
    for a in args:
        if a.startswith("--"):
            continue
        try:
            nums.append(int(a))
        except ValueError:
            pass
    return nums, do_tx, do_sn


def run(episode_numbers: list[int] | None, do_transcripts: bool, do_shownotes: bool) -> None:
    eps_by_num = {e.number: e for e in load_episodes()}
    targets = (
        [eps_by_num[n] for n in (episode_numbers or []) if n in eps_by_num]
        or list(eps_by_num.values())
    )
    if not targets:
        print("Nothing to upload.")
        return

    service = drive_service(write=True)

    for ep in targets:
        if not ep.folder_id:
            print(f"[skip] Ep {ep.padded} — no folder_id in audit row")
            continue

        if do_transcripts:
            tx = WORK_TRANSCRIPTS / f"PPP-Episode-{ep.padded}-Transcript.txt"
            if tx.is_file():
                print(f"[up  ] Ep {ep.padded} transcript -> {ep.folder_name!r}")
                meta = upload_text_file(
                    service,
                    folder_id=ep.folder_id,
                    name=ep.transcript_filename,
                    text=tx.read_text(encoding="utf-8"),
                )
                print(f"        -> {meta.get('webViewLink', meta.get('id'))}")

        if do_shownotes:
            sn = WORK_NOTES / f"PPP Episode {ep.padded} — Show notes.md"
            if sn.is_file():
                print(f"[up  ] Ep {ep.padded} show notes -> {ep.folder_name!r}")
                meta = upload_as_google_doc(
                    service,
                    folder_id=ep.folder_id,
                    title=ep.show_notes_doc_title,
                    body_markdown=sn.read_text(encoding="utf-8"),
                )
                print(f"        -> {meta.get('webViewLink', meta.get('id'))}")


if __name__ == "__main__":
    nums, do_tx, do_sn = _filter(sys.argv[1:])
    run(nums, do_tx, do_sn)
