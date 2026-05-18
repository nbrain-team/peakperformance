#!/usr/bin/env bash
# Entry point for the Render cron job.
#
# Render runs this on a schedule (see render.yaml). The job:
#   1. Clones the GitHub repo using a fine-grained PAT.
#   2. Runs the podcast update pipeline (refresh_assets + RSS + build).
#   3. If anything changed, commits and pushes back to main. That push
#      triggers Render's static-site auto-deploy.
#
# Environment variables required (set in the Render dashboard):
#   GITHUB_REPO         e.g. nbrain-team/peakperformance
#   GITHUB_TOKEN        Fine-grained PAT with contents:write on the repo
#   GIT_USER_NAME       Display name for commits (e.g. "PPP Podcast Bot")
#   GIT_USER_EMAIL      Email for commits (e.g. ppp-bot@peakproperty…)
#   GOOGLE_DRIVE_SA_JSON   Full service-account JSON (single env var)

set -euo pipefail

: "${GITHUB_REPO:?GITHUB_REPO must be set, e.g. nbrain-team/peakperformance}"
: "${GITHUB_TOKEN:?GITHUB_TOKEN must be set (fine-grained PAT with contents:write)}"
: "${GIT_USER_NAME:=PPP Podcast Bot}"
: "${GIT_USER_EMAIL:=ppp-bot@peakpropertyperformance.com}"
: "${GOOGLE_DRIVE_SA_JSON:?GOOGLE_DRIVE_SA_JSON must be set (service-account JSON)}"

WORKDIR="${WORKDIR:-/tmp/ppp-podcast-cron}"
BRANCH="${GIT_BRANCH:-main}"
REPO_URL="https://x-access-token:${GITHUB_TOKEN}@github.com/${GITHUB_REPO}.git"

echo "=== PPP Podcast Cron — $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="

# 1. Fresh clone (faster + safer than incremental for a small repo) ---------
rm -rf "$WORKDIR"
mkdir -p "$WORKDIR"
git clone --depth 1 --branch "$BRANCH" "$REPO_URL" "$WORKDIR"
cd "$WORKDIR"

git config user.name  "$GIT_USER_NAME"
git config user.email "$GIT_USER_EMAIL"

# 2. Run the pipeline -------------------------------------------------------
echo
echo "--- Running update_podcast.py ---"
python3 scripts/podcast/update_podcast.py

# 3. Commit & push if anything changed --------------------------------------
echo
if [[ -z "$(git status --porcelain)" ]]; then
  echo "✓ No changes — nothing to commit."
  exit 0
fi

echo "--- Changes detected ---"
git status --short
git add -A
COMMIT_MSG="auto: podcast cron $(date -u +%Y-%m-%dT%H:%M:%SZ)"
git commit -m "$COMMIT_MSG"
git push origin "$BRANCH"

echo
echo "✓ Pushed: $COMMIT_MSG"
echo "  Render static site will auto-deploy."
