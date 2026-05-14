"""Pre-flight checker for the podcast pipeline.

Verifies (in order):
  1. Python imports for the pipeline modules
  2. ffmpeg binary (system or bundled via imageio-ffmpeg)
  3. OPENAI_API_KEY is set and the key actually authenticates
  4. Google Drive credential is set, can authenticate, and has visibility
     into the PPP root folder
  5. Drive write scope (best-effort detection without actually writing)
  6. Audit CSV parses and reports work to do

Each check prints PASS / WARN / FAIL on its own line. The script exits 0
when no FAIL was hit (warnings are okay). Run with no arguments:

    python -m scripts.podcast_pipeline.doctor
"""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

PPP_ROOT_FOLDER_ID = "1mhA8fDK9uPIn-1IzM-eG_yd5VOfnpWHO"

PASS = "PASS"
WARN = "WARN"
FAIL = "FAIL"


class Reporter:
    def __init__(self) -> None:
        self.failed = False

    def line(self, status: str, name: str, detail: str = "") -> None:
        symbol = {PASS: "✓", WARN: "!", FAIL: "✗"}[status]
        suffix = f"  — {detail}" if detail else ""
        print(f"  [{symbol}] {status:<4}  {name}{suffix}")
        if status == FAIL:
            self.failed = True


def _check_python(r: Reporter) -> None:
    v = sys.version_info
    detail = f"{v.major}.{v.minor}.{v.micro}"
    if v >= (3, 9):
        r.line(PASS, "Python 3.9+", detail)
    else:
        r.line(FAIL, "Python 3.9+", detail)


def _check_imports(r: Reporter) -> None:
    try:
        from openai import OpenAI  # noqa: F401
        from googleapiclient.discovery import build  # noqa: F401
        from google.oauth2 import service_account  # noqa: F401

        r.line(PASS, "Pipeline imports", "openai + google-api-python-client OK")
    except Exception as exc:  # noqa: BLE001
        r.line(FAIL, "Pipeline imports", f"{type(exc).__name__}: {exc}")


def _check_ffmpeg(r: Reporter) -> None:
    sys_ff = shutil.which("ffmpeg")
    if sys_ff:
        r.line(PASS, "ffmpeg", f"system: {sys_ff}")
        return
    try:
        import imageio_ffmpeg

        ff = imageio_ffmpeg.get_ffmpeg_exe()
        if Path(ff).exists():
            r.line(PASS, "ffmpeg", f"bundled: {ff}")
        else:
            r.line(FAIL, "ffmpeg", f"bundled path missing: {ff}")
    except Exception as exc:  # noqa: BLE001
        r.line(FAIL, "ffmpeg", f"no ffmpeg available ({exc})")


def _check_openai(r: Reporter) -> None:
    key = os.environ.get("OPENAI_API_KEY", "")
    if not key:
        r.line(FAIL, "OPENAI_API_KEY", "not set")
        return
    masked = f"{key[:7]}…{key[-4:]}" if len(key) > 12 else "(short)"
    try:
        from openai import OpenAI

        client = OpenAI()
        models = list(client.models.list())
        whisper_present = any("whisper" in m.id for m in models)
        detail = f"key {masked}, {len(models)} models accessible"
        if whisper_present:
            r.line(PASS, "OpenAI auth", detail + ", whisper available")
        else:
            r.line(WARN, "OpenAI auth", detail + ", no whisper-* model in list")
    except Exception as exc:  # noqa: BLE001
        r.line(FAIL, "OpenAI auth", f"{type(exc).__name__}: {exc}")


def _check_drive(r: Reporter) -> None:
    sa = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    user = os.environ.get("GOOGLE_OAUTH_USER_TOKEN_JSON")
    if not sa and not user:
        r.line(
            FAIL,
            "Drive credential",
            "neither GOOGLE_APPLICATION_CREDENTIALS nor GOOGLE_OAUTH_USER_TOKEN_JSON is set",
        )
        return

    cred_label: str
    if sa:
        if not Path(sa).is_file():
            r.line(FAIL, "Drive credential", f"file not found: {sa}")
            return
        cred_label = f"service account at {sa}"
    else:
        if not Path(user).is_file():  # type: ignore[arg-type]
            r.line(FAIL, "Drive credential", f"file not found: {user}")
            return
        cred_label = f"user token at {user}"

    try:
        from .drive_client import drive_service

        svc = drive_service(write=False)
        meta = (
            svc.files()
            .get(fileId=PPP_ROOT_FOLDER_ID, fields="id, name, mimeType", supportsAllDrives=True)
            .execute()
        )
        r.line(PASS, "Drive read access", f"{cred_label}; can see folder {meta.get('name')!r}")
    except Exception as exc:  # noqa: BLE001
        r.line(
            FAIL,
            "Drive read access",
            f"could not read PPP root folder ({type(exc).__name__}: {exc})",
        )
        return

    try:
        from .drive_client import drive_service

        svc_w = drive_service(write=True)
        about = svc_w.about().get(fields="user(emailAddress)").execute()
        email = about.get("user", {}).get("emailAddress", "?")
        r.line(PASS, "Drive write scope", f"authenticated as {email}")
    except Exception as exc:  # noqa: BLE001
        r.line(
            WARN,
            "Drive write scope",
            f"write scope not yet available ({type(exc).__name__}: {exc}); "
            "pipeline can still produce files locally with --no-upload",
        )


def _check_audit(r: Reporter) -> None:
    try:
        from .episodes import load_episodes

        eps = load_episodes()
        need_t = sum(1 for e in eps if e.needs_transcript)
        need_s = sum(1 for e in eps if e.needs_show_notes)
        r.line(
            PASS,
            "Audit CSV",
            f"{len(eps)} episodes parsed; {need_t} need transcripts, {need_s} need show notes",
        )
    except Exception as exc:  # noqa: BLE001
        r.line(FAIL, "Audit CSV", f"{type(exc).__name__}: {exc}")


def main() -> int:
    print("PPP podcast pipeline — preflight check")
    print("-" * 60)
    r = Reporter()
    _check_python(r)
    _check_imports(r)
    _check_ffmpeg(r)
    _check_audit(r)
    _check_openai(r)
    _check_drive(r)
    print("-" * 60)
    if r.failed:
        print("Result: FAIL — fix the items above before running the pipeline.")
        return 1
    print("Result: ready. Run `python -m scripts.podcast_pipeline.run_all` "
          "(add `--no-upload` if Drive write is still WARN).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
