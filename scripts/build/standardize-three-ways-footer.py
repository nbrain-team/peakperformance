#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Standardize bottom-of-page CTAs to “Three ways in” + three yellow blocks.

Visible HTML + React Flight payload are both updated so hydration does not revert.

Homepage (index.html) card-grid “Three ways in” is intentionally unchanged.

Run from repo root:
  python3 scripts/build/standardize-three-ways-footer.py
"""

from __future__ import annotations

import sys
from pathlib import Path


REPO = Path(__file__).resolve().parent.parent.parent


def flight_array_end(s: str, start: int) -> int:
    """s[start] must be '['. Find matching ']' in Flight text using \\\" string rules."""
    i = start
    depth = 0
    in_str = False
    while i < len(s):
        if not in_str:
            if s.startswith('\\"', i):
                in_str = True
                i += 2
                continue
            if s[i] == "[":
                depth += 1
            elif s[i] == "]":
                depth -= 1
                if depth == 0:
                    return i
            i += 1
            continue
        if s.startswith('\\"', i):
            in_str = False
            i += 2
            continue
        if s[i] == "\\" and i + 1 < len(s):
            i += 2
            continue
        i += 1
    raise ValueError("unbalanced brackets in Flight payload")


def visible_three_ways_section(prefix: str) -> str:
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


# Fourth container column — mirrors cta__buttons tuple shape (…children:[[…]]]}])
NEW_GRID_TUPLE = (
    '[\\"$\\",\\"div\\",null,{\\"className\\":\\"three-ways-blocks__grid\\",\\"children\\":[['
    '[\\"$\\",\\"div\\",\\"ppp-tw0\\",{\\"className\\":\\"three-ways-blocks__block\\",\\"children\\":'
    '[[\\"$\\",\\"h3\\",null,{\\"className\\":\\"three-ways-blocks__heading\\",\\"children\\":\\"Listen to the podcast\\"}],'
    '[\\"$\\",\\"$L5\\",\\"ppp-tw0b\\",{\\"href\\":\\"/podcast\\",\\"className\\":\\"btn btn-primary btn-lg\\",\\"children\\":\\"Listen to the podcast\\"}]]}],'
    '[\\"$\\",\\"div\\",\\"ppp-tw1\\",{\\"className\\":\\"three-ways-blocks__block\\",\\"children\\":'
    '[[\\"$\\",\\"h3\\",null,{\\"className\\":\\"three-ways-blocks__heading\\",\\"children\\":\\"Get the book\\"}],'
    '[\\"$\\",\\"$L5\\",\\"ppp-tw1b\\",{\\"href\\":\\"/book\\",\\"className\\":\\"btn btn-primary btn-lg\\",\\"children\\":\\"Get the book\\"}]]}],'
    '[\\"$\\",\\"div\\",\\"ppp-tw2\\",{\\"className\\":\\"three-ways-blocks__block\\",\\"children\\":'
    '[[\\"$\\",\\"h3\\",null,{\\"className\\":\\"three-ways-blocks__heading\\",\\"children\\":\\"Request the review\\"}],'
    '[\\"$\\",\\"$L5\\",\\"ppp-tw2b\\",{\\"href\\":\\"/ppp-review\\",\\"className\\":\\"btn btn-primary btn-lg\\",\\"children\\":\\"Request the review\\"}]]}]'
    "]]}]"
)


def extract_last_visible_section_before_main(html: str, class_prefix: str):
    """Find last section with given class before </main>."""
    main_end = html.find("</main>")
    if main_end < 0:
        return None
    pre = html[:main_end]
    needle = f'<section class="{class_prefix}"'
    idx = pre.rfind(needle)
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
    new_sec = visible_three_ways_section(prefix)
    for cls in ("cta-section cta-section--dark",):
        got = extract_last_visible_section_before_main(html, cls)
        if got:
            old, a, b = got
            return html[:a] + new_sec + html[b:], True
    if paper_ok:
        got = extract_last_visible_section_before_main(html, "cta-section cta-section--paper")
        if got:
            old, a, b = got
            return html[:a] + new_sec + html[b:], True
    return html, False


def synthetic_footer_section(uuid: str) -> str:
    """Minimal valid footer Flight fragment for morph_footer_payload_fragment."""
    inner = (
        '[[\\"$\\",\\"span\\",null,{\\"className\\":\\"eyebrow no-rule\\",\\"style\\":{\\"justifyContent\\":\\"center\\",\\"display\\":\\"flex\\"},\\"children\\":\\"Get Started\\"}],'
        '[\\"$\\",\\"h2\\",null,{\\"className\\":\\"mt-4 mb-4\\",\\"children\\":\\"Three ways in.\\"}],'
        '[\\"$\\",\\"p\\",null,{\\"className\\":\\"lede\\",\\"style\\":{\\"maxWidth\\":\\"52ch\\",\\"marginInline\\":\\"auto\\"},\\"children\\":\\"Whether you\'re scouting\\"}],'
        '[\\"$\\",\\"div\\",null,{\\"className\\":\\"cta__buttons\\",\\"children\\":[[\\"$\\",\\"$L5\\",\\"x\\",{\\"href\\":\\"/\\",\\"className\\":\\"btn\\",\\"children\\":\\"_\\"}]]}]'
        ']]'
    )
    return (
        '[\\"$\\",\\"section\\",\\"'
        + uuid
        + '\\",{\\"className\\":\\"cta-section cta-section--dark\\",\\"children\\":[\\"$\\",\\"div\\",null,{\\"className\\":\\"container\\",\\"children\\":'
        + inner
        + '}]}]}]'
    )


def morph_footer_payload_fragment(frag: str) -> str:
    """Mutate a [$section,… Flight fragment (single footer section)."""
    import re

    frag = re.sub(
        r'\\"className\\":\\"cta-section cta-section--(?:dark|paper)\\"',
        '\\"className\\":\\"cta-section cta-section--dark three-ways-blocks\\"',
        frag,
        count=1,
    )
    marker = '\\"className\\":\\"container\\",\\"children\\":'
    mi = frag.find(marker)
    if mi < 0:
        raise ValueError("container children marker not found in Flight fragment")
    inner_all = frag[mi + len(marker) :]
    inner_all = inner_all.replace(
        '\\"className\\":\\"lede\\"',
        '\\"className\\":\\"lede three-ways-blocks__lede\\"',
        1,
    )
    tuple_needle = '[\\"$\\",\\"div\\",null,{\\"className\\":\\"cta__buttons\\"'
    ts = inner_all.find(tuple_needle)
    if ts < 0:
        raise ValueError("cta__buttons tuple not found")
    te = flight_array_end(inner_all, ts)
    new_inner = inner_all[:ts] + NEW_GRID_TUPLE + inner_all[te + 1 :]
    return frag[: mi + len(marker)] + new_inner


def rel_prefix(path: Path) -> str:
    rel = path.relative_to(REPO)
    depth = len(rel.parts) - 1
    return "../" * depth


def patch_payload(html: str, *, paper_ok: bool) -> tuple[str, bool]:
    classes = ['\\"className\\":\\"cta-section cta-section--dark\\"']
    if paper_ok:
        classes.append('\\"className\\":\\"cta-section cta-section--paper\\"')
    for cls_esc in classes:
        p = html.rfind(cls_esc)
        if p < 0:
            continue
        sec_needle = '[\\"$\\",\\"section\\",\\"'
        sec_start = html.rfind(sec_needle, 0, p)
        if sec_start < 0:
            continue
        sec_end = flight_array_end(html, sec_start)
        old_frag = html[sec_start : sec_end + 1]
        try:
            new_frag = morph_footer_payload_fragment(old_frag)
        except ValueError:
            continue
        return html[:sec_start] + new_frag + html[sec_end + 1 :], True
    return html, False


SPECIAL_BOOK_VISIBLE_MARK = '</div></section></main><footer class="footer">'

SPECIAL_PODCAST_VISIBLE_MARK = (
    "</div></div></a></div></div></section></main><footer class=\"footer\">"
)
SPECIAL_PODCAST_PAYLOAD_OLD = (
    "COMING SOON: Peak Property Performance® With Bill Douglas \\u0026 Drew Hall\\\"}]]}]]}]]}]}]}]]\\n\"]</script><style>"
)


JOBS: list[tuple[str, str | None, bool]] = [
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
    # Validate NEW_GRID_TUPLE once
    flight_array_end(NEW_GRID_TUPLE, 0)

    changed: list[str] = []

    for rel, prefix_override, paper_ok in JOBS:
        path = REPO / rel
        if not path.exists():
            print(f"SKIP missing {rel}")
            continue
        html = path.read_text(encoding="utf-8")
        prefix = prefix_override if prefix_override is not None else rel_prefix(path)
        html, v_ok = patch_visible(html, prefix, paper_ok=paper_ok)
        flight = "__next_f" in html
        p_ok = False
        if flight:
            html, p_ok = patch_payload(html, paper_ok=paper_ok)
            if not p_ok and v_ok:
                print(f"WARN {rel}: visible patched but Flight payload not matched")
        path.write_text(html, encoding="utf-8")
        changed.append(rel)
        print(f"OK {rel}  visible={'Y' if v_ok else '-'}  payload={'Y' if flight and p_ok else ('-' if not flight else 'N')}")

    vpath = REPO / "vendor-contract-audit/index.html"
    if vpath.exists():
        html = vpath.read_text(encoding="utf-8")
        html, v_ok = patch_visible(html, "../", paper_ok=False)
        if v_ok:
            vpath.write_text(html, encoding="utf-8")
            changed.append("vendor-contract-audit/index.html")
            print("OK vendor-contract-audit/index.html  visible=Y  payload=-")

    # --- Book: append visible + splice Flight before retailer section ---
    bpath = REPO / "book/index.html"
    if bpath.exists():
        html = bpath.read_text(encoding="utf-8")
        ins = visible_three_ways_section("../")
        book_sec_frag = (
            '[\\"$\\",\\"section\\",\\"69pppthree695214ebook\\",{\\"className\\":\\"cta-section cta-section--dark\\",'
            '\\"children\\":[\\"$\\",\\"div\\",null,{\\"className\\":\\"container\\",\\"children\\":'
            '[[\\"$\\",\\"span\\",null,{\\"className\\":\\"eyebrow\\",\\"children\\":\\"_\\"}]'
            ',[\\"$\\",\\"div\\",null,{\\"className\\":\\"cta__buttons\\",\\"children\\":[[\\"$\\",\\"$L5\\",\\"_\\",'
            '{\\"href\\":\\"/\\",\\"className\\":\\"btn\\",\\"children\\":\\"_\\"}]]}]}]}]}]'
        )
        book_sec_new = morph_footer_payload_fragment(book_sec_frag)
        if SPECIAL_BOOK_VISIBLE_MARK in html and ins not in html:
            html = html.replace(
                SPECIAL_BOOK_VISIBLE_MARK,
                "</div></section>" + ins + "</main><footer class=\"footer\">",
                1,
            )
        needle = (
            "Partner at NAI Shames Makovsky.\\\",null,null]}]]}]}]]]\\n\"]</script><script>self.__next_f.push([1,"
            '\\"12:[\\"$\\",\\"section\\",\\"69efb8125996bea084142e33\\"'
        )
        if needle in html and "69pppthree695214ebook" not in html:
            html = html.replace(
                needle,
                "Partner at NAI Shames Makovsky.\\\",null,null]}]]}]}],["
                + book_sec_new
                + ']]\\n"])</script><script>self.__next_f.push([1,"12:[\\"$\\",\\"section\\",\\"69efb8125996bea084142e33\\"',
                1,
            )
        bpath.write_text(html, encoding="utf-8")
        changed.append("book/index.html")
        print("OK book/index.html")

    # --- Podcast hub ---
    ppath = REPO / "podcast/index.html"
    if ppath.exists():
        html = ppath.read_text(encoding="utf-8")
        ins = visible_three_ways_section("../")
        pod_frag = (
            '[\\"$\\",\\"section\\",\\"69pppthree695214epod\\",{\\"className\\":\\"cta-section cta-section--dark\\",'
            '\\"children\\":[\\"$\\",\\"div\\",null,{\\"className\\":\\"container\\",\\"children\\":'
            '[[\\"$\\",\\"span\\",null,{\\"className\\":\\"eyebrow\\",\\"children\\":\\"_\\"}]'
            ',[\\"$\\",\\"div\\",null,{\\"className\\":\\"cta__buttons\\",\\"children\\":[[\\"$\\",\\"$L5\\",\\"_\\",'
            '{\\"href\\":\\"/\\",\\"className\\":\\"btn\\",\\"children\\":\\"_\\"}]]}]}]}]}]'
        )
        pod_sec_new = morph_footer_payload_fragment(pod_frag)
        if SPECIAL_PODCAST_VISIBLE_MARK in html and ins not in html:
            html = html.replace(
                SPECIAL_PODCAST_VISIBLE_MARK,
                "</div></div></a></div></div></section>" + ins + "</main><footer class=\"footer\">",
                1,
            )
        pneedle = SPECIAL_PODCAST_PAYLOAD_OLD
        if pneedle in html and "69pppthree695214epod" not in html:
            html = html.replace(
                pneedle,
                "COMING SOON: Peak Property Performance® With Bill Douglas \\u0026 Drew Hall\\\"}]]}]]}]]}]}]}],["
                + pod_sec_new
                + "]]\\n\"]</script><style>",
                1,
            )
        ppath.write_text(html, encoding="utf-8")
        changed.append("podcast/index.html")
        print("OK podcast/index.html")

    print(f"\nDone. {len(changed)} files touched.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
