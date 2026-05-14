# Source this file before running the podcast pipeline:
#   source scripts/podcast_pipeline/env.sh
#
# It activates the local virtualenv and points gcloud at the Python 3.12
# interpreter that uv installed (gcloud bundles its own Python on most
# distributions, but the macOS tarball ships unbundled).

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")/../.." && pwd)"

if [ -d "$REPO_ROOT/.venv" ]; then
  # shellcheck source=/dev/null
  . "$REPO_ROOT/.venv/bin/activate"
fi

# Local secrets (gitignored): OPENAI_API_KEY etc.
if [ -f "$REPO_ROOT/.env.local" ]; then
  # shellcheck source=/dev/null
  . "$REPO_ROOT/.env.local"
fi

# uv-installed Python 3.12 for gcloud
if [ -x "$HOME/.local/bin/uv" ]; then
  export PATH="$HOME/.local/bin:$PATH"
  CLOUDSDK_PYTHON_CANDIDATE="$($HOME/.local/bin/uv python find 3.12 2>/dev/null)"
  if [ -n "$CLOUDSDK_PYTHON_CANDIDATE" ]; then
    export CLOUDSDK_PYTHON="$CLOUDSDK_PYTHON_CANDIDATE"
  fi
fi

# gcloud binary on PATH for this shell only
if [ -d "$HOME/google-cloud-sdk/bin" ]; then
  export PATH="$HOME/google-cloud-sdk/bin:$PATH"
fi

# Google libraries auto-discover Application Default Credentials at this path
# after `gcloud auth application-default login` runs.
ADC_PATH="$HOME/.config/gcloud/application_default_credentials.json"
if [ -f "$ADC_PATH" ] && [ -z "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
  export GOOGLE_APPLICATION_CREDENTIALS="$ADC_PATH"
fi
