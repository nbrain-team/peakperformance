"""Episode registry sourced from docs/podcast-drive-gap-audit.csv.

Single source of truth for which Drive folder corresponds to which episode
number. The audit CSV is human-edited (Roxanna marks rows complete), so this
module just reads it and exposes a typed view.
"""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
AUDIT_CSV = REPO_ROOT / "docs" / "podcast-drive-gap-audit.csv"

FOLDER_ID_RE = re.compile(r"/folders/([A-Za-z0-9_-]+)")


@dataclass(frozen=True)
class Episode:
    number: int
    folder_name: str
    folder_id: str
    folder_url: str
    needs_transcript: bool
    needs_show_notes: bool
    notes: str

    @property
    def padded(self) -> str:
        return f"{self.number:02d}"

    @property
    def transcript_doc_title(self) -> str:
        return f"PPP Episode {self.padded} — Transcript"

    @property
    def show_notes_doc_title(self) -> str:
        return f"PPP Episode {self.padded} — Show notes"

    @property
    def transcript_filename(self) -> str:
        return f"PPP-Episode-{self.padded}-Transcript.txt"


def _parse_folder_id(url: str) -> str:
    m = FOLDER_ID_RE.search(url or "")
    return m.group(1) if m else ""


def load_episodes(audit_csv: Path = AUDIT_CSV) -> list[Episode]:
    if not audit_csv.is_file():
        raise FileNotFoundError(f"Audit CSV not found at {audit_csv}")

    out: list[Episode] = []
    with audit_csv.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            try:
                num = int(row["sort_order"])
            except (KeyError, ValueError):
                continue
            if num <= 0:
                continue
            flags = (row.get("gap_flags") or "").upper()
            out.append(
                Episode(
                    number=num,
                    folder_name=row["folder_name"].strip(),
                    folder_id=_parse_folder_id(row["folder_url"]),
                    folder_url=row["folder_url"].strip(),
                    needs_transcript="NEEDS_TRANSCRIPT" in flags,
                    needs_show_notes="NEEDS_SHOW_NOTES" in flags,
                    notes=(row.get("notes_for_ops") or "").strip(),
                )
            )
    out.sort(key=lambda e: e.number)
    return out


def episodes_needing_transcripts() -> list[Episode]:
    return [e for e in load_episodes() if e.needs_transcript and e.folder_id]


def episodes_needing_show_notes() -> list[Episode]:
    return [e for e in load_episodes() if e.needs_show_notes and e.folder_id]


if __name__ == "__main__":
    eps = load_episodes()
    print(f"{len(eps)} episodes in audit")
    print(f"  needing transcripts: {sum(e.needs_transcript for e in eps)}")
    print(f"  needing show notes:  {sum(e.needs_show_notes for e in eps)}")
    for e in eps:
        flags = []
        if e.needs_transcript:
            flags.append("T")
        if e.needs_show_notes:
            flags.append("S")
        flag_str = ",".join(flags) or "-"
        print(f"  Ep {e.padded}  [{flag_str}]  {e.folder_name}")
