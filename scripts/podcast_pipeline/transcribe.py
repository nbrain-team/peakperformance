"""Transcribe downloaded MP3s with Whisper, strip timestamps, write to disk.

Outputs:
  - transcripts/ppp-ep-NNN-<slug-or-padded>.txt  (consumed by regenerate-podcast.py)
  - scripts/podcast_pipeline/work/transcripts/PPP-Episode-NN-Transcript.txt
    (this is the file we upload back to Drive)

Whisper API has a 25 MB upload cap; large MP3s are split into ~20-minute
chunks first using ffmpeg (must be on PATH). For the 20–60 MB files in this
catalog, two to four chunks is typical.

Usage:
  python -m scripts.podcast_pipeline.transcribe         # everything in work/audio
  python -m scripts.podcast_pipeline.transcribe 12 13   # specific episodes

Env:
  OPENAI_API_KEY        required
  WHISPER_MODEL         optional, default whisper-1
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from openai import OpenAI

from .episodes import load_episodes

ROOT = Path(__file__).resolve().parents[2]
AUDIO_DIR = Path(__file__).resolve().parent / "work" / "audio"
WORK_TRANSCRIPTS = Path(__file__).resolve().parent / "work" / "transcripts"
SITE_TRANSCRIPTS = ROOT / "transcripts"

WHISPER_CHUNK_SECONDS = int(os.environ.get("WHISPER_CHUNK_SECONDS", "1200"))
WHISPER_MODEL = os.environ.get("WHISPER_MODEL", "whisper-1")


def _ffmpeg_path() -> str | None:
    """Prefer system ffmpeg; fall back to the static binary bundled with
    imageio-ffmpeg so the user doesn't have to install Homebrew."""
    sys_ff = shutil.which("ffmpeg")
    if sys_ff:
        return sys_ff
    try:
        import imageio_ffmpeg  # type: ignore

        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


def _split_audio(src: Path, chunk_seconds: int, dest_dir: Path) -> list[Path]:
    dest_dir.mkdir(parents=True, exist_ok=True)
    pattern = dest_dir / "chunk_%03d.mp3"
    ff = _ffmpeg_path()
    if not ff:
        raise RuntimeError("ffmpeg not available (install imageio-ffmpeg or system ffmpeg)")
    cmd = [
        ff,
        "-y",
        "-i",
        str(src),
        "-f",
        "segment",
        "-segment_time",
        str(chunk_seconds),
        "-c",
        "copy",
        str(pattern),
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return sorted(dest_dir.glob("chunk_*.mp3"))


def _strip_timestamps(text: str) -> str:
    text = re.sub(r"\[\d{1,2}:\d{2}(?::\d{2})?(?:\.\d+)?\]", "", text)
    text = re.sub(r"\(\d{1,2}:\d{2}(?::\d{2})?(?:\.\d+)?\)", "", text)
    text = re.sub(
        r"\d{1,2}:\d{2}(?::\d{2})?\s+-->\s+\d{1,2}:\d{2}(?::\d{2})?",
        "",
        text,
    )
    text = re.sub(r"^\d+\s*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip() + "\n"


def _transcribe_one(client: OpenAI, mp3: Path) -> str:
    with mp3.open("rb") as fh:
        resp = client.audio.transcriptions.create(
            model=WHISPER_MODEL,
            file=fh,
            response_format="text",
        )
    return resp if isinstance(resp, str) else getattr(resp, "text", "")


def transcribe_file(client: OpenAI, mp3: Path) -> str:
    size_mb = mp3.stat().st_size / 1_000_000
    if size_mb < 24:
        return _strip_timestamps(_transcribe_one(client, mp3))
    if not _ffmpeg_path():
        raise RuntimeError(
            f"{mp3.name} is {size_mb:.1f} MB and no ffmpeg binary was found. "
            "Reinstall requirements.txt so imageio-ffmpeg is present."
        )
    with tempfile.TemporaryDirectory() as td:
        chunks = _split_audio(mp3, WHISPER_CHUNK_SECONDS, Path(td))
        parts = [_transcribe_one(client, c) for c in chunks]
    return _strip_timestamps("\n\n".join(p.strip() for p in parts if p))


def run(episode_numbers: list[int] | None = None) -> list[Path]:
    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY is not set.")
    eps_by_num = {e.number: e for e in load_episodes()}
    if episode_numbers:
        wanted = [eps_by_num[n] for n in episode_numbers if n in eps_by_num]
    else:
        wanted = [e for e in eps_by_num.values() if (AUDIO_DIR / f"PPP-Episode-{e.padded}.mp3").is_file()]
    if not wanted:
        print("Nothing to transcribe.")
        return []

    WORK_TRANSCRIPTS.mkdir(parents=True, exist_ok=True)
    SITE_TRANSCRIPTS.mkdir(parents=True, exist_ok=True)

    client = OpenAI()
    out: list[Path] = []
    for ep in wanted:
        mp3 = AUDIO_DIR / f"PPP-Episode-{ep.padded}.mp3"
        if not mp3.is_file():
            print(f"[miss] Ep {ep.padded} — audio not downloaded yet ({mp3.name})")
            continue
        producer_path = WORK_TRANSCRIPTS / f"PPP-Episode-{ep.padded}-Transcript.txt"
        site_path = SITE_TRANSCRIPTS / f"ppp-ep-{ep.number:03d}.txt"
        if producer_path.is_file() and site_path.is_file():
            print(f"[skip] Ep {ep.padded} transcript already on disk")
            out.append(producer_path)
            continue

        print(f"[asr ] Ep {ep.padded} ({mp3.stat().st_size / 1_000_000:.1f} MB) ...")
        text = transcribe_file(client, mp3)

        producer_path.write_text(text, encoding="utf-8")
        site_path.write_text(text, encoding="utf-8")
        print(f"        -> {producer_path.relative_to(ROOT)}")
        print(f"        -> {site_path.relative_to(ROOT)}")
        out.append(producer_path)
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
