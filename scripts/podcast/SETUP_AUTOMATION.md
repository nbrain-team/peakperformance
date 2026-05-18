# Hands-Off Podcast Pipeline — Setup Guide

This is a one-time setup that flips the podcast pipeline from
"laptop + agent driven" to "Render cron + Drive API, no human in the
loop." After this, every new episode that appears in the Anchor RSS
feed gets published to the site within 30 minutes — assets are pulled
straight from Drive, no laptop required.

You'll do four things, in order. Estimated time: 20–25 minutes.

1. Create a Google Cloud service account that can read the master
   podcast Drive folder.
2. Create a fine-grained GitHub Personal Access Token so the cron job
   can push commits.
3. Create the Render Blueprint (cron service + static site).
4. Verify the first cron run.

---

## 1. Google Drive service account (10 min)

A service account is a "robot user" identity. We grant it Viewer
access to the master podcast Drive folder; the cron job authenticates
as the robot and reads files.

1. Open <https://console.cloud.google.com/>. Log in with whichever
   Google account owns the podcast Drive folder (or any Google
   account — the service account itself does the reading).
2. Top-left, click the project picker → **New Project**.
   - Name: `ppp-podcast-pipeline`
   - Click **Create**, then select the project from the picker.
3. In the search bar at the top, type **Google Drive API** and click
   the result. Click **Enable**.
4. Search **Service Accounts** → click the result → **+ Create
   service account**.
   - Service account name: `ppp-podcast-cron`
   - Service account ID: (auto-filled) `ppp-podcast-cron`
   - Description: `Reads the PPP podcast Drive folder for the cron`
   - Click **Create and Continue**.
   - **Grant this service account access to project**: skip (click
     **Continue**).
   - **Grant users access to this service account**: skip (click
     **Done**).
5. You're now back on the Service Accounts list. Click the row for
   `ppp-podcast-cron@...iam.gserviceaccount.com`. Copy that **email
   address** — you'll paste it into Drive in step 7.
6. On the service account detail page, go to the **Keys** tab → **Add
   Key** → **Create new key** → **JSON** → **Create**. A JSON file
   downloads. Open it in a text editor; you'll paste the entire
   contents into Render in step 12.
7. Open the master Drive folder:
   <https://drive.google.com/drive/folders/1mhA8fDK9uPIn-1IzM-eG_yd5VOfnpWHO>
   - Right-click the folder name at the top → **Share**.
   - Paste the service account email from step 5.
   - Role: **Viewer**.
   - **Uncheck "Notify people"** (it'll bounce — service accounts
     don't have inboxes).
   - Click **Share**.

   The cron can now read every file in this folder via the Drive API.

---

## 2. GitHub Personal Access Token (3 min)

The cron commits regenerated HTML back to `main`, which is what
triggers Render's static-site auto-deploy.

1. Open <https://github.com/settings/personal-access-tokens/new>
   (fine-grained tokens).
2. **Token name**: `ppp-podcast-cron`
3. **Expiration**: 1 year (calendar reminder to rotate).
4. **Resource owner**: select the org/user that owns
   `nbrain-team/peakperformance`.
5. **Repository access** → **Only select repositories** →
   `nbrain-team/peakperformance`.
6. **Repository permissions** → expand → **Contents** → **Read and
   write**. (Leave everything else as the default "No access".)
7. **Generate token**. Copy the value (starts with `github_pat_…`) —
   you can't see it again.

---

## 3. Create the Render Blueprint (5 min)

The blueprint definition lives in `render.yaml` at the repo root. We
just need to point Render at the repo and paste the two secrets.

1. Open <https://dashboard.render.com/>.
2. **New +** → **Blueprint**.
3. Connect the GitHub repo `nbrain-team/peakperformance` (you may
   need to grant Render access to the repo first).
4. Render reads `render.yaml` and previews two services:
   - `peakperformance` (static site)
   - `ppp-podcast-updater` (cron)

   Click **Apply**.
5. Render creates both services. The static site should match what's
   already live at `peakperformance.onrender.com` (no behavior
   change there). The cron service is new.
6. Open the **ppp-podcast-updater** service → **Environment** tab.
   You'll see five non-secret env vars already populated from
   `render.yaml`, plus two empty secret slots:
   - **`GITHUB_TOKEN`** — paste the PAT from step 2.7.
   - **`GOOGLE_DRIVE_SA_JSON`** — paste the *entire* contents of
     the JSON file from step 1.6. (Yes, the whole multi-line JSON
     blob — Render handles the newlines fine.)
   - Click **Save Changes**. The cron service rebuilds with the new
     env vars.

---

## 4. Verify (5 min)

1. On the `ppp-podcast-updater` service page, click **Trigger Run**
   (top right).
2. Watch the **Logs** stream. You should see:
   ```
   === PPP Podcast Cron — 2026-05-18T... ===
   --- Running update_podcast.py ---
   [0/5] Refreshing Drive assets (transcripts, show notes, thumbnails)…
     → Discovering episode folders in master Drive folder…
       Found 36 episode folders (eps 0…36)
     → Ep 1: Episode 1 — Lane Taylor  (1S44jnYGtIY…)
         transcript: PPP Ep 1 - Transcript - Lane Taylor.docx
         show notes: PPP Ep 1 - Show Notes - Lane Taylor.pdf
         thumbnails: PPP Ep 1 - YouTube Thumbnail.jpg
     …
   [1/5] Fetching https://anchor.fm/s/…/podcast/rss → …
   [2/5] Rebuilding scripts/podcast/_episode_index.json
   [3/5] Audit: 35 ready, 0 missing assets, 0 new slugs, 1 gated
   [4/5] Nothing to build.   ← (everything already up to date)
   [5/5] Listing-page card thumbnails already up to date

   ✓ No changes — nothing to commit.
   ```
3. From this point the cron runs every 30 minutes. When a new
   episode hits the Anchor RSS feed and its assets are in Drive, the
   next run will:
   - Detect the new RSS entry.
   - Pull the transcript / show notes / thumbnails from Drive.
   - Render the page, update the listing, update the sitemap.
   - Commit + push to main.
   - Render's static-site auto-deploy picks up the commit.

   End-to-end: episode is live on `peakperformance.onrender.com`
   within ~30 minutes of the RSS feed publishing it. No laptop, no
   human in the loop.

---

## Drive folder hygiene for future episodes

The auto-discovery rules in `refresh_assets.py` look for specific
filename patterns inside each per-episode subfolder. To keep new
episodes flowing through cleanly:

- **Transcript**: any file whose name contains `Transcript` and is
  either a `.docx` or a native Google Doc.
- **Show notes**: any file whose name contains `Show Notes` (or
  `Shownotes`) and is either a PDF or a native Google Doc.
- **Thumbnail (1:1 + 16:9, modern naming, preferred)**: put both
  `1 by 1.png` AND `16 by 9.png` in the folder.
- **Thumbnail (fallback)**: the `PPP Ep N - YouTube Thumbnail.jpg`
  (the same 16:9 still you upload to YouTube). Browser CSS center-
  crops it to 1:1 on the listing.

If both are present, the modern pair wins. The discovery is
deterministic, so naming things consistently means zero manual work
per episode.

---

## What about the laptop?

Nothing changes locally. You can still run
`python3 scripts/podcast/update_podcast.py` on your Mac when you want
to test something or push a manual update — it will use whichever of
the laptop's Drive sync mirror OR the cron-populated `_drive_cache/`
is available. If the service account JSON also lives at
`~/.config/ppp/drive-sa.json`, local runs will also fetch from Drive
directly without depending on Drive Desktop sync.
