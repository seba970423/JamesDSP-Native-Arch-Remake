#!/usr/bin/env bash
# Maintainer-only source build. The normal installer never invokes this script.
set -euo pipefail
repo_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
# shellcheck source=scripts/progress.sh
source "${repo_root}/scripts/progress.sh"
jdsp_setup_git_progress "${repo_root}"
trap jdsp_cleanup_git_progress EXIT
# shellcheck source=scripts/logs.sh
source "${repo_root}/scripts/logs.sh"
jdsp_setup_logs
cd -- "${repo_root}"
printf '%s\n' 'Maintainer source build: installing build dependencies first.'
makepkg -p PKGBUILD.source --syncdeps --nobuild
python3 scripts/run_logged.py --label 'Compiling patched JamesDSP' \
  --log "${JDSP_LOG_DIR}/source-build-$(date +%Y%m%d-%H%M%S).log" -- \
  makepkg -p PKGBUILD.source --noextract --force
