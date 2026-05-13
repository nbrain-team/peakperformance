# -*- coding: utf-8 -*-
"""Remove Next.js Flight payloads and webpack/React chunks from exported HTML.

Static exports keep server-rendered markup in <body>, but loading these scripts
hydrates next/link and calls preventDefault — client routing then navigates to
bare paths like /book which do not exist on disk (404 / blank screens).

Dropdown navigation uses CSS :hover/:focus-within; audit/vendor pages use plain
inline JS — those continue to work without hydration.

Preserves:
  - <script type="application/ld+json"> … </script>
  - Inline scripts that do not reference self.__next_f
  - External analytics snippets not loaded exclusively via Flight (may drop GA)

Run from repo root: python3 scripts/strip-next-hydration.py

After stripping (one-time per export batch):

  python3 scripts/build/build-ppp-review-form.py

That restores the full `/ppp-review` HTML form + submit handler; without it the page
only had an OpticWise embed placeholder that depended on React layout scripts.

Google Analytics loaded via Next `<Script>` may disappear until you add a plain
`<script>` tag for gtag yourself.
"""

from __future__ import annotations

import re
from pathlib import Path

_CHUNK_SCRIPT_RE = re.compile(
    r"<script\b[^>]*\bsrc=\"[^\"]*_next/static/chunks/[^\"]*\"[^>]*>\s*</script>",
    re.IGNORECASE,
)

_NEXT_INLINE_RE = re.compile(
    r"<script\b(?![^>]*\btype=[\"\']application/ld\+json[\"\'])[^>]*>"
    r"\s*(?:\(self\.__next_f|self\.__next_f).*?</script>",
    re.DOTALL | re.IGNORECASE,
)


def strip_html(html: str) -> tuple[str, int]:
    orig_len = len(html)
    html, n_chunk = _CHUNK_SCRIPT_RE.subn("", html)
    html, n_inline = _NEXT_INLINE_RE.subn("", html)
    removed = orig_len - len(html)
    return html, removed


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    touched = []
    for path in sorted(root.rglob("*.html")):
        site_rel = path.relative_to(root)
        src = path.read_text(encoding="utf-8")
        new, removed = strip_html(src)
        if removed <= 0:
            continue
        path.write_text(new, encoding="utf-8")
        touched.append((site_rel.as_posix(), removed))

    print(f"Stripped hydration from {len(touched)} HTML file(s)")
    for rel, nbytes in touched:
        print(f"  {rel}  (~{nbytes // 1024} KiB removed)")


if __name__ == "__main__":
    main()
