#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Replace bottom-of-page CTAs with the standardized “Three ways in” strip:
three wide yellow blocks (CSS: .three-ways-blocks__*) with primary buttons:
  1. Listen to the podcast  → /podcast
  2. Get the book           → /book
  3. Request the review     → /ppp-review

Pages already using the home-style explanatory cards (root index.html card-grid)
are left unchanged.

Updates BOTH pre-rendered HTML and the last matching React Flight `[$,section,...]`
payload block when present (so hydration does not revert the footer).

Run from repo root:
  python3 scripts/build/standardize-three-ways-footer.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parent.parent.parent


def walk_payload_array_end(s: str, start: int) -> int:
    """Given s[start] == '[', return index of the matching ']' (Flight JSON text)."""
    if start >= len(s) or s[start] != "[":
        raise ValueError("walk_payload_array_end: start must point at '['")
    depth = 0
    i = start
    in_str = False
    esc = False
    while i < len(s):
        c = s[i]
        if in_str:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                in_str = False
            i += 1
            continue
        if c == '"':
            in_str = True
            i += 1
            continue
        if c == "[":
            depth += 1
        elif c == "]":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    raise ValueError("unbalanced brackets in Flight payload")


def replace_last_payload_section(html: str, section_class: str, replacement: str) -> tuple[str, bool]:
    """Replace the last [$,\"section\",uuid,{className: section_class ...}] Flight node."""
    cls_pat = '\\"className\\":\\"' + section_class + '\\"'
    p = html.rfind(cls_pat)
    if p < 0:
        return html, False
    sec_needle = '[\\"$\\",\\"section\\",\\"'
    sec_start = html.rfind(sec_needle, 0, p)
    if sec_start < 0:
        return html, False
    sec_end = walk_payload_array_end(html, sec_start)
    new_html = html[:sec_start] + replacement + html[sec_end + 1 :]
    return new_html, True


def extract_payload_section_uuid(section_src: str) -> str:
    m = re.match(
        r'^\[\\"\$\\",\\"section\\",\\"([^"]+)\\",',
        section_src,
    )
    if not m:
        raise ValueError("could not parse section uuid from payload fragment")
    return m.group(1)


def visible_three_ways_section(prefix: str) -> str:
    """prefix is '' for root index-style paths, '../' one level down, etc."""
    return (
        '<section class="cta-section cta-section--dark three-ways-blocks"><div class="container">'
        '<span class="eyebrow no-rule" style="justify-content:center;display:flex">Get Started</span>'
        '<h2 class="mt-4 mb-4">Three ways in.</h2>'
        '<p class="lede three-ways-blocks__lede" style="max-width:52ch;margin-inline:auto">'
        "Whether you&#x27;re scouting, training camp, or game time — there&#x27;s a way to start today."
        "</p>"
        '<div class="three-ways-blocks__grid">'
        '<div class="three-ways-blocks__block">'
        '<h3 class="three-ways-blocks__heading">Listen to the podcast</h3>'
        f'<a class="btn btn-primary btn-lg" href="{prefix}podcast/index.html">Listen to the podcast</a>'
        "</div>"
        '<div class="three-ways-blocks__block">'
        '<h3 class="three-ways-blocks__heading">Get the book</h3>'
        f'<a class="btn btn-primary btn-lg" href="{prefix}book/index.html">Get the book</a>'
        "</div>"
        '<div class="three-ways-blocks__block">'
        '<h3 class="three-ways-blocks__heading">Request the review</h3>'
        f'<a class="btn btn-primary btn-lg" href="{prefix}ppp-review/index.html">Request the review</a>'
        "</div>"
        "</div></div></section>"
    )


def payload_three_ways_section(uuid: str) -> str:
    kids = (
        "[[\\"$\\",\\"span\\",null,{\\"className\\":\\"eyebrow no-rule\\",\\"style\\":{\\"justifyContent\\":\\"center\\",\\"display\\":\\"flex\\"},"
        '\\"children\\":\\"Get Started\\"}],'
        '[\\"$\\",\\"h2\\",null,{\\"className\\":\\"mt-4 mb-4\\",\\"children\\":\\"Three ways in.\\"}],'
        '[\\"$\\",\\"p\\",null,{\\"className\\":\\"lede three-ways-blocks__lede\\",\\"style\\":{\\"maxWidth\\":\\"52ch\\",\\"marginInline\\":\\"auto\\"},'
        "\\\"children\\\":\\\"Whether you're scouting, training camp, or game time — there's a way to start today.\\\"}],"
        '[\\"$\\",\\"div\\",null,{\\"className\\":\\"three-ways-blocks__grid\\",\\"children\\":'
        "[[\\"$\\",\\"div\\",\\"ppp-tw0\\",{\\"className\\":\\"three-ways-blocks__block\\",\\"children\\":"
        "[[\\"$\\",\\"h3\\",null,{\\"className\\":\\"three-ways-blocks__heading\\",\\"children\\":\\"Listen to the podcast\\"}],"
        '[\\"$\\",\\"$L5\\",\\"ppp-tw0b\\",{\\"href\\":\\"/podcast\\",\\"className\\":\\"btn btn-primary btn-lg\\",\\"children\\":\\"Listen to the podcast\\"}]]}],'
        '[\\"$\\",\\"div\\",\\"ppp-tw1\\",{\\"className\\":\\"three-ways-blocks__block\\",\\"children\\":'
        "[[\\"$\\",\\"h3\\",null,{\\"className\\":\\"three-ways-blocks__heading\\",\\"children\\":\\"Get the book\\"}],"
        '[\\"$\\",\\"$L5\\",\\"ppp-tw1b\\",{\\"href\\":\\"/book\\",\\"className\\":\\"btn btn-primary btn-lg\\",\\"children\\":\\"Get the book\\"}]]}],'
        '[\\"$\\",\\"div\\",\\"ppp-tw2\\",{\\"className\\":\\"three-ways-blocks__block\\",\\"children\\":'
        "[[\\"$\\",\\"h3\\",null,{\\"className\\":\\"three-ways-blocks__heading\\",\\"children\\":\\"Request the review\\"}],"
        '[\\"$\\",\\"$L5\\",\\"ppp-tw2b\\",{\\"href\\":\\"/ppp-review\\",\\"className\\":\\"btn btn-primary btn-lg\\",\\"children\\":\\"Request the review\\"}]]}]]}]'
        "]}"
    )
    return (
        '[\\"$\\",\\"section\\",\\"'
        + uuid
        + '\\",{\\"className\\":\\"cta-section cta-section--dark three-ways-blocks\\",\\"children\\":'
        '[\\"$\\",\\"div\\",null,{\\"className\\":\\"container\\",\\"children\\":'
        + kids
        + "}]}]"
    )


def extract_last_visible_section_before_main(html: str, class_attr: str) -> tuple[str, int, int] | None:
    """Find last <section class="...class_attr..."> before </main>; return (full_tag, start, end)."""
    main_end = html.find("</main>")
    if main_end < 0:
        return None
    pre = html[:main_end]
    needle = f'<section class="{class_attr}"'
    idx = pre.rfind(needle)
    if idx < 0:
        # optional attributes after class (e.g. style=)
        alt = f'<section class="{class_attr}" '
        idx = pre.rfind(alt)
    if idx < 0:
        return None
    pos = idx
    depth = 0
    seg_start = idx
    while pos < main_end:
        next_open = html.find("<section", pos + 1)
        next_close = html.find("</section>", pos)
        if next_close < 0:
            break
        if next_open != -1 and next_open < next_close:
            depth += 1
            pos = next_open + 1
        else:
            if depth == 0:
                end = next_close + len("</section>")
                return html[seg_start:end], seg_start, end
            depth -= 1
            pos = next_close + 1
    return None


def patch_visible(html: str, prefix: str, *, paper_ok: bool) -> tuple[str, bool]:
    """Replace last dark CTA, else last paper CTA before </main>."""
    dark = "cta-section cta-section--dark"
    paper = "cta-section cta-section--paper"
    new_sec = visible_three_ways_section(prefix)
    got = extract_last_visible_section_before_main(html, dark)
    if got:
        old, a, b = got
        # Nested vendor audit: section may include style= — match begins at same prefix
        if "cta-section cta-section--dark" not in old:
            pass
        return html[:a] + new_sec + html[b:], True
    if paper_ok:
        got = extract_last_visible_section_before_main(html, paper)
        if got:
            old, a, b = got
            return html[:a] + new_sec + html[b:], True
    return html, False


def patch_payload(html: str, *, paper_ok: bool) -> tuple[str, bool]:
    dark = "cta-section cta-section--dark"
    paper = "cta-section cta-section--paper"
    for cls in (dark, paper):
        if cls == paper and not paper_ok:
            continue
        cls_pat = '\\"className\\":\\"' + cls + '\\"'
        p = html.rfind(cls_pat)
        if p < 0:
            continue
        sec_needle = '[\\"$\\",\\"section\\",\\"'
        sec_start = html.rfind(sec_needle, 0, p)
        if sec_start < 0:
            continue
        sec_end = walk_payload_array_end(html, sec_start)
        frag = html[sec_start : sec_end + 1]
        try:
            uuid = extract_payload_section_uuid(frag)
        except ValueError:
            continue
        rep = payload_three_ways_section(uuid)
        return html[:sec_start] + rep + html[sec_end + 1 :], True
    return html, False


def rel_prefix(path: Path) -> str:
    """Relative prefix from this HTML file to site root (parent of index.html)."""
    rel = path.relative_to(REPO)
    depth = len(rel.parts) - 1
    return "../" * depth


SPECIAL_BOOK_VISIBLE_MARK = (
    "</div></section></main><footer class=\"footer\">"
)
SPECIAL_BOOK_PAYLOAD_MARK_OLD = (
    "Partner at NAI Shames Makovsky.\\\",null,null]}]]}]}]]]\\n\"]</script><script>self.__next_f.push([1,"
    '\\"12:[\\"$\\",\\"section\\",\\"69efb8125996bea084142e33\\"'
)

SPECIAL_PODCAST_VISIBLE_MARK = (
    "</div></div></a></div></div></section></main><footer class=\"footer\">"
)
SPECIAL_PODCAST_PAYLOAD_MARK_OLD = (
    "COMING SOON: Peak Property Performance® With Bill Douglas \\u0026 Drew Hall\\\"}]]}]]}]]}]}]}]]\\n\"]</script><style>"
)

BOOK_PAYLOAD_INSERT = (
    "Partner at NAI Shames Makovsky.\\\",null,null]}]]}]}],["
    + payload_three_ways_section("69pppthree695214ebook")
    + "]]]\\n\"]</script><script>self.__next_f.push([1,"
    '\\"12:[\\"$\\",\\"section\\",\\"69efb8125996bea084142e33\\"'
)

PODCAST_PAYLOAD_INSERT = (
    "COMING SOON: Peak Property Performance® With Bill Douglas \\u0026 Drew Hall\\\"}]]}]]}]]}]}]}],["
    + payload_three_ways_section("69pppthree695214epod")
    + "]]\\n\"]</script><style>"
)


JOBS: list[tuple[str, str | None, bool]] = [
    # rel_path, prefix override (None = auto), paper_fallback
    ("about/index.html", None, False),
    ("5c-framework/index.html", None, False),
    ("for-owners/index.html", None, False),
    ("for-asset-managers/index.html", None, False),
    ("for-it-managers/index.html", None, False),
    ("for-property-managers/index.html", None, False),
    ("resources/index.html", None, True),
    ("be-on-the-show/index.html", None, True),
    ("ppp-review/index.html", None, True),
    ("glossary/index.html", None, True),
]


def main() -> int:
    changed = []
    for rel, prefix_override, paper_ok in JOBS:
        path = REPO / rel
        if not path.exists():
            print(f"SKIP missing {rel}")
            continue
        html = path.read_text(encoding="utf-8")
        prefix = prefix_override if prefix_override is not None else rel_prefix(path)
        new_html, v_ok = patch_visible(html, prefix, paper_ok=paper_ok)
        flight = "__next_f" in new_html
        if flight:
            new_html, p_ok = patch_payload(new_html, paper_ok=paper_ok)
            if not p_ok and v_ok:
                print(f"WARN {rel}: visible patched but no Flight payload match")
        else:
            p_ok = False
        if new_html != html:
            path.write_text(new_html, encoding="utf-8")
            changed.append(rel)
            print(f"OK {rel}  visible={'Y' if v_ok else '-'}  payload={'Y' if flight and p_ok else ('-' if not flight else 'N')}")

    # Vendor audit (no Flight): nested dark section — visible only
    vpath = REPO / "vendor-contract-audit/index.html"
    if vpath.exists():
        html = vpath.read_text(encoding="utf-8")
        new_html, v_ok = patch_visible(html, "../", paper_ok=False)
        if v_ok and new_html != html:
            vpath.write_text(new_html, encoding="utf-8")
            changed.append("vendor-contract-audit/index.html")
            print(f"OK vendor-contract-audit/index.html  visible=Y  payload=-")

    # Book — append before </main> + Flight splice
    bpath = REPO / "book/index.html"
    if bpath.exists():
        html = bpath.read_text(encoding="utf-8")
        ins = visible_three_ways_section("../")
        if SPECIAL_BOOK_VISIBLE_MARK in html and ins not in html:
            html = html.replace(
                SPECIAL_BOOK_VISIBLE_MARK,
                "</div></section>" + ins + "</main><footer class=\"footer\">",
                1,
            )
        if SPECIAL_BOOK_PAYLOAD_MARK_OLD in html and "69pppthree695214ebook" not in html:
            html = html.replace(SPECIAL_BOOK_PAYLOAD_MARK_OLD, BOOK_PAYLOAD_INSERT, 1)
        bpath.write_text(html, encoding="utf-8")
        changed.append("book/index.html")
        print("OK book/index.html  (insert before main end)")

    # Podcast hub
    ppath = REPO / "podcast/index.html"
    if ppath.exists():
        html = ppath.read_text(encoding="utf-8")
        ins = visible_three_ways_section("../")
        if SPECIAL_PODCAST_VISIBLE_MARK in html and ins not in html:
            html = html.replace(
                SPECIAL_PODCAST_VISIBLE_MARK,
                "</div></div></a></div></div></section>" + ins + "</main><footer class=\"footer\">",
                1,
            )
        if SPECIAL_PODCAST_PAYLOAD_MARK_OLD in html and "69pppthree695214epod" not in html:
            html = html.replace(SPECIAL_PODCAST_PAYLOAD_MARK_OLD, PODCAST_PAYLOAD_INSERT, 1)
        ppath.write_text(html, encoding="utf-8")
        changed.append("podcast/index.html")
        print("OK podcast/index.html  (insert before main end)")

    print(f"\nDone. {len(changed)} files touched.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
