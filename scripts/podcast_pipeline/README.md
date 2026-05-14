# Peak Property Performance — Podcast Pipeline

Automates the audit's two outstanding tasks for every episode folder in the
producer's Drive:

1. **Generate a transcript** from the canonical `Audioversion.mp3`
   (Whisper) and put it back in the episode folder.
2. **Draft show notes** in the standard PPP template (see
   `docs/podcast-show-notes-template.md`) and put them back as a Google Doc
   for Roxanna to refine.

The audit CSV at `docs/podcast-drive-gap-audit.csv` is the single source of
truth for "which episodes still need this." Re-running the pipeline after
Roxanna marks a row complete will skip it on the next pass.

> **Note on Read.ai:** Read.ai transcribes live meetings (Zoom/Meet/Teams),
> not arbitrary MP3 files. The PPP catalog is Riverside-recorded audio in
> Drive, so we use Whisper directly on the MP3s. Nothing is pulled from the
> Read.ai mirror for this catalog.

---

## Setup

### 1. Python dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r scripts/podcast_pipeline/requirements.txt
```

### 2. ffmpeg (for episodes > ~24 MB MP3)

Whisper's API caps uploads at 25 MB; longer episodes are auto-chunked with
ffmpeg. Most episodes in this catalog need it.

```bash
brew install ffmpeg
```

### 3. OpenAI API key (Whisper + show notes drafting)

```bash
export OPENAI_API_KEY="sk-..."
```

### 4. Google Drive credentials

Two valid options — pick one.

**A. Service account (recommended for cron / production)**

The OpticWise Drive integration in this workspace currently has **read-only**
scope on the producer's Drive folder. To let the script upload transcript
files and create show-notes Google Docs, ask the OpticWise admin to:

1. Add `https://www.googleapis.com/auth/drive` (or `drive.file`) to the
   service account's scope set.
2. Share the root **Peak Property Performance** Drive folder
   (`1mhA8fDK9uPIn-1IzM-eG_yd5VOfnpWHO`) with the service account's email
   address as **Editor**.
3. Hand back the service-account JSON key file.

Then point the env var at it:

```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/sa-key.json"
```

**B. Personal OAuth (for one-off manual runs)**

If you'd rather run this from your own laptop under your own Drive identity,
generate a `token.json` via the standard Google OAuth flow with the
`drive` scope and point at it:

```bash
export GOOGLE_OAUTH_USER_TOKEN_JSON="/path/to/token.json"
```

(Either env var also satisfies read-only download for the fetch step.)

---

## Run

### End-to-end (everything still flagged in the audit)

```bash
python -m scripts.podcast_pipeline.run_all
```

### A single episode (testing / re-runs)

```bash
python -m scripts.podcast_pipeline.run_all 12
```

### Step by step

```bash
python -m scripts.podcast_pipeline.fetch_audio        # Drive read-only is fine
python -m scripts.podcast_pipeline.transcribe         # needs OPENAI_API_KEY
python -m scripts.podcast_pipeline.draft_shownotes    # needs OPENAI_API_KEY
python -m scripts.podcast_pipeline.upload_to_drive    # needs Drive write
```

### Run without uploading (preview locally first)

```bash
python -m scripts.podcast_pipeline.run_all --no-upload
```

---

## Outputs

| Path | Purpose |
|---|---|
| `scripts/podcast_pipeline/work/audio/PPP-Episode-NN.mp3` | Downloaded canonical audio (gitignored) |
| `scripts/podcast_pipeline/work/transcripts/PPP-Episode-NN-Transcript.txt` | Producer-facing transcript (gitignored) |
| `scripts/podcast_pipeline/work/show_notes/PPP Episode NN — Show notes.md` | Markdown source for the Drive Doc (gitignored) |
| `transcripts/ppp-ep-NNN.txt` | Site-facing transcript — picked up automatically by `scripts/regenerate-podcast.py` |
| `docs/episode-drafts/PPP-Episode-NN-Show-notes.md` | Repo-tracked draft so we have a Git history of what was generated |

After upload, in Drive each episode folder gains:

- `PPP-Episode-NN-Transcript.txt`
- `PPP Episode NN — Show notes` (Google Doc)

If those names already exist, the script **updates the existing file in place**
(preserves the Drive ID and link) — Roxanna can edit the Doc directly and her
changes survive the next regeneration.

---

## Cost estimate

Whisper API: **$0.006 / minute**.
Catalog of ~35 episodes × ~30 min average ≈ **$6.30 one-time** to transcribe
everything. Drafting show notes with `gpt-4o-mini` adds roughly the same
order of magnitude.

---

## Future: weekly cron

Once write scope is in place, drop this in a weekly cron / GitHub Actions
schedule (Thursdays 2 PM Mountain) and let it pick up new episodes
automatically as Roxanna marks new rows in the audit CSV. The audit CSV is
the throttle — only rows still flagged `NEEDS_TRANSCRIPT` or
`NEEDS_SHOW_NOTES` are processed.
