# -*- coding: utf-8 -*-
"""Rewrite root-absolute internal hrefs (/book, …) to relative URLs for static export.

Includes Next.js Flight JSON segments like {\\"href\\":\\"/book\\"}

Also fixes role-page episode stubs that pointed at non-exported slug paths (/podcast/ep-XX-…).

Run from repo root: python3 scripts/fix-internal-nav-links.py
"""

from __future__ import annotations

import re
from pathlib import Path

# Canonical site paths exported as folders -> index.html
# These appear on the broken pages as `/podcast/ep-NN-…` aliases.
_EPISODE_ALIASES: tuple[tuple[str, str], ...] = (
    (
        "/podcast/ep-32-when-technology-sprawl-meets-real-estate-managing-risk-and-control-in",
        "/podcast/when-technology-sprawl-meets-real-estate-managing-risk-and-control-in-modern",
    ),
    (
        "/podcast/ep-33-when-underwriting-assumptions-meet-on-the-ground-challenges-in-property",
        "/podcast/when-underwriting-assumptions-meet-on-the-ground-challenges-in-property",
    ),
    # Ep 34 title not present in repo export — land on podcast index.
    (
        "/podcast/ep-34-changing-the-game-property-managers-as-asset-stewards-in-complex-digital",
        "/podcast",
    ),
)

# Visible HTML attributes: href="/…"
_HTML_HREF_RE = re.compile(r'href="(/[^\"]*)"')


def _flight_href_re() -> re.Pattern[str]:
    """Match JSON fragment {\"href\":\"/path\" inside Next Flight strings."""
    pfx = "".join(["{", chr(92), '"', "href", chr(92), '"', ":", chr(92), '"'])
    return re.compile(re.escape(pfx) + r'(/[^\\]*)\\"')


_FLIGHT_HREF_RE = _flight_href_re()


def _depth_from_site_relative(html_path: Path) -> int:
    """Segments above index.html inside site root."""
    parts = html_path.parts
    if parts[-1] != "index.html":
        raise ValueError(f"Expected index.html, got {html_path}")
    return max(0, len(parts) - 1)


def _prefix_at_depth(depth: int) -> str:
    return "../" * depth


def _internal_path_to_target(stripped: str) -> str:
    """Turn '' (home), 'book', 'podcast/slug', … into 'index.html' or 'slug/.../index.html'."""
    if not stripped:
        return "index.html"
    return f"{stripped}/index.html"


def _to_relative(site_rel: Path, raw_path: str) -> str:
    """`/book`, `/podcast/foo`, `/`, `#x` tails."""
    depth = _depth_from_site_relative(site_rel)
    prefix = _prefix_at_depth(depth)

    if raw_path.startswith("//"):
        raise ValueError("protocol-relative URLs should have been skipped")

    frag = ""
    p = raw_path
    if "#" in p:
        p, frag = p.split("#", 1)
        frag = "#" + frag

    if not p:
        # '/#foo'
        return f"{prefix}index.html{frag}"

    if not p.startswith("/"):
        raise ValueError(f"expected absolute internal path: {raw_path!r}")

    stripped = p.lstrip("/").rstrip("/")
    tail = _internal_path_to_target(stripped)
    return f"{prefix}{tail}{frag}"


def _apply_episode_aliases(s: str) -> str:
    out = s
    for old, new in _EPISODE_ALIASES:
        out = out.replace(old, new)
    return out


def _repl_html(site_rel: Path):
    def _cb(m: re.Match[str]) -> str:
        raw = m.group(1)
        if raw.startswith("//") or raw.startswith("/http"):
            return m.group(0)
        repl = _to_relative(site_rel, raw)
        return f'href="{repl}"'

    return _cb


def _repl_flight(site_rel: Path):
    pfx = "".join(["{", chr(92), '"', "href", chr(92), '"', ":", chr(92), '"'])

    def _cb(m: re.Match[str]) -> str:
        inner = m.group(1)
        if inner.startswith("//") or inner.startswith("/http"):
            return m.group(0)
        rel = _to_relative(site_rel, inner)
        esc = rel.replace("\\", "\\\\").replace('"', '\\"')
        return f'{pfx}{esc}\\"'

    return _cb


def patch_file(repo_root: Path, rel: Path) -> bool:
    path = repo_root / rel
    src = path.read_text(encoding="utf-8")
    s = _apply_episode_aliases(src)

    new = _HTML_HREF_RE.sub(_repl_html(rel), s)
    new = _FLIGHT_HREF_RE.sub(_repl_flight(rel), new)

    if new != src:
        path.write_text(new, encoding="utf-8")
        return True
    return False


def main() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    touched = []
    for p in sorted(repo_root.rglob("*.html")):
        site_rel = p.relative_to(repo_root)
        parts = site_rel.parts
        if parts[-1] != "index.html":
            continue
        if patch_file(repo_root, site_rel):
            touched.append(site_rel.as_posix())
    print(f"Patched {len(touched)} file(s)")
    for t in touched:
        print(f"  {t}")


if __name__ == "__main__":
    main()
