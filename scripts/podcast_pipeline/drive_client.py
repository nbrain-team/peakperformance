"""Thin Drive v3 client used by fetch_audio.py and upload_to_drive.py.

Auth options (checked in this order):

  1. GOOGLE_APPLICATION_CREDENTIALS       — path to a service-account JSON
                                            (production / cron path).
  2. GOOGLE_OAUTH_USER_TOKEN_JSON         — path to a token.json from a
                                            user OAuth flow (manual runs).

Read scopes are sufficient for fetch_audio.py. Write scopes (drive.file or
drive) are required for upload_to_drive.py — see README for the scope
upgrade workflow.
"""

from __future__ import annotations

import io
import os
from pathlib import Path

from google.oauth2 import service_account
from google.oauth2.credentials import Credentials as UserCredentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

READONLY_SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
WRITE_SCOPES = ["https://www.googleapis.com/auth/drive"]


def _credentials(scopes: list[str]):
    sa_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if sa_path and Path(sa_path).is_file():
        return service_account.Credentials.from_service_account_file(
            sa_path, scopes=scopes
        )
    user_token = os.environ.get("GOOGLE_OAUTH_USER_TOKEN_JSON")
    if user_token and Path(user_token).is_file():
        return UserCredentials.from_authorized_user_file(user_token, scopes)
    raise RuntimeError(
        "No Google credentials found. Set GOOGLE_APPLICATION_CREDENTIALS "
        "(service account JSON) or GOOGLE_OAUTH_USER_TOKEN_JSON (user token)."
    )


def drive_service(*, write: bool = False):
    scopes = WRITE_SCOPES if write else READONLY_SCOPES
    creds = _credentials(scopes)
    return build("drive", "v3", credentials=creds, cache_discovery=False)


def find_audio_file(service, folder_id: str) -> dict | None:
    """Return the canonical episode MP3 in a folder, preferring 'Audioversion*'."""
    q = (
        f"'{folder_id}' in parents and trashed = false "
        "and (mimeType = 'audio/mpeg' or mimeType = 'audio/mp3')"
    )
    resp = (
        service.files()
        .list(
            q=q,
            fields="files(id, name, size, mimeType, modifiedTime)",
            pageSize=50,
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
        )
        .execute()
    )
    files = resp.get("files", [])
    if not files:
        return None
    files.sort(
        key=lambda f: (
            0 if "audioversion" in (f["name"] or "").lower() else 1,
            -int(f.get("size") or 0),
        )
    )
    return files[0]


def find_existing_in_folder(service, folder_id: str, name: str) -> dict | None:
    q = (
        f"'{folder_id}' in parents and trashed = false "
        f"and name = '{name.replace(chr(39), chr(92) + chr(39))}'"
    )
    resp = (
        service.files()
        .list(
            q=q,
            fields="files(id, name, mimeType)",
            pageSize=5,
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
        )
        .execute()
    )
    files = resp.get("files", [])
    return files[0] if files else None


def download_file(service, file_id: str, dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    request = service.files().get_media(fileId=file_id, supportsAllDrives=True)
    with dest.open("wb") as fh:
        downloader = MediaIoBaseDownload(fh, request, chunksize=8 * 1024 * 1024)
        done = False
        while not done:
            _, done = downloader.next_chunk()
    return dest


def upload_text_file(
    service,
    folder_id: str,
    name: str,
    text: str,
    *,
    mime_type: str = "text/plain",
    overwrite: bool = True,
) -> dict:
    existing = find_existing_in_folder(service, folder_id, name)
    tmp = Path(f"/tmp/{name}")
    tmp.write_text(text, encoding="utf-8")
    media = MediaFileUpload(str(tmp), mimetype=mime_type, resumable=False)
    if existing and overwrite:
        return service.files().update(fileId=existing["id"], media_body=media).execute()
    metadata = {"name": name, "parents": [folder_id], "mimeType": mime_type}
    return (
        service.files()
        .create(body=metadata, media_body=media, supportsAllDrives=True, fields="id, name, webViewLink")
        .execute()
    )


def upload_as_google_doc(
    service,
    folder_id: str,
    title: str,
    body_markdown: str,
    *,
    overwrite: bool = True,
) -> dict:
    """Create (or overwrite) a Google Doc from markdown source.

    Drive will convert text/markdown into a native Google Doc when
    mimeType in the create call is set to application/vnd.google-apps.document.
    """
    existing = find_existing_in_folder(service, folder_id, title)
    tmp = Path(f"/tmp/{title}.md")
    tmp.write_text(body_markdown, encoding="utf-8")
    media = MediaFileUpload(str(tmp), mimetype="text/markdown", resumable=False)
    if existing and overwrite:
        return service.files().update(fileId=existing["id"], media_body=media).execute()
    metadata = {
        "name": title,
        "parents": [folder_id],
        "mimeType": "application/vnd.google-apps.document",
    }
    return (
        service.files()
        .create(
            body=metadata,
            media_body=media,
            supportsAllDrives=True,
            fields="id, name, webViewLink",
        )
        .execute()
    )
