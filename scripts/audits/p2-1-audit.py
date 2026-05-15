# -*- coding: utf-8 -*-
"""P2-1 — Read-only site-wide audit for trademark + language consistency.

Scans every HTML file under the repo (skipping vendored/build folders) and
reports:

  1. "Peak Property Performance" without ® — every occurrence with file:line context
  2. "5C Framework" without ™ — every occurrence with file:line context
  3. "PPP" stand-alone references that may need to be "Peak Property Performance®" on first mention
  4. Standalone "infrastructure" — every occurrence (judgment call which to expand)
  5. Other registered marks — sanity-check BoT®, ElasticISP®, 5S®, SIC®, Property Brain™, Portfolio Brain™

Read-only. No file writes.
"""

from __future__ import annotations
import os
import re
from collections import defaultdict
from pathlib import Path

SKIP_DIRS = {".git", "_next", ".venv", "node_modules", "public", "_external", "scripts", "docs", "transcripts", "api"}


def collect_html_files(root: Path) -> list[Path]:
    paths: list[Path] = []
    for r, dirs, names in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
        for n in names:
            if n.endswith(".html"):
                paths.append(Path(r) / n)
    return sorted(paths)


def linecol_of(text: str, idx: int) -> tuple[int, int]:
    line = text.count("\n", 0, idx) + 1
    last_nl = text.rfind("\n", 0, idx)
    col = idx - (last_nl + 1) + 1
    return line, col


def context(text: str, idx: int, end: int, width: int = 80) -> str:
    start = max(0, idx - width)
    finish = min(len(text), end + width)
    snippet = text[start:finish].replace("\n", " ").replace("  ", " ")
    return snippet[:240]


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    os.chdir(repo_root)

    files = collect_html_files(Path("."))
    print(f"Scanning {len(files)} HTML files...\n")

    # =============================================================================
    # 1. "Peak Property Performance" without ® immediately following
    #    Pattern: "Peak Property Performance" not followed by ®
    # =============================================================================
    ppp_violations: dict[str, list[tuple[int, str]]] = defaultdict(list)
    ppp_re = re.compile(r"Peak Property Performance(?!®|&reg;|&#174;)")
    for fp in files:
        s = fp.read_text(encoding="utf-8")
        for m in ppp_re.finditer(s):
            line, _ = linecol_of(s, m.start())
            ppp_violations[str(fp)].append((line, context(s, m.start(), m.end())))

    print("=" * 100)
    print(f"1. 'Peak Property Performance' WITHOUT ® → {sum(len(v) for v in ppp_violations.values())} occurrences in {len(ppp_violations)} files")
    print("=" * 100)
    for fp, hits in sorted(ppp_violations.items()):
        print(f"\n  📄 {fp}  ({len(hits)} hits)")
        for line, ctx in hits[:5]:
            print(f"     line {line:>4}: ...{ctx}...")
        if len(hits) > 5:
            print(f"     ...and {len(hits) - 5} more")

    # =============================================================================
    # 2. "5C Framework" without ™
    # =============================================================================
    fivec_violations: dict[str, list[tuple[int, str]]] = defaultdict(list)
    fivec_re = re.compile(r"5C(?!™|&trade;|&#8482;) Framework")
    for fp in files:
        s = fp.read_text(encoding="utf-8")
        for m in fivec_re.finditer(s):
            line, _ = linecol_of(s, m.start())
            fivec_violations[str(fp)].append((line, context(s, m.start(), m.end())))

    print("\n" + "=" * 100)
    print(f"2. '5C Framework' WITHOUT ™ → {sum(len(v) for v in fivec_violations.values())} occurrences in {len(fivec_violations)} files")
    print("=" * 100)
    for fp, hits in sorted(fivec_violations.items()):
        print(f"\n  📄 {fp}  ({len(hits)} hits)")
        for line, ctx in hits[:5]:
            print(f"     line {line:>4}: ...{ctx}...")
        if len(hits) > 5:
            print(f"     ...and {len(hits) - 5} more")

    # =============================================================================
    # 3. Standalone "infrastructure" (not preceded by "data and digital ", "data & digital ",
    #    or part of a compound word). Show context to allow judgment calls.
    # =============================================================================
    print("\n" + "=" * 100)
    print(f"3. Standalone 'infrastructure' (not 'data and digital infrastructure') → context for judgment")
    print("=" * 100)

    infra_re = re.compile(r"\binfrastructure\b", re.IGNORECASE)
    # Negative-lookbehind would be ideal but variable-width — do post-filter instead.
    GOOD_PREFIXES = (
        "data and digital ",
        "data & digital ",
        "data, digital, and ",
        "data, digital and ",
        "digital ",  # e.g. "digital infrastructure"
    )
    infra_findings: dict[str, list[tuple[int, str, bool]]] = defaultdict(list)
    for fp in files:
        s = fp.read_text(encoding="utf-8")
        for m in infra_re.finditer(s):
            # Look at last ~30 chars before the match to see if "data and digital" precedes it
            window_start = max(0, m.start() - 35)
            preceding = s[window_start:m.start()].lower()
            is_compound = any(preceding.endswith(p) for p in GOOD_PREFIXES)
            line, _ = linecol_of(s, m.start())
            infra_findings[str(fp)].append((line, context(s, m.start(), m.end(), 100), is_compound))

    total_infra = sum(len(v) for v in infra_findings.values())
    standalone_count = sum(1 for hits in infra_findings.values() for _, _, ok in hits if not ok)
    compound_count = total_infra - standalone_count
    print(f"\n  Total 'infrastructure' occurrences: {total_infra}")
    print(f"  Already 'data and digital infrastructure' (or 'digital infrastructure'): {compound_count}")
    print(f"  STANDALONE 'infrastructure' needing review: {standalone_count}")

    print("\n  Standalone occurrences with context:")
    for fp, hits in sorted(infra_findings.items()):
        standalone = [(line, ctx) for line, ctx, ok in hits if not ok]
        if not standalone:
            continue
        print(f"\n    📄 {fp}  ({len(standalone)} standalone)")
        for line, ctx in standalone[:8]:
            print(f"       line {line:>4}: ...{ctx}...")
        if len(standalone) > 8:
            print(f"       ...and {len(standalone) - 8} more")

    # =============================================================================
    # 4. Other registered marks — confirm BoT®, ElasticISP®, 5S®, SIC®, Property Brain™, Portfolio Brain™ all carry symbols
    # =============================================================================
    print("\n" + "=" * 100)
    print("4. Other registered marks — checking each appears WITH its symbol")
    print("=" * 100)

    OTHER_MARKS = [
        ("BoT", "®"),
        ("ElasticISP", "®"),
        ("5S", "®"),
        ("SIC", "®"),
        ("Property Brain", "™"),
        ("Portfolio Brain", "™"),
    ]
    for name, symbol in OTHER_MARKS:
        # Find all instances of "name" not followed by symbol or HTML entity
        pattern = re.compile(re.escape(name) + r"(?!" + re.escape(symbol) + r"|&reg;|&trade;)\b")
        bad: dict[str, list[int]] = defaultdict(list)
        good_count = 0
        for fp in files:
            s = fp.read_text(encoding="utf-8")
            for m in re.finditer(re.escape(name), s):
                # Tail check
                end = m.end()
                tail = s[end:end + 8]
                if tail.startswith(symbol) or tail.startswith("&reg;") or tail.startswith("&trade;"):
                    good_count += 1
                else:
                    # Filter out word-boundary false positives — e.g. "5SE" should NOT match "5S"
                    # Use \b at end
                    if end < len(s) and s[end].isalnum():
                        continue
                    line, _ = linecol_of(s, m.start())
                    bad[str(fp)].append(line)
        bad_total = sum(len(v) for v in bad.values())
        print(f"\n  {name}{symbol} — {good_count} correct, {bad_total} missing symbol")
        if bad:
            for fp, lines in sorted(bad.items()):
                print(f"      📄 {fp} → lines {lines[:10]}")

    # =============================================================================
    # 5. "Game-changing" filler — flagged earlier on /podcast H1, check site-wide
    # =============================================================================
    print("\n" + "=" * 100)
    print("5. 'Game-changing' / 'Game changing' filler — to consider tightening")
    print("=" * 100)

    gc_re = re.compile(r"[Gg]ame[- ]changing", re.IGNORECASE)
    gc_findings: dict[str, list[tuple[int, str]]] = defaultdict(list)
    for fp in files:
        s = fp.read_text(encoding="utf-8")
        for m in gc_re.finditer(s):
            line, _ = linecol_of(s, m.start())
            gc_findings[str(fp)].append((line, context(s, m.start(), m.end(), 100)))
    total_gc = sum(len(v) for v in gc_findings.values())
    print(f"\n  Total 'game-changing' occurrences: {total_gc}\n")
    for fp, hits in sorted(gc_findings.items()):
        print(f"  📄 {fp}  ({len(hits)} hits)")
        for line, ctx in hits[:3]:
            print(f"     line {line:>4}: ...{ctx}...")
        if len(hits) > 3:
            print(f"     ...and {len(hits) - 3} more")


if __name__ == "__main__":
    main()
