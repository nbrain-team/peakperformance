#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Inject cookie-consent assets into all HTML pages.

Adds:
  1. Consent CSS <link> in <head>
  2. Inline consent-default + GA4 gtag snippet in <head>
  3. Consent JS <script defer> before </body>
  4. "Cookie Settings" link in footer legal line
  5. Removes orphaned gtag preload from ppp-review/index.html
"""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def relative_prefix(html_path: Path) -> str:
    """Calculate the relative path prefix from an HTML file back to repo root."""
    rel = html_path.relative_to(REPO_ROOT)
    depth = len(rel.parts) - 1  # subtract the filename itself
    if depth == 0:
        return './'
    return '../' * depth


def consent_css_link(prefix: str) -> str:
    return f'<link rel="stylesheet" href="{prefix}public/css/cookie-consent.css"/>'


def gtag_inline_snippet() -> str:
    return (
        '<script>'
        'window.dataLayer=window.dataLayer||[];'
        'function gtag(){dataLayer.push(arguments);}'
        "gtag('consent','default',{"
        "analytics_storage:'denied',"
        "ad_storage:'denied',"
        "ad_user_data:'denied',"
        "ad_personalization:'denied',"
        "wait_for_update:500"
        '});'
        "gtag('js',new Date());"
        "gtag('config','G-DF9CQ5M85D');"
        '</script>'
        '<script async src="https://www.googletagmanager.com/gtag/js?id=G-DF9CQ5M85D"></script>'
    )


def consent_js_script(prefix: str) -> str:
    return f'<script defer src="{prefix}public/js/cookie-consent.js"></script>'


def cookie_settings_link(prefix: str) -> str:
    return (
        f' · <a href="{prefix}cookie-policy/index.html" '
        f'style="color:rgba(245,240,228,0.7)" data-cc-settings>Cookie Settings</a>'
    )


def inject_file(html_path: Path) -> str:
    """Inject consent assets into a single HTML file. Returns status message."""
    content = html_path.read_text(encoding='utf-8')
    prefix = relative_prefix(html_path)
    modified = False

    # Skip if already injected
    if 'cookie-consent.js' in content:
        return f'  SKIP {html_path.relative_to(REPO_ROOT)}: already injected'

    # 1. Remove orphaned gtag preload (ppp-review specifically)
    preload_pattern = r'<link rel="preload"[^>]*googletagmanager[^>]*/>'
    if re.search(preload_pattern, content):
        content = re.sub(preload_pattern, '', content)
        modified = True

    # 2. Insert consent CSS + gtag snippet before </head>
    head_insert = consent_css_link(prefix) + gtag_inline_snippet()
    if '</head>' in content:
        content = content.replace('</head>', head_insert + '</head>', 1)
        modified = True

    # 3. Insert consent JS before </body>
    body_insert = consent_js_script(prefix)
    if '</body>' in content:
        content = content.replace('</body>', body_insert + '</body>', 1)
        modified = True

    # 4. Add Cookie Settings link after Terms of Use in footer
    terms_pattern = r'(Terms of Use</a>)(</span>)'
    terms_replacement = r'\1' + cookie_settings_link(prefix) + r'\2'
    if re.search(terms_pattern, content):
        content = re.sub(terms_pattern, terms_replacement, content, count=1)
        modified = True

    if modified:
        html_path.write_text(content, encoding='utf-8')
        return f'  OK   {html_path.relative_to(REPO_ROOT)}'
    else:
        return f'  WARN {html_path.relative_to(REPO_ROOT)}: no injection points found'


def main():
    html_files = sorted(REPO_ROOT.rglob('*.html'))
    # Exclude any files in scripts/, _next/, or _external/ directories
    html_files = [
        f for f in html_files
        if not any(part.startswith(('scripts', '_next', '_external', 'node_modules'))
                   for part in f.relative_to(REPO_ROOT).parts)
    ]

    print(f'Injecting cookie consent into {len(html_files)} HTML files...\n')
    for html_path in html_files:
        result = inject_file(html_path)
        print(result)

    print(f'\nDone. Processed {len(html_files)} files.')


if __name__ == '__main__':
    main()
