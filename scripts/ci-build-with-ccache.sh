#!/usr/bin/env bash
# CI-only helper: keep the existing makepkg source build and check() tests.
set -euo pipefail

compiler=$(command -v g++)
printf 'C++ compiler wrapper: %s\n' "$compiler"
if [[ $compiler != /usr/lib/ccache/bin/g++ ]]; then
  printf 'ERROR: ccache compiler wrapper is not active.\n' >&2
  exit 1
fi

ccache --zero-stats
makepkg -p PKGBUILD.source --syncdeps --noconfirm --cleanbuild
printf '\nccache results for %s:\n' "${JDSP_NATIVE_PROFILE:-unknown}"
ccache --show-stats
# A green build without any compiler calls passing through ccache is a regression.
ccache --print-stats | awk '
  $1 == "cache_miss" || $1 == "direct_cache_hit" || $1 == "preprocessed_cache_hit" { calls += $2 }
  END { if (calls < 1) { print "ERROR: ccache did not handle any compiler calls." > "/dev/stderr"; exit 1 } }
'
