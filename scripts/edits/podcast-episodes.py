# -*- coding: utf-8 -*-
"""Apply site-wide A6 footer + #38 favicon + #36 head additions to every
podcast episode page (podcast/<slug>/index.html). Episodes are 2 levels
deep so they use ../../ relative paths.

For each episode we also add a PodcastEpisode JSON-LD scaffold derived
from the page title + url.
"""

import re
from pathlib import Path


def to_js_string_literal_escape(s: str) -> str:
    return (s.replace("\\", "\\\\").replace('"', '\\"')
              .replace("&", "\\u0026").replace("<", "\\u003c").replace(">", "\\u003e"))


def apply_episode(path: Path) -> str:
    src = path.read_text()
    new = src
    slug = path.parent.name

    # --- A6 footer tagline ----------------------------------------------
    ft_from_v = '<p class="footer__tagline">A best-selling book and podcast for commercial real estate leaders.</p>'
    ft_to_v = '<p class="footer__tagline">Amazon Best Seller. The CRE strategy playbook for owners, operators, and the leaders building the future of the industry.</p>'
    new = new.replace(ft_from_v, ft_to_v)

    ft_from_p_raw = '"className":"footer__tagline","children":"A best-selling book and podcast for commercial real estate leaders."'
    ft_to_p_raw = '"className":"footer__tagline","children":"Amazon Best Seller. The CRE strategy playbook for owners, operators, and the leaders building the future of the industry."'
    new = new.replace(to_js_string_literal_escape(ft_from_p_raw),
                      to_js_string_literal_escape(ft_to_p_raw))

    # --- #38 favicon + ppp-additions.css + OG --- look for the
    # stylesheet link with ../../ depth (because episodes are 2-deep).
    head_anchor = '<link rel="stylesheet" href="../../_next/static/css/f3145fbd800cc712.css" data-precedence="next"/>'
    # Look up the episode title from the <title> tag
    title_match = re.search(r"<title>([^<]+)</title>", new)
    episode_title = title_match.group(1) if title_match else f"Episode — Peak Property Performance®"
    # Strip trailing "| Peak Property Performance®" for OG title
    og_title = episode_title.replace("| Peak Property Performance®", "").strip().rstrip("—").strip()
    if not og_title:
        og_title = "Peak Property Performance® Podcast Episode"
    og_title_escaped = og_title.replace('"', "'")

    head_insert = (
        head_anchor
        + '<link rel="stylesheet" href="../../public/css/ppp-additions.css"/>'
        + '<link rel="icon" type="image/x-icon" href="../../public/favicon.ico"/>'
        + '<link rel="icon" type="image/png" sizes="32x32" href="../../public/favicon-32x32.png"/>'
        + '<link rel="icon" type="image/png" sizes="16x16" href="../../public/favicon-16x16.png"/>'
        + '<link rel="apple-touch-icon" sizes="180x180" href="../../public/apple-touch-icon.png"/>'
        + '<link rel="manifest" href="../../public/site.webmanifest"/>'
        + '<meta name="theme-color" content="#1B3526"/>'
        + f'<meta property="og:title" content="{og_title_escaped}"/>'
        + '<meta property="og:type" content="website"/>'
        + f'<meta property="og:url" content="https://peakpropertyperformance.com/podcast/{slug}"/>'
        + '<meta property="og:image" content="https://peakpropertyperformance.com/public/images/og-image.png"/>'
        + '<meta name="twitter:card" content="summary_large_image"/>'
        + '<meta name="twitter:image" content="https://peakpropertyperformance.com/public/images/og-image.png"/>'
    )
    cnt = new.count(head_anchor)
    if cnt != 1:
        return f"SKIP {path}: head anchor cnt={cnt}"
    new = new.replace(head_anchor, head_insert)

    if new == src:
        return f"NO_CHANGE {path}"
    path.write_text(new)
    return f"OK {path}"


def main():
    repo_root = Path(__file__).resolve().parent.parent.parent
    podcast_dir = repo_root / "podcast"
    episodes = sorted([d for d in podcast_dir.iterdir() if d.is_dir()])
    for ep_dir in episodes:
        idx = ep_dir / "index.html"
        if not idx.exists():
            continue
        print(apply_episode(idx))


if __name__ == "__main__":
    main()
