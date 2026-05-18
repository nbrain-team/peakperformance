"""Decode base64 binary content (as returned by user-opticwise-gdrive MCP) into plain text.

Used to pull podcast transcripts (.docx) and show notes (.pdf) for embedding into episode pages.

Inputs are JSON files dropped under scripts/podcast/_drive_cache/<ep_num>/{transcript,shownotes}.json
each shaped like the MCP read_file response: {name, mimeType, content_base64, binary: true, ...}.

Outputs plain-text + lightly structured HTML to scripts/podcast/_extracted/<ep_num>/.
"""
from __future__ import annotations
import base64
import io
import json
import re
import sys
from pathlib import Path

# Ensure pip --user packages resolve
sys.path.insert(0, '/Users/billdouglas/Library/Python/3.9/lib/python/site-packages')

import docx  # python-docx
from pdfminer.high_level import extract_text as pdf_extract_text


ROOT = Path(__file__).resolve().parent
CACHE_DIR = ROOT / '_drive_cache'
OUT_DIR = ROOT / '_extracted'


def extract_docx(blob: bytes) -> list[str]:
    """Return a list of non-empty paragraphs from a docx blob."""
    document = docx.Document(io.BytesIO(blob))
    paragraphs: list[str] = []
    for para in document.paragraphs:
        text = (para.text or '').strip()
        if text:
            paragraphs.append(text)
    return paragraphs


def extract_pdf(blob: bytes) -> str:
    """Return raw text extracted from a PDF blob."""
    return pdf_extract_text(io.BytesIO(blob))


def normalize_pdf_text(raw: str) -> list[str]:
    """Split pdf text into clean paragraphs/lines, collapsing PDF artifacts."""
    raw = raw.replace('\u00a0', ' ')
    raw = re.sub(r'[ \t]+', ' ', raw)
    paras: list[str] = []
    cur: list[str] = []
    for line in raw.splitlines():
        s = line.strip()
        if not s:
            if cur:
                paras.append(' '.join(cur).strip())
                cur = []
            continue
        cur.append(s)
    if cur:
        paras.append(' '.join(cur).strip())
    return [p for p in paras if p]


def process_one(ep_dir: Path) -> dict:
    transcript_meta = json.loads((ep_dir / 'transcript.json').read_text())
    shownotes_meta = json.loads((ep_dir / 'shownotes.json').read_text())

    transcript_paragraphs = extract_docx(
        base64.b64decode(transcript_meta['content_base64'])
    )
    shownotes_text = extract_pdf(base64.b64decode(shownotes_meta['content_base64']))
    shownotes_paragraphs = normalize_pdf_text(shownotes_text)

    out = OUT_DIR / ep_dir.name
    out.mkdir(parents=True, exist_ok=True)
    (out / 'transcript.txt').write_text('\n\n'.join(transcript_paragraphs))
    (out / 'shownotes.txt').write_text('\n\n'.join(shownotes_paragraphs))
    return {
        'ep': ep_dir.name,
        'transcript_paragraphs': len(transcript_paragraphs),
        'shownotes_paragraphs': len(shownotes_paragraphs),
    }


def main():
    if not CACHE_DIR.exists():
        print(f'No cache at {CACHE_DIR}; nothing to do.')
        return
    results = []
    for ep_dir in sorted(CACHE_DIR.iterdir()):
        if not ep_dir.is_dir():
            continue
        if not (ep_dir / 'transcript.json').exists():
            continue
        if not (ep_dir / 'shownotes.json').exists():
            continue
        results.append(process_one(ep_dir))
    for r in results:
        print(r)


if __name__ == '__main__':
    main()
