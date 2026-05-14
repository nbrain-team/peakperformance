"""Draft show notes from a transcript using GPT, in the standard PPP template.

Outputs:
  - docs/episode-drafts/PPP-Episode-NN-Show-notes.md   (review surface in the repo)
  - scripts/podcast_pipeline/work/show_notes/PPP Episode NN — Show notes.md
    (used by upload_to_drive.py to create/update the Google Doc)

This drafts only — Roxanna reviews and edits before publishing.

Usage:
  python -m scripts.podcast_pipeline.draft_shownotes        # everything with a transcript
  python -m scripts.podcast_pipeline.draft_shownotes 12 13  # specific episodes

Env:
  OPENAI_API_KEY                required
  SHOW_NOTES_MODEL              optional, default gpt-4o-mini
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from openai import OpenAI

from .episodes import load_episodes

ROOT = Path(__file__).resolve().parents[2]
TEMPLATE_PATH = ROOT / "docs" / "podcast-show-notes-template.md"
TRANSCRIPTS_DIR = Path(__file__).resolve().parent / "work" / "transcripts"
WORK_NOTES_DIR = Path(__file__).resolve().parent / "work" / "show_notes"
DRAFT_DIR = ROOT / "docs" / "episode-drafts"

MODEL = os.environ.get("SHOW_NOTES_MODEL", "gpt-4o-mini")

SYSTEM_PROMPT = """You are an editor for the Peak Property Performance podcast.
Produce show notes that follow the supplied template EXACTLY:
- Same section order
- Same headings (case, bold, dividers)
- Same bullet count where the template specifies
- Same boilerplate for hosts, operator resources, about, and tags

Rules:
- Use real timestamps from the transcript when present; round to MM:SS.
- Bold the lead phrase of each "What You'll Learn" bullet.
- Do not invent guests, links, or quotes.
- If the episode is hosts-only (no guest), follow the solo-episode variant
  in the template and omit the guest section.
- Output Markdown only, no commentary.
"""


def _build_user_prompt(episode_number: int, folder_name: str, transcript: str, template: str) -> str:
    return (
        f"Episode number: {episode_number}\n"
        f"Drive folder name: {folder_name}\n\n"
        "TEMPLATE TO MATCH (do not include this verbatim — use it as the structure):\n"
        "-----\n"
        f"{template}\n"
        "-----\n\n"
        "TRANSCRIPT (already stripped of timing markers):\n"
        "-----\n"
        f"{transcript}\n"
        "-----\n\n"
        "Now produce the finished show-notes markdown."
    )


def draft_one(client: OpenAI, episode_number: int, folder_name: str, transcript: str, template: str) -> str:
    resp = client.chat.completions.create(
        model=MODEL,
        temperature=0.4,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": _build_user_prompt(episode_number, folder_name, transcript, template),
            },
        ],
    )
    return resp.choices[0].message.content.strip() + "\n"


def run(episode_numbers: list[int] | None = None) -> list[Path]:
    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY is not set.")
    if not TEMPLATE_PATH.is_file():
        raise SystemExit(f"Template not found at {TEMPLATE_PATH}")
    template = TEMPLATE_PATH.read_text(encoding="utf-8")

    eps_by_num = {e.number: e for e in load_episodes()}
    if episode_numbers:
        wanted = [eps_by_num[n] for n in episode_numbers if n in eps_by_num]
    else:
        wanted = [
            e for e in eps_by_num.values()
            if (TRANSCRIPTS_DIR / f"PPP-Episode-{e.padded}-Transcript.txt").is_file()
        ]
    if not wanted:
        print("Nothing to draft.")
        return []

    WORK_NOTES_DIR.mkdir(parents=True, exist_ok=True)
    DRAFT_DIR.mkdir(parents=True, exist_ok=True)

    client = OpenAI()
    out: list[Path] = []
    for ep in wanted:
        tx_path = TRANSCRIPTS_DIR / f"PPP-Episode-{ep.padded}-Transcript.txt"
        if not tx_path.is_file():
            print(f"[miss] Ep {ep.padded} — no transcript yet ({tx_path.name})")
            continue
        transcript = tx_path.read_text(encoding="utf-8")

        print(f"[gen ] Ep {ep.padded} show notes ...")
        body = draft_one(client, ep.number, ep.folder_name, transcript, template)

        repo_draft = DRAFT_DIR / f"PPP-Episode-{ep.padded}-Show-notes.md"
        upload_copy = WORK_NOTES_DIR / f"PPP Episode {ep.padded} — Show notes.md"
        repo_draft.write_text(body, encoding="utf-8")
        upload_copy.write_text(body, encoding="utf-8")
        print(f"        -> {repo_draft.relative_to(ROOT)}")
        out.append(repo_draft)
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
    run(_parse_args(sys.argv[1:]))
