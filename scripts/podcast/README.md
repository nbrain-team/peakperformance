# Podcast page build pipeline

This folder contains the scripts that generate the per-episode pages at
`/podcast/<slug>/`. The pipeline is **RSS-triggered**: an episode only goes
live on the site when Anchor's RSS feed lists it. Even if assets are sitting
in Drive, the page stays gated until RSS publishes the episode (this is how
we avoid pre-announcing).

## Source-of-truth hierarchy

1. **Anchor RSS feed** — `_anchor_rss.xml` (cached locally; refreshed by
   `update_podcast.py`). This is the gate: an episode publishes when RSS
   says it published. It also provides title, description, mp3 url, pub
   date, duration, and episode number.

2. **Master Drive folder** —
   <https://drive.google.com/drive/folders/1mhA8fDK9uPIn-1IzM-eG_yd5VOfnpWHO>
   contains one subfolder per episode (named `Ep N`). Each subfolder holds:
   - `PPP Ep N - Transcript - <Guest>.docx`
   - `PPP Ep N - Show Notes - <Guest>.pdf`
   - `PPP Ep N - YouTube Thumbnail.jpg` (or a `1 by 1.png` override)
   - audio/video originals (ignored by this pipeline)

   The current set of `Ep N` subfolders is cached in
   `_drive_master_listing.json` and used to detect "in Drive but not in
   RSS" episodes (which stay gated).

3. **Local Drive mirror** —
   `~/My Drive/AA DOWNLOADS - WD rev 2025-Apr/PPP-Podcast-Deliverables/`
   is a flat copy of all transcripts and show notes plus three CSVs:
   - `master-episodes.csv` (ep → YouTube id, drive_folder_id, title)
   - `thumbnail-manifest.csv` (ep → thumbnail urls)
   - `batch-deliverables-summary.csv` (ep → guest, asset file ids)

   The build script reads the docx/pdf files from this flat mirror because
   per-ep Drive folders are not synced to local disk.

## Scripts

| File | Role |
|---|---|
| `fetch_rss.sh` | (one-liner) `curl -o _anchor_rss.xml https://anchor.fm/s/1057cecf4/podcast/rss` |
| `build_episode_index.py` | Joins RSS + manifest + existing pages → `_episode_index.json` |
| `extract.py` | Standalone DOCX/PDF text-extraction helper (not used by the main loop) |
| `build_episode_pages.py` | Renders one or all `podcast/<slug>/index.html` files |
| `save_drive_asset.py` | Decodes a base64 blob from the gdrive MCP and writes it to the local mirror |
| `update_podcast.py` | **Main entry.** Refresh RSS → rebuild index → audit gaps → build ready pages → publish OW Insights posts → report what still needs Drive fetches and what's gated |
| `publish_ow_insights.py` | Bridge script that calls the OpticWise `generate-ppp-blog-posts.ts` to create Insights blog posts for newly built episodes (requires OPENAI_API_KEY) |

## Routine update workflow

When a new episode lands in the RSS feed:

```bash
cd ~/My\ Drive/Cursor/ppp-html
python3 scripts/podcast/update_podcast.py
```

This will:

1. Pull the latest RSS into `_anchor_rss.xml`.
2. Rebuild `_episode_index.json` from RSS + manifest + existing pages.
3. Audit which episodes are ready, which need assets, which need new
   local page directories, and which are gated.
4. Build everything that's ready (page < 40KB or assets newer than page).
5. Print clear "FETCH FROM DRIVE" instructions for any episodes whose
   transcript or show notes aren't in the local mirror yet.

If assets are missing, the agent fetches them via the gdrive MCP and
saves them with `save_drive_asset.py`:

```bash
# Inside Cursor, an agent does:
#   1. Call gdrive MCP `search_files` / `list_folder` to find the asset file_id
#   2. Call gdrive MCP `read_file` to get the base64 blob
#   3. Pipe the base64 to save_drive_asset.py:

python3 scripts/podcast/save_drive_asset.py \
    --ep 36 --kind transcript --guest "Jane Doe" \
    --b64-file /tmp/ep36_transcript.b64

# Then re-run update_podcast.py to build the page.
```

> **Note on MCP base64 reliability.** During the 2026-05-18 build of Ep 25
> we discovered that round-tripping ~16KB base64 blobs through the
> `gdrive` MCP read_file → agent → save_drive_asset.py pipeline can
> introduce character substitutions that corrupt the docx (CRC mismatch
> on `word/document.xml`). The workaround used was to restore from a
> previously-built backup zip at
> `~/Library/Application Support/Claude/.../outputs/PPP-Podcast-Deliverables.zip`.
> Going forward, if a docx fails to open after a fresh MCP fetch, prefer
> sourcing it from that zip or from a manual download.

## Refreshing the Drive folder listing

The `_drive_master_listing.json` cache should be refreshed whenever a new
episode subfolder is created (so the gating logic notices). The agent runs:

```python
# Pseudocode:
result = mcp_call('user-opticwise-gdrive', 'list_folder', {
    'folder_id': '1mhA8fDK9uPIn-1IzM-eG_yd5VOfnpWHO', 'page_size': 100
})
# extract Ep N subfolders, write to _drive_master_listing.json
```

## Build modes

```bash
# Refresh RSS, rebuild everything that needs it, report gaps
python3 scripts/podcast/update_podcast.py

# Skip RSS fetch (faster; useful when iterating on the build script)
python3 scripts/podcast/update_podcast.py --no-refresh

# Force re-render every ready page even if it looks current
python3 scripts/podcast/update_podcast.py --force

# Dry-run / audit only — don't write any files
python3 scripts/podcast/update_podcast.py --report-only

# Build a single episode
python3 scripts/podcast/build_episode_pages.py --ep 1

# Build a custom list
python3 scripts/podcast/build_episode_pages.py --eps 1,17,33
```

## File outputs per episode

Each `podcast/<slug>/` directory contains:

```
index.html          # the rendered page (≈60-130 KB)
thumbnail.jpg       # 1:1 cropped YouTube thumbnail (≈100 KB)
thumbnail-16x9.jpg  # original YouTube maxres (≈130 KB)
```

The page includes:

- Hero with episode number, duration, pub date, listen-on row
- Click-to-play YouTube facade (no embed JS until clicked)
- HTML5 `<audio>` element with the Anchor mp3 URL
- Structured show notes: overview, pull quote, what-you'll-learn,
  key moments timeline, resources mentioned
- Full transcript inside a `<details>` expander (collapsed by default)
- Sidebar: Get the Book + Request a PPP Review + 4 recent episodes
- JSON-LD: Organization, BreadcrumbList, PodcastEpisode (with
  `transcript`, `video`, `author[]`, `partOfSeries`)
