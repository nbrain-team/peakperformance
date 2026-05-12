#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Regenerate static podcast pages from Anchor RSS + optional YouTube + Drive art.

- Fixes double-encoded show notes (renders real HTML from RSS description).
- Sets episode numbers (0 = coming-soon slug; others from itunes:episode).
- Hero + listing card art (priority): Google Drive episode-folder thumbnail PNG/JPG,
  then YouTube hqdefault when matched, then RSS itunes:image.
- Injects optional transcripts from PPP_TRANSCRIPTS_DIR (default ./transcripts).

Intro / show notes: always from RSS description (same as Apple/YouTube distributors).

Usage (repo root):
  python3 scripts/regenerate-podcast.py

Env:
  RSS_URL                             Anchor feed URL
  YOUTUBE_UPLOADS_PLAYLIST_ID         uploads playlist (UU…)
  YOUTUBE_API_KEY                     optional — full YouTube title matching
  GOOGLE_DRIVE_API_KEY                optional — list episode folders under parent & pick thumbnail
  GOOGLE_API_KEY                      fallback if GOOGLE_DRIVE_API_KEY unset (same GCP key works if both APIs enabled)
  DRIVE_EPISODES_PARENT_FOLDER_ID     Drive folder containing “Ep 34” subfolders (default: PPP production folder)

Files:
  scripts/podcast-drive-thumbnails.json   optional { "31": "driveFileId", … } when API key missing or offline
  scripts/podcast-youtube-overrides.json slug → video id
"""

from __future__ import annotations

import html
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from difflib import SequenceMatcher
from pathlib import Path


RSS_URL = os.environ.get(
    "RSS_URL", "https://anchor.fm/s/1057cecf4/podcast/rss"
)
# Channel UCQQQx__XXu8XvCRuozX3FYA → uploads playlist UU + rest after UC
YOUTUBE_UPLOADS_PLAYLIST_ID = os.environ.get(
    "YOUTUBE_UPLOADS_PLAYLIST_ID", "UUQQQx__XXu8XvCRuozX3FYA"
)
COMING_SOON_SLUG = "coming-soon-peak-property-performance-with-bill-douglas-drew-hall"
# PPP podcast episode assets (shared Drive): subfolders “Ep 34”, “Ep. 8”, etc.
DEFAULT_DRIVE_EPISODES_PARENT_ID = "1mhA8fDK9uPIn-1IzM-eG_yd5VOfnpWHO"

NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "content": "http://purl.org/rss/1.0/modules/content/",
    "itunes": "http://www.itunes.com/dtds/podcast-1.0.dtd",
    "dc": "http://purl.org/dc/elements/1.1/",
    "media": "http://search.yahoo.com/mrss/",
    "yt": "http://www.youtube.com/xml/schemas/2015",
}


def fetch(url: str) -> str:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "PPP-podcast-regen/1.0 (+https://peakperformance.onrender.com)"},
    )
    with urllib.request.urlopen(req, timeout=45) as r:
        return r.read().decode("utf-8", errors="replace")


def drive_api_list_files(api_key: str, q: str) -> list[dict]:
    """Drive API v3 files.list; uses API key (folder must be accessible to key / link-shared public)."""
    out: list[dict] = []
    page_token: str | None = None
    while True:
        params: dict[str, str] = {
            "q": q,
            "fields": "nextPageToken,files(id,name,mimeType)",
            "key": api_key,
            "pageSize": "100",
            "supportsAllDrives": "true",
            "includeItemsFromAllDrives": "true",
        }
        if page_token:
            params["pageToken"] = page_token
        url = "https://www.googleapis.com/drive/v3/files?" + urllib.parse.urlencode(
            params
        )
        try:
            raw = fetch(url)
            payload = json.loads(raw)
        except urllib.error.HTTPError as e:
            print(f"WARN Drive API HTTP {e.code}: {e.reason}", file=sys.stderr)
            break
        except json.JSONDecodeError as ex:
            print(f"WARN Drive API bad JSON: {ex}", file=sys.stderr)
            break
        except Exception as ex:
            print(f"WARN Drive API: {ex}", file=sys.stderr)
            break
        out.extend(payload.get("files") or [])
        page_token = payload.get("nextPageToken")
        if not page_token:
            break
    return out


def episode_num_from_drive_folder_title(name: str) -> int | None:
    s = name.strip()
    if "&" in s:
        return None
    m = re.match(r"(?i)^ep\.?\s*(\d+)", s)
    if not m:
        return None
    return int(m.group(1))


def pick_thumbnail_file_id(children: list[dict]) -> str | None:
    images = [
        f
        for f in children
        if (f.get("mimeType") or "").startswith("image/")
    ]
    if not images:
        return None
    thumbs = [f for f in images if re.search(r"thumbnail", f.get("name", ""), re.I)]
    pool = thumbs or images

    def sort_key(f: dict) -> tuple:
        n = f.get("name", "")
        has_tn = 0 if re.search(r"thumbnail", n, re.I) else 1
        return (has_tn, len(n))

    pool.sort(key=sort_key)
    fid = pool[0].get("id")
    return fid if fid else None


def build_drive_thumbnail_file_index(api_key: str, parent_folder_id: str) -> dict[int, str]:
    q = (
        f"'{parent_folder_id}' in parents and "
        f"mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    )
    folders = drive_api_list_files(api_key, q)
    result: dict[int, str] = {}
    for fol in folders:
        name = fol.get("name") or ""
        ep = episode_num_from_drive_folder_title(name)
        if ep is None:
            continue
        fid = fol.get("id")
        if not fid:
            continue
        cq = f"'{fid}' in parents and trashed = false"
        kids = drive_api_list_files(api_key, cq)
        thumb_id = pick_thumbnail_file_id(kids)
        if thumb_id:
            result[ep] = thumb_id
    return result


def drive_thumbnail_image_url(file_id: str) -> str:
    return f"https://drive.google.com/thumbnail?id={urllib.parse.quote(file_id)}&sz=w1280"


def load_drive_thumbnail_id_manifest(root: Path) -> dict[int, str]:
    p = root / "scripts" / "podcast-drive-thumbnails.json"
    if not p.is_file():
        return {}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    out: dict[int, str] = {}
    if not isinstance(data, dict):
        return out
    for k, v in data.items():
        if not k or str(k).startswith("_"):
            continue
        if not isinstance(v, str) or not v.strip():
            continue
        try:
            ki = int(k)
        except (TypeError, ValueError):
            continue
        out[ki] = v.strip()
    return out


def resolve_drive_thumbnail_file_index(
    root: Path, api_key: str, parent_folder_id: str
) -> dict[int, str]:
    merged = load_drive_thumbnail_id_manifest(root)
    if api_key and parent_folder_id:
        fetched = build_drive_thumbnail_file_index(api_key, parent_folder_id)
        merged.update(fetched)
    return merged


def patch_preload_episode_thumb(page_html: str, thumb: str) -> str:
    """Replace the first non-fast-company preload image (episode art slot)."""
    replaced = False

    def repl(m: re.Match) -> str:
        nonlocal replaced
        href = m.group(2)
        if "fast-company-press" in href:
            return m.group(0)
        if replaced:
            return m.group(0)
        replaced = True
        return m.group(1) + html.escape(thumb, quote=True) + m.group(3)

    return re.sub(
        r'(<link rel="preload" as="image" href=")([^"]+)(")',
        repl,
        page_html,
    )


def play_id_from_anchor_url(u: str) -> str | None:
    m = re.search(r"/play/(\d+)/", u)
    return m.group(1) if m else None


def sanitize_show_notes(fragment: str) -> str:
    t = html.unescape(fragment.strip())
    t = re.sub(r"(?is)<script[^>]*>.*?</script>", "", t)
    t = re.sub(r"(?is)<style[^>]*>.*?</style>", "", t)
    return t.strip()


def duration_pretty(raw: str | None) -> str:
    if not raw:
        return ""
    parts = raw.strip().split(":")
    try:
        if len(parts) == 3:
            h, m, s = int(parts[0]), int(parts[1]), int(parts[2])
        elif len(parts) == 2:
            h, m, s = 0, int(parts[0]), int(parts[1])
        else:
            return raw
    except ValueError:
        return raw
    total_min = h * 60 + m + (1 if s >= 30 else 0)
    if h > 0:
        return f"{h} hr {m} min" if m else f"{h} hr"
    return f"{total_min} min" if total_min else f"{m} min"


def iso_duration_from_itunes(raw: str | None) -> str | None:
    if not raw:
        return None
    parts = raw.strip().split(":")
    try:
        if len(parts) == 3:
            h, m, s = int(parts[0]), int(parts[1]), int(parts[2])
        elif len(parts) == 2:
            h, m, s = 0, int(parts[0]), int(parts[1])
        else:
            return None
    except ValueError:
        return None
    if h:
        return f"PT{h}H{m}M{s}S"
    if m:
        return f"PT{m}M{s}S" if s else f"PT{m}M"
    return f"PT{s}S"


def norm_title(s: str) -> str:
    s = html.unescape(s).lower()
    s = re.sub(r"^ep\.\s*\d+\s*:?\s*", "", s, flags=re.I)
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def rss_episode_number(item: ET.Element, slug: str) -> int:
    if slug == COMING_SOON_SLUG:
        return 0
    el = item.find("itunes:episode", NS)
    if el is not None and el.text and el.text.strip().isdigit():
        return int(el.text.strip())
    t = item.findtext("title") or ""
    m = re.match(r"^Ep\.\s*(\d+)\b", t.strip())
    if m:
        return int(m.group(1))
    return -1


def parse_rss(xml_text: str) -> dict[str, dict]:
    root = ET.fromstring(xml_text)
    by_play: dict[str, dict] = {}
    for item in root.findall("./channel/item"):
        enc = item.find("enclosure")
        if enc is None:
            continue
        url = enc.get("url") or ""
        pid = play_id_from_anchor_url(url)
        if not pid:
            continue
        title = (item.findtext("title") or "").strip()
        desc = item.findtext("description") or item.findtext(
            "{http://purl.org/rss/1.0/modules/content/}encoded"
        ) or ""
        it_img = item.find("itunes:image", NS)
        img_href = it_img.get("href") if it_img is not None else None
        dur = None
        d_el = item.find("itunes:duration", NS)
        if d_el is not None and d_el.text:
            dur = d_el.text.strip()
        by_play[pid] = {
            "title": title,
            "description_html": desc,
            "itunes_image": img_href,
            "duration_raw": dur,
            "enclosure_url": url,
            "_item": item,
        }
    return by_play


def parse_youtube_playlist(xml_text: str) -> list[dict]:
    root = ET.fromstring(xml_text)
    out: list[dict] = []
    for ent in root.findall("atom:entry", NS):
        vid_el = ent.find("yt:videoId", NS)
        video_id = vid_el.text if vid_el is not None else None
        if not video_id:
            continue
        link = ent.find("atom:link", NS)
        href = link.get("href") if link is not None else ""
        # Prefer long-form /watch/ URLs for matching; still index Shorts by id for thumbnails.
        is_watch = "/watch?v=" in href or "watch%3Fv%3D" in href
        title_el = ent.find("atom:title", NS)
        title = (title_el.text or "").strip()
        thumb = None
        group = ent.find("media:group", NS)
        if group is not None:
            th = group.find("media:thumbnail", NS)
            if th is not None:
                thumb = th.get("url")
        out.append(
            {
                "video_id": video_id,
                "title": title,
                "thumb": thumb or f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg",
                "norm": norm_title(title),
                "is_watch": is_watch,
            }
        )
    return out


def fetch_youtube_playlist_via_api(api_key: str, playlist_id: str) -> list[dict]:
    """All items in the uploads playlist (paginated). Requires YouTube Data API v3 key."""
    import urllib.parse

    out: list[dict] = []
    page_token: str | None = None
    while True:
        q = {
            "part": "snippet",
            "playlistId": playlist_id,
            "maxResults": "50",
            "key": api_key,
        }
        if page_token:
            q["pageToken"] = page_token
        url = "https://www.googleapis.com/youtube/v3/playlistItems?" + urllib.parse.urlencode(
            q
        )
        raw = fetch(url)
        payload = json.loads(raw)
        for it in payload.get("items") or []:
            sn = it.get("snippet") or {}
            resource = sn.get("resourceId") or {}
            video_id = resource.get("videoId")
            title = (sn.get("title") or "").strip()
            if not video_id:
                continue
            thumbs = sn.get("thumbnails") or {}
            th = (
                (thumbs.get("high") or {}).get("url")
                or (thumbs.get("medium") or {}).get("url")
                or f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"
            )
            out.append(
                {
                    "video_id": video_id,
                    "title": title,
                    "thumb": th,
                    "norm": norm_title(title),
                    "is_watch": True,
                }
            )
        page_token = payload.get("nextPageToken")
        if not page_token:
            break
    return out


def load_youtube_overrides(root: Path) -> dict[str, str]:
    p = root / "scripts" / "podcast-youtube-overrides.json"
    if not p.is_file():
        return {}
    data = json.loads(p.read_text(encoding="utf-8"))
    out: dict[str, str] = {}
    if not isinstance(data, dict):
        return out
    for k, v in data.items():
        if k.startswith("_"):
            continue
        if isinstance(k, str) and isinstance(v, str) and len(v) == 11:
            out[k] = v
    return out


def match_youtube(rss_title: str, yt: list[dict], min_ratio: float = 0.72) -> dict | None:
    n = norm_title(rss_title)
    if len(n) < 8:
        return None
    scored = []
    for row in yt:
        r = SequenceMatcher(None, n, row["norm"]).ratio()
        scored.append((r, row))
    if not scored:
        return None
    scored.sort(
        key=lambda x: (x[0], 1 if x[1].get("is_watch") else 0),
        reverse=True,
    )
    best_r, best = scored[0]
    if best_r >= min_ratio:
        return best
    return None


def extract_audio_play_id(page_html: str) -> str | None:
    m = re.search(r'<audio[^>]+src="([^"]+)"', page_html)
    if not m:
        m = re.search(r'"contentUrl":"(https://anchor\.fm[^"]+)"', page_html)
    if not m:
        return None
    return play_id_from_anchor_url(m.group(1))


def patch_episode_json_ld(html: str, updates: dict) -> str:
    def repl_script(m: re.Match) -> str:
        raw = m.group(1).strip()
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return m.group(0)
        if data.get("@type") != "PodcastEpisode":
            return m.group(0)
        for k, v in updates.items():
            if v is None:
                data.pop(k, None)
            else:
                data[k] = v
        return '<script type="application/ld+json">' + json.dumps(
            data, ensure_ascii=False
        ) + "</script>"

    return re.sub(
        r'<script type="application/ld\+json">\s*(.*?)\s*</script>',
        repl_script,
        html,
        flags=re.DOTALL,
    )


def load_transcript(transcripts_dir: Path, ep_num: int, slug: str) -> str | None:
    if not transcripts_dir.is_dir():
        return None
    pad = f"{ep_num:03d}"
    names = [
        f"ppp-ep-{pad}-{slug}.html",
        f"ppp-ep-{pad}-{slug}.md",
        f"ppp-ep-{pad}-{slug}.txt",
        f"ppp-ep-{pad}.html",
        f"ppp-ep-{pad}.md",
        f"ppp-ep-{pad}.txt",
    ]
    for name in names:
        p = transcripts_dir / name
        if p.is_file():
            text = p.read_text(encoding="utf-8", errors="replace")
            suf = p.suffix.lower()
            if suf == ".html":
                return sanitize_show_notes(text)
            if suf == ".txt":
                return f'<div class="episode-transcript__body episode-transcript__body--plain">{html.escape(text)}</div>'
            return md_light_to_html(text)
    return None


def md_light_to_html(md: str) -> str:
    parts: list[str] = []
    for block in re.split(r"\n{2,}", md.strip()):
        block = block.strip()
        if not block:
            continue
        if block.startswith("### "):
            parts.append(f"<h4>{html.escape(block[4:].strip())}</h4>")
        elif block.startswith("## "):
            parts.append(f"<h3>{html.escape(block[3:].strip())}</h3>")
        elif block.startswith("# "):
            parts.append(f"<h2>{html.escape(block[2:].strip())}</h2>")
        else:
            parts.append(f"<p>{html.escape(block)}</p>")
    return '<div class="episode-transcript__body">' + "\n".join(parts) + "</div>"


def inject_or_replace_transcript(html: str, inner: str | None) -> str:
    if not inner:
        html = re.sub(
            r'<section class="episode-transcript"[^>]*>.*?</section>',
            "",
            html,
            flags=re.DOTALL,
        )
        return html
    block = (
        '<section class="episode-transcript" id="transcript" aria-label="Transcript">'
        '<h2 class="episode-transcript__title">Transcript</h2>'
        f"{inner}</section>"
    )
    if 'class="episode-transcript"' in html:
        return re.sub(
            r'<section class="episode-transcript"[^>]*>.*?</section>',
            block,
            html,
            count=1,
            flags=re.DOTALL,
        )
    return html.replace("</div></article><aside", f"</div>{block}</article><aside", 1)


def patch_episode_page(
    path: Path,
    rss_row: dict,
    item: ET.Element,
    slug: str,
    yt_match: dict | None,
    transcripts_dir: Path,
    drive_thumb_file_id: str | None,
) -> dict:
    page_html = path.read_text(encoding="utf-8", errors="replace")
    ep_num = rss_episode_number(item, slug)
    dur_p = duration_pretty(rss_row["duration_raw"])
    ep_label = str(ep_num) if ep_num >= 0 else "—"
    hero_lede_new = f'<p class="hero__lede mt-3">Episode {ep_label} · {dur_p}</p>'

    page_html = re.sub(
        r'<p class="hero__lede mt-3">Episode <!-- --> · <!-- -->[^<]*</p>',
        hero_lede_new,
        page_html,
        count=1,
    )

    drive_url = (
        drive_thumbnail_image_url(drive_thumb_file_id) if drive_thumb_file_id else None
    )
    thumb = (
        drive_url
        or (
            f"https://i.ytimg.com/vi/{yt_match['video_id']}/hqdefault.jpg"
            if yt_match
            else None
        )
        or rss_row.get("itunes_image")
    )
    if thumb:
        page_html = patch_preload_episode_thumb(page_html, thumb)
        page_html = re.sub(
            r'(<img src=")([^"]+)(" alt="[^"]*" style="border-radius:8px;box-shadow:0 12px 36px rgba\(20, 33, 26, 0\.40\)")',
            rf"\1{html.escape(thumb, quote=True)}\3",
            page_html,
            count=1,
        )
        page_html = page_html.replace(
            '<meta property="og:image" content="https://peakpropertyperformance.com/public/images/og-image.png"/>',
            f'<meta property="og:image" content="{html.escape(thumb, quote=True)}"/>',
            1,
        )
        page_html = page_html.replace(
            '<meta name="twitter:image" content="https://peakpropertyperformance.com/public/images/og-image.png"/>',
            f'<meta name="twitter:image" content="{html.escape(thumb, quote=True)}"/>',
            1,
        )

    notes = sanitize_show_notes(rss_row["description_html"])

    def repl_rich(_m: re.Match) -> str:
        return _m.group(1) + notes + _m.group(2)

    page_html = re.sub(
        r'(<div class="rich-content">)[\s\S]*?(</div></article>)',
        repl_rich,
        page_html,
        count=1,
    )

    tr = load_transcript(transcripts_dir, ep_num, slug) if ep_num >= 0 else None
    page_html = inject_or_replace_transcript(page_html, tr)

    iso_dur = iso_duration_from_itunes(rss_row["duration_raw"])
    desc_plain = re.sub(r"<[^>]+>", " ", notes)
    desc_plain = html.unescape(re.sub(r"\s+", " ", desc_plain).strip())[:5000]

    json_updates = {
        "description": desc_plain,
    }
    if ep_num >= 0:
        json_updates["episodeNumber"] = ep_num
    if thumb:
        json_updates["image"] = thumb
    if iso_dur:
        json_updates["duration"] = iso_dur

    page_html = patch_episode_json_ld(page_html, json_updates)
    path.write_text(page_html, encoding="utf-8")

    return {
        "slug": slug,
        "episode_num": ep_num,
        "episode_label": ep_label,
        "duration_pretty": dur_p,
        "thumb": thumb,
    }


def patch_podcast_index(index_path: Path, card_meta: dict[str, dict]) -> None:
    import html as h_esc

    html_page = index_path.read_text(encoding="utf-8", errors="replace")

    def replace_card(m: re.Match) -> str:
        full = m.group(0)
        slug = m.group(1)
        meta = card_meta.get(slug)
        if not meta:
            return full
        thumb = meta.get("thumb") or ""
        ep = meta["episode_num"]
        lbl = meta.get("episode_label") or (str(ep) if ep >= 0 else "—")
        dur = meta["duration_pretty"]
        full = re.sub(
            r'(<div class="episode-card__art"><img src=")([^"]+)(" alt=")',
            rf"\1{h_esc.escape(thumb, quote=True)}\3",
            full,
            count=1,
        )
        full = re.sub(
            r'(<div class="episode-card__meta">)(.*?)(</div>)',
            rf"\1Episode {lbl} · {h_esc.escape(dur)}\3",
            full,
            count=1,
            flags=re.DOTALL,
        )
        return full

    pattern = re.compile(
        r'<a class="episode-card" href="\./([^/]+)/index\.html">.*?</a>',
        re.DOTALL,
    )
    index_path.write_text(pattern.sub(replace_card, html_page), encoding="utf-8")


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    podcast_dir = root / "podcast"
    transcripts_dir = Path(os.environ.get("PPP_TRANSCRIPTS_DIR", str(root / "transcripts")))

    print("Fetching RSS…", file=sys.stderr)
    rss_xml = fetch(RSS_URL)
    by_play = parse_rss(rss_xml)

    yt_overrides = load_youtube_overrides(root)

    drive_parent = os.environ.get(
        "DRIVE_EPISODES_PARENT_FOLDER_ID", DEFAULT_DRIVE_EPISODES_PARENT_ID
    ).strip()
    drive_key = (
        os.environ.get("GOOGLE_DRIVE_API_KEY", "")
        or os.environ.get("GOOGLE_API_KEY", "")
    ).strip()

    print("Resolving Drive episode thumbnails…", file=sys.stderr)
    drive_index = resolve_drive_thumbnail_file_index(root, drive_key, drive_parent)
    print(f"  {len(drive_index)} episodes with Drive thumbnail file ids", file=sys.stderr)

    print("Fetching YouTube…", file=sys.stderr)
    api_key = os.environ.get("YOUTUBE_API_KEY", "").strip()
    if api_key:
        yt_entries = fetch_youtube_playlist_via_api(api_key, YOUTUBE_UPLOADS_PLAYLIST_ID)
        print(f"  {len(yt_entries)} videos via Data API", file=sys.stderr)
    else:
        yt_url = f"https://www.youtube.com/feeds/videos.xml?playlist_id={YOUTUBE_UPLOADS_PLAYLIST_ID}"
        yt_entries = parse_youtube_playlist(fetch(yt_url))
        print(
            f"  {len(yt_entries)} videos from playlist RSS (~15 max; set YOUTUBE_API_KEY for full catalog)",
            file=sys.stderr,
        )

    card_meta: dict[str, dict] = {}
    missing_rss: list[str] = []
    missing_yt: list[str] = []
    missing_drive: list[str] = []

    for ep_dir in sorted(podcast_dir.iterdir()):
        if not ep_dir.is_dir():
            continue
        idx = ep_dir / "index.html"
        if not idx.is_file():
            continue
        slug = ep_dir.name
        page = idx.read_text(encoding="utf-8", errors="replace")
        pid = extract_audio_play_id(page)
        if not pid or pid not in by_play:
            missing_rss.append(slug)
            continue
        rss_row = by_play[pid]
        item = rss_row["_item"]
        rss_title = rss_row["title"]
        ep_num_pre = rss_episode_number(item, slug)

        drive_fid = drive_index.get(ep_num_pre) if ep_num_pre >= 0 else None
        if ep_num_pre >= 1 and not drive_fid:
            missing_drive.append(slug)

        yt_m = None
        if slug in yt_overrides:
            vid = yt_overrides[slug]
            yt_m = {
                "video_id": vid,
                "title": "",
                "thumb": f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg",
                "norm": "",
                "is_watch": True,
            }
        else:
            yt_m = match_youtube(rss_title, yt_entries)
        if not yt_m:
            missing_yt.append(slug)

        meta = patch_episode_page(
            idx,
            rss_row,
            item,
            slug,
            yt_m,
            transcripts_dir,
            drive_fid,
        )
        card_meta[slug] = meta
        print(f"OK {slug} → ep {meta['episode_num']}", file=sys.stderr)

    index_html = podcast_dir / "index.html"
    if index_html.is_file():
        patch_podcast_index(index_html, card_meta)
        print("OK podcast/index.html cards", file=sys.stderr)

    if missing_rss:
        print("WARN no RSS match for slugs:", ", ".join(missing_rss), file=sys.stderr)
    if missing_drive:
        print(
            "WARN no Drive thumbnail for episode (YouTube/RSS fallback):",
            ", ".join(missing_drive),
            file=sys.stderr,
        )
    if missing_yt:
        print(
            "WARN no YouTube match (Drive or RSS art may still apply):",
            ", ".join(missing_yt),
            file=sys.stderr,
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
