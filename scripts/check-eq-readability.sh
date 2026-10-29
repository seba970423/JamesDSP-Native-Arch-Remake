#!/usr/bin/env bash
# Fast EQ readability test: build only the Qt test target, not the audio engine.
set -euo pipefail
repo_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
source_tree=${1:?Usage: check-eq-readability.sh /path/to/patched/upstream}
export JDSP_TEST_SOURCE_TREE
JDSP_TEST_SOURCE_TREE=$(cd -- "$source_tree" && pwd)
build_dir=$(mktemp -d)
trap 'rm -rf -- "$build_dir"' EXIT
cd "$build_dir"
qmake6 "$repo_root/tests/interface_readability.pro"
make -j2
if ! ./interface-readability; then
  printf '%s\n' 'EQ readability failed. Reproducing under gdb for a backtrace...' >&2
  gdb -q -batch -ex run -ex 'thread apply all bt 20' --args ./interface-readability >&2 || true
  exit 1
fi
