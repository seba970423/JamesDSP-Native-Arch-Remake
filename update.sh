#!/usr/bin/env bash
set -euo pipefail
repo_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
printf '%s\n' 'Checking for a newer prebuilt patched release...'
python3 "${repo_root}/scripts/check_updates.py"
