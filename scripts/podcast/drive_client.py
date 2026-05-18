"""Thin wrapper around the Google Drive v3 API for the podcast pipeline.

WHY THIS EXISTS
===============
The original pipeline depended on two things outside the Python process:

  1. The user's Google Drive desktop sync, which pulled transcripts /
     show notes / thumbnails down to a local mirror folder on the Mac.
  2. The Cursor agent invoking the gdrive MCP to list folders and
     discover new episode subfolders.

Both of those tie the build to the user's laptop. To run the pipeline
on a Render cron service (or any always-on server) we need direct
Drive API access via a Google Cloud service account.

USAGE
=====
    from drive_client import DriveClient
    drive = DriveClient.from_env()            # reads GOOGLE_DRIVE_SA_JSON
    files = drive.list_folder('1mhA8fDK9uPI…')
    drive.download_file(file_id, dest_path)

The service account credentials are loaded from one of:
  • GOOGLE_DRIVE_SA_JSON  — env var containing the full JSON blob
  • GOOGLE_DRIVE_SA_FILE  — env var pointing at a JSON file on disk
  • ~/.config/ppp/drive-sa.json — local fallback for laptop runs

The service account email must be granted Viewer access to the master
Drive folder (1mhA8fDK9uPIn-1IzM-eG_yd5VOfnpWHO). See README for setup.
"""
from __future__ import annotations
import io
import json
import os
import re
import sys
from pathlib import Path
from typing import Iterable

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
DEFAULT_LOCAL_KEY = Path.home() / '.config' / 'ppp' / 'drive-sa.json'


class DriveClient:
    def __init__(self, credentials):
        # Imported lazily so the rest of the build pipeline doesn't pay
        # the import cost when no Drive access is needed.
        from googleapiclient.discovery import build  # type: ignore
        self.service = build('drive', 'v3', credentials=credentials,
                             cache_discovery=False)

    # ----- credential loading ------------------------------------------------

    @classmethod
    def from_env(cls) -> 'DriveClient':
        """Construct from environment / well-known credential locations.

        Order of precedence:
          1. GOOGLE_DRIVE_SA_JSON (raw JSON in env)
          2. GOOGLE_DRIVE_SA_FILE (path to JSON on disk)
          3. ~/.config/ppp/drive-sa.json (laptop fallback)
        """
        from google.oauth2 import service_account  # type: ignore

        raw = os.environ.get('GOOGLE_DRIVE_SA_JSON')
        if raw:
            info = json.loads(raw)
            creds = service_account.Credentials.from_service_account_info(
                info, scopes=SCOPES)
            return cls(creds)

        path = os.environ.get('GOOGLE_DRIVE_SA_FILE')
        if path and Path(path).exists():
            creds = service_account.Credentials.from_service_account_file(
                path, scopes=SCOPES)
            return cls(creds)

        if DEFAULT_LOCAL_KEY.exists():
            creds = service_account.Credentials.from_service_account_file(
                str(DEFAULT_LOCAL_KEY), scopes=SCOPES)
            return cls(creds)

        raise RuntimeError(
            'No Drive service-account credentials found. Set '
            'GOOGLE_DRIVE_SA_JSON (inline) or GOOGLE_DRIVE_SA_FILE (path), '
            f'or place the JSON at {DEFAULT_LOCAL_KEY}.'
        )

    # ----- folder + file listing --------------------------------------------

    def list_folder(self, folder_id: str) -> list[dict]:
        """List immediate children of a Drive folder. Returns list of
        dicts with: id, name, mimeType, size (str|None), modifiedTime."""
        out: list[dict] = []
        page_token: str | None = None
        while True:
            resp = self.service.files().list(
                q=f"'{folder_id}' in parents and trashed = false",
                spaces='drive',
                fields='nextPageToken, files(id, name, mimeType, size, modifiedTime, md5Checksum)',
                pageSize=200,
                pageToken=page_token,
            ).execute()
            out.extend(resp.get('files', []))
            page_token = resp.get('nextPageToken')
            if not page_token:
                break
        return out

    def list_subfolders(self, folder_id: str) -> list[dict]:
        return [f for f in self.list_folder(folder_id)
                if f.get('mimeType') == 'application/vnd.google-apps.folder']

    # ----- download ----------------------------------------------------------

    def download_file(self, file_id: str, dest_path: Path) -> int:
        """Stream a binary file to disk. Returns bytes written.

        Idempotent: if dest_path exists and its size matches the Drive
        file's size, skip the download. (We refresh by deleting the
        local file first when we want a re-download.)"""
        from googleapiclient.http import MediaIoBaseDownload  # type: ignore

        dest_path.parent.mkdir(parents=True, exist_ok=True)

        # Check size for idempotency.
        try:
            meta = self.service.files().get(
                fileId=file_id, fields='size, name').execute()
            remote_size = int(meta.get('size', 0))
            if dest_path.exists() and remote_size > 0 \
                    and dest_path.stat().st_size == remote_size:
                return remote_size
        except Exception:
            pass

        request = self.service.files().get_media(fileId=file_id)
        buf = io.BytesIO()
        downloader = MediaIoBaseDownload(buf, request, chunksize=2 * 1024 * 1024)
        done = False
        while not done:
            _, done = downloader.next_chunk()
        data = buf.getvalue()
        dest_path.write_bytes(data)
        return len(data)

    def export_doc(self, file_id: str, mime_type: str, dest_path: Path) -> int:
        """Export a native Google Doc / Sheet as a binary file.
        Used for transcripts that may be Google Docs rather than .docx.
        Common mime targets:
          • application/vnd.openxmlformats-officedocument.wordprocessingml.document  (.docx)
          • application/pdf  (.pdf)
        """
        request = self.service.files().export_media(
            fileId=file_id, mimeType=mime_type)
        buf = io.BytesIO()
        from googleapiclient.http import MediaIoBaseDownload  # type: ignore
        downloader = MediaIoBaseDownload(buf, request, chunksize=2 * 1024 * 1024)
        done = False
        while not done:
            _, done = downloader.next_chunk()
        data = buf.getvalue()
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        dest_path.write_bytes(data)
        return len(data)


# ---------------------------------------------------------------------------
# Episode-folder helpers (knowledge of the PPP Drive layout)
# ---------------------------------------------------------------------------

EP_FOLDER_NAME_RE = re.compile(r'(?:^|\b)(?:ep(?:isode)?\.?\s*|#)?(\d{1,3})(?:\b|$)', re.IGNORECASE)


def parse_episode_number(folder_name: str) -> int | None:
    """Extract an episode number from a Drive folder name like
    'Ep 25 - Tadros Abdelmalek', 'Episode 14', 'PPP EP 03', '#7', etc."""
    m = re.search(r'(?:ep(?:isode)?\.?\s*|#)\s*(\d{1,3})', folder_name, re.IGNORECASE)
    if m:
        return int(m.group(1))
    # Fall back to any bare integer (e.g., folder named "25")
    m = re.search(r'\b(\d{1,3})\b', folder_name)
    if m:
        return int(m.group(1))
    return None


def find_transcript_file(files: Iterable[dict]) -> dict | None:
    """Return the file that looks like an episode transcript."""
    for f in files:
        name = f.get('name', '').lower()
        if 'transcript' not in name:
            continue
        mt = f.get('mimeType', '')
        if mt == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
            return f
        if mt == 'application/vnd.google-apps.document':
            return f
    return None


def find_show_notes_file(files: Iterable[dict]) -> dict | None:
    for f in files:
        name = f.get('name', '').lower()
        if 'show notes' not in name and 'shownotes' not in name:
            continue
        mt = f.get('mimeType', '')
        if mt == 'application/pdf' or mt == 'application/vnd.google-apps.document':
            return f
    return None


# Thumbnail discovery priority:
#   1) Explicit "1 by 1.png" / "16 by 9.png" naming  (modern convention)
#   2) "PPP Ep N - YouTube Thumbnail.jpg"             (always 16:9; CSS center-crops on the listing)
#   3) Any other large image whose name contains 'thumbnail'
#
# The priority lets the user move from old naming to new naming without
# breaking past episodes. Returned dict is keyed:
#   { 'id_1x1': str, 'id_16x9': str, 'source_file': str }

def discover_thumbnails(files: list[dict], ep_num: int | None = None) -> dict | None:
    by_name: dict[str, dict] = {f['name']: f for f in files
                                if f.get('mimeType', '').startswith('image/')}
    lower = {n.lower(): f for n, f in by_name.items()}

    one_by_one = lower.get('1 by 1.png') or lower.get('1x1.png') or lower.get('1-by-1.png')
    sixteen_nine = lower.get('16 by 9.png') or lower.get('16x9.png') or lower.get('16-by-9.png')
    if one_by_one and sixteen_nine:
        return {
            'id_1x1': one_by_one['id'],
            'id_16x9': sixteen_nine['id'],
            'source_file': f'{one_by_one["name"]} + {sixteen_nine["name"]}',
        }

    # YouTube thumbnail (16:9, shows guest). Browser CSS center-crops the
    # 1:1 listing card.
    yt = None
    for n, f in lower.items():
        if 'youtube thumbnail' in n and f.get('mimeType') == 'image/jpeg':
            yt = f
            break
    if yt:
        return {
            'id_1x1': yt['id'],
            'id_16x9': yt['id'],
            'source_file': yt['name'],
        }

    # Fall back: any image whose name has "thumbnail" in it, prefer larger.
    candidates = []
    for n, f in lower.items():
        if 'thumbnail' in n or (ep_num is not None and f'ep {ep_num}' in n):
            try:
                sz = int(f.get('size') or 0)
            except (TypeError, ValueError):
                sz = 0
            candidates.append((sz, f))
    if candidates:
        candidates.sort(key=lambda t: -t[0])
        f = candidates[0][1]
        return {
            'id_1x1': f['id'],
            'id_16x9': f['id'],
            'source_file': f['name'],
        }
    return None
