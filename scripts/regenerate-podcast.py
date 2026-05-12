#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Regenerate static podcast pages from Anchor RSS + YouTube uploads feed.

- Fixes double-encoded show notes (renders real HTML from RSS description).
- Sets episode numbers (0 = coming-soon slug; others from itunes:episode).
- Hero + listing card art: YouTube hqdefault when matched; else RSS itunes:image.
- Injects optional transcripts from PPP_TRANSCRIPTS_DIR (default ./transcripts).

Usage (repo root):
  python3 scripts/regenerate-podcast.py

Env:
  RSS_URL                          default Anchor feed for this show
  YOUTUBE_UPLOADS_PLAYLIST_ID      default UU… playlist for @PeakPropertyPerformance
  PPP_TRANSCRIPTS_DIR              default transcripts
"""

from __future__ import annotations

import html
import json
import os
import re
import sys
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
        link = ent.find("atom:link", NS)
        href = link.get("href") if link is not None else ""
        if "/watch?v=" not in href and "watch%3Fv%3D" not in href:
            continue
        vid_el = ent.find("yt:videoId", NS)
        video_id = vid_el.text if vid_el is not None else None
        if not video_id:
            continue
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
            }
        )
    return out


def match_youtube(rss_title: str, yt: list[dict], min_ratio: float = 0.72) -> dict | None:
    n = norm_title(rss_title)
    if len(n) < 8:
        return None
    best = None
    best_r = 0.0
    for row in yt:
        r = SequenceMatcher(None, n, row["norm"]).ratio()
        if r > best_r:
            best_r = r
            best = row
    if best is not None and best_r >= min_ratio:
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
) -> dict:
    html = path.read_text(encoding="utf-8", errors="replace")
    ep_num = rss_episode_number(item, slug)
    if ep_num < 0:
        ep_num = 0
    dur_p = duration_pretty(rss_row["duration_raw"])
    ep_label = str(ep_num)
    hero_lede_new = f'<p class="hero__lede mt-3">Episode {ep_label} · {dur_p}</p>'

    html = re.sub(
        r'<p class="hero__lede mt-3">Episode <!-- --> · <!-- -->[^<]*</p>',
        hero_lede_new,
        html,
        count=1,
    )

    thumb = (
        f"https://i.ytimg.com/vi/{yt_match['video_id']}/hqdefault.jpg"
        if yt_match
        else rss_row.get("itunes_image")
    )
    if thumb:
        html = re.sub(
            r'(<link rel="preload" as="image" href=")([^"]*podcast_uploaded[^"]+)(")',
            rf'\1{html.escape(thumb, quote=True)}\3',
            html,
            count=1,
        )
        html = re.sub(
            r'(<img src=")([^"]+)(" alt="[^"]*" style="border-radius:8px;box-shadow:0 12px 36px rgba\(20, 33, 26, 0\.40\)")',
            rf"\1{html.escape(thumb, quote=True)}\3",
            html,
            count=1,
        )
        html = html.replace(
            '<meta property="og:image" content="https://peakpropertyperformance.com/public/images/og-image.png"/>',
            f'<meta property="og:image" content="{html.escape(thumb, quote=True)}"/>',
            1,
        )
        html = html.replace(
            '<meta name="twitter:image" content="https://peakpropertyperformance.com/public/images/og-image.png"/>',
            f'<meta name="twitter:image" content="{html.escape(thumb, quote=True)}"/>',
            1,
        )

    notes = sanitize_show_notes(rss_row["description_html"])

    def repl_rich(_m: re.Match) -> str:
        return _m.group(1) + notes + _m.group(2)

    html = re.sub(
        r'(<div class="rich-content">)[\s\S]*?(</div></article>)',
        repl_rich,
        html,
        count=1,
    )

    tr = load_transcript(transcripts_dir, ep_num, slug)
    html = inject_or_replace_transcript(html, tr)

    iso_dur = iso_duration_from_itunes(rss_row["duration_raw"])
    desc_plain = re.sub(r"<[^>]+>", " ", notes)
    desc_plain = html.unescape(re.sub(r"\s+", " ", desc_plain).strip())[:5000]

    json_updates = {
        "episodeNumber": ep_num,
        "description": desc_plain,
    }
    if thumb:
        json_updates["image"] = thumb
    if iso_dur:
        json_updates["duration"] = iso_dur

    html = patch_episode_json_ld(html, json_updates)
    path.write_text(html, encoding="utf-8")

    return {
        "slug": slug,
        "episode_num": ep_num,
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
        dur = meta["duration_pretty"]
        full = re.sub(
            r'(<div class="episode-card__art"><img src=")([^"]+)(" alt=")',
            rf"\1{h_esc.escape(thumb, quote=True)}\3",
            full,
            count=1,
        )
        full = re.sub(
            r'(<div class="episode-card__meta">)([^<]+)(</div>)',
            rf"\1Episode {ep} · {h_esc.escape(dur)}\3",
            full,
            count=1,
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

    print("Fetching YouTube playlist…", file=sys.stderr)
    yt_url = f"https://www.youtube.com/feeds/videos.xml?playlist_id={YOUTUBE_UPLOADS_PLAYLIST_ID}"
    yt_entries = parse_youtube_playlist(fetch(yt_url))
    print(f"  {len(yt_entries)} watch URLs", file=sys.stderr)

    card_meta: dict[str, dict] = {}
    missing_rss: list[str] = []
    missing_yt: list[str] = []

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
        yt_m = match_youtube(rss_title, yt_entries)
        if not yt_m:
            missing_yt.append(slug)

        meta = patch_episode_page(
            idx, rss_row, item, slug, yt_m, transcripts_dir
        )
        card_meta[slug] = meta
        print(f"OK {slug} → ep {meta['episode_num']}", file=sys.stderr)

    index_html = podcast_dir / "index.html"
    if index_html.is_file():
        patch_podcast_index(index_html, card_meta)
        print("OK podcast/index.html cards", file=sys.stderr)

    if missing_rss:
        print("WARN no RSS match for slugs:", ", ".join(missing_rss), file=sys.stderr)
    if missing_yt:
        print("WARN no YouTube thumb match (using RSS art):", ", ".join(missing_yt), file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
