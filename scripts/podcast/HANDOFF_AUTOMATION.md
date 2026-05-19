# Handoff: PPP Podcast Automation — Render Cron + Drive API

**To:** Danny
**From:** Bill (work product co-developed with Cursor agent)
**Date:** 2026-05-18
**Estimated time:** 20–25 minutes of your time + ~2 minutes from Bill

## TL;DR

The PPP podcast pages have been static — every new episode required
manual work to pull transcripts/show notes/thumbnails from a Google
Drive folder and re-render the HTML. We've automated the whole thing.
**I need you to wire up the credentials and Render Blueprint** because
those steps require org-level access I don't have. After your ~25
minutes of setup, the loop is closed: a new episode hitting the Anchor
RSS feed → live on `peakperformance.onrender.com` within 30 minutes,
no humans involved.

All the code is already merged on `main`. There's a complete step-by-
step runbook at `scripts/podcast/SETUP_AUTOMATION.md`. This file is the
cover letter that summarizes the work, defines the division of
responsibility, and gives you a verification checklist.

---

## What's already done (no action needed)

All Python, shell, and YAML code is committed to the repo:

| File | Purpose |
|---|---|
| `render.yaml` | Render Blueprint declaring the existing static site + a new `ppp-podcast-updater` cron service. |
| `scripts/podcast/cron_run.sh` | Render's cron entry point. Clones repo, runs the pipeline, commits + pushes anything that changed. |
| `scripts/podcast/drive_client.py` | Google Drive v3 API wrapper (service-account auth). |
| `scripts/podcast/refresh_assets.py` | Walks the master Drive folder, downloads transcripts/show notes, auto-discovers thumbnails, writes the asset manifests. |
| `scripts/podcast/update_podcast.py` | Orchestrator: Drive refresh → RSS fetch → index rebuild → audit → page render → listing-card rewrite. |
| `scripts/podcast/build_episode_pages.py` | Page renderer. Now reads assets from either a laptop Drive sync mirror **or** the cron-populated cache, whichever is available. |
| `scripts/podcast/requirements.txt` | Pip deps the Render build step installs. |
| `scripts/podcast/SETUP_AUTOMATION.md` | Step-by-step runbook — this is what you'll follow. |

Things I verified locally before handing this off:

- `python3 scripts/podcast/update_podcast.py --report-only --no-refresh --no-drive` runs cleanly, reports 35 ready episodes, 1 gated (Ep 36 has assets in Drive but isn't in RSS yet — this is the correct behavior).
- All four Python files compile.
- The static site is currently serving the latest hand-built output at <https://peakperformance.onrender.com/podcast/index.html>.

---

## What I need you to do

Open the runbook (`scripts/podcast/SETUP_AUTOMATION.md`) and walk
through it top to bottom. It's exhaustive. The four sections, summarized:

### Section 1 — Google Cloud service account (10 min, you alone)

You'll create a GCP project named `ppp-podcast-pipeline`, enable the
Google Drive API, create a service account named `ppp-podcast-cron`,
and download its JSON key. **Keep the JSON file safe — you'll paste
it into Render.** You'll also copy the service account's email
address (looks like `ppp-podcast-cron@ppp-podcast-pipeline.iam.gserviceaccount.com`).

**Handoff to Bill:** send Bill the service account email. He has to
share the Drive folder with it (he owns it, you can't). One-line
Slack message: *"Share this email as Viewer on the master Drive
folder, no email notify: `ppp-podcast-cron@…iam.gserviceaccount.com`"*.
Bill: it takes 30 seconds — right-click the master folder
<https://drive.google.com/drive/folders/1mhA8fDK9uPIn-1IzM-eG_yd5VOfnpWHO>
→ Share → paste the email → Viewer → uncheck Notify → Share.

### Section 2 — GitHub fine-grained PAT (3 min, you alone)

Generate a fine-grained PAT scoped only to `nbrain-team/peakperformance`
with **Contents: read and write**. Copy the value — GitHub only shows
it once. You'll paste it into Render in section 3.

You need org-admin or repo-admin rights on `nbrain-team/peakperformance`
to do this. If you're not the right person, redirect to whoever owns
the nbrain-team org.

### Section 3 — Render Blueprint (5 min, you alone)

Render Dashboard → New + → Blueprint → connect the GitHub repo. Render
reads `render.yaml` and previews two services: the existing
`peakperformance` static site and a new `ppp-podcast-updater` cron.
Click Apply.

Then in the cron service's Environment tab, paste:
- `GITHUB_TOKEN` ← the PAT from section 2
- `GOOGLE_DRIVE_SA_JSON` ← the *entire* JSON blob from section 1
  (multi-line; Render handles the newlines)

Hit Save.

### Section 4 — Verify (5 min, you alone)

Click "Trigger Run" on the cron service. Tail the logs. Expected output
is in the runbook. The first run will print discovery for ~36 episode
folders, find 0 changes (everything's already up to date), and exit
with "No changes — nothing to commit." That's success.

---

## Division of responsibility

| Step | Owner | Why |
|---|---|---|
| GCP project + service account + JSON key | **Danny** | Standard infra setup. |
| Share master Drive folder with service account | **Bill** | Bill owns the folder. |
| GitHub PAT generation | **Danny** | Requires repo-admin on `nbrain-team/peakperformance`. |
| Render Blueprint creation | **Danny** | Requires Render org-admin. |
| Pasting secrets into Render | **Danny** | Danny has the secrets in hand. |
| Triggering first run + watching logs | **Danny** | You're already there. |
| Reporting back "it's live" | **Danny** | Bill is unblocked. |

The collaborative step is Bill sharing the Drive folder with the
service account email. Everything else is yours.

---

## Verification checklist (when you're done)

Paste this into the response to Bill so we both know it's working:

- [ ] GCP project `ppp-podcast-pipeline` created.
- [ ] Drive API enabled on the project.
- [ ] Service account `ppp-podcast-cron` created; email shared with Bill.
- [ ] Bill confirmed master Drive folder is shared (Viewer) with the SA email.
- [ ] GCP service account JSON key downloaded and stored securely.
- [ ] GitHub fine-grained PAT generated, scoped to `nbrain-team/peakperformance`, Contents: read+write.
- [ ] Render Blueprint applied — both services visible in dashboard.
- [ ] `GITHUB_TOKEN` and `GOOGLE_DRIVE_SA_JSON` set on the cron service.
- [ ] First manual cron run completed successfully (paste the run URL).
- [ ] Cron schedule is `*/30 * * * *` (every 30 min). Adjust if needed in `render.yaml` + redeploy.

---

## Cost expectation

Render charges per-minute for cron services on the Starter plan. Each
run takes ~1–2 minutes (mostly `pip install` on cold starts). At every
30 minutes that's ~60–120 minutes/day of compute, which works out to
roughly $1–3/month. Confirmed pricing at <https://render.com/pricing>.

If you want lower frequency (Bill said 30 min is fine, but if cost is
a concern), edit the `schedule` line in `render.yaml` — `0 */2 * * *`
runs every 2 hours, `0 8,12,16,20 * * *` runs 4× per day at fixed
hours, etc. Cron expressions: <https://crontab.guru/>.

---

## What success looks like

After your setup, here's the steady-state behavior:

1. Bill records and produces an episode. He drops the transcript
   `.docx`, show notes `.pdf`, and a thumbnail PNG/JPG into that
   episode's Drive subfolder. He publishes to Anchor.
2. Anchor's RSS feed updates within minutes.
3. The next Render cron run (≤ 30 min later) detects the new RSS
   entry, pulls the assets from Drive via the service account, renders
   the episode page, updates the listing + sitemap, and pushes the
   commit to `main`.
4. Render's static-site auto-deploy picks up the push and the new page
   is live on `peakperformance.onrender.com`.

Bill's laptop is never in the loop. No agent runs are required. The
only ongoing human action is "drop assets into Drive + publish to
Anchor", which Bill was doing anyway.

---

## If something breaks

The pipeline is designed to fail loudly and visibly:

- **Cron run fails entirely:** Render emails Danny + shows the run in
  red on the dashboard. Click into the logs — Python tracebacks are
  unbuffered so you'll see exactly where.
- **Drive API auth fails:** Will show `RuntimeError: No Drive
  service-account credentials found` or a Google `403`. Most likely
  the service account email wasn't actually shared on the folder. Have
  Bill double-check the share.
- **Git push fails:** Token expired or scope wrong. Regenerate the
  PAT.
- **Page renders but looks broken:** The build is idempotent — running
  `python3 scripts/podcast/update_podcast.py --force` locally on
  Bill's laptop will regenerate from scratch. Bill has been doing
  this for weeks; it's reliable.

The whole system is designed so that you can **disable the cron at any
time** (just toggle it off in Render's dashboard) without affecting the
live site. The static site keeps serving whatever was last pushed.
Manual updates from Bill's laptop also keep working.

---

## Contacts

- **Bill** — Drive folder owner, content owner. Reach via the usual
  Slack channel.
- **Repo:** `nbrain-team/peakperformance` on GitHub.
- **Master Drive folder:**
  <https://drive.google.com/drive/folders/1mhA8fDK9uPIn-1IzM-eG_yd5VOfnpWHO>
- **Live site:** <https://peakperformance.onrender.com>
- **Anchor RSS:** <https://anchor.fm/s/1057cecf4/podcast/rss>
- **Runbook:** `scripts/podcast/SETUP_AUTOMATION.md` (in this repo)

If you hit a step in the runbook that doesn't match what you see in
the GCP / GitHub / Render UI (those products evolve), ping Bill and
he'll loop the Cursor agent back in to update the docs.
