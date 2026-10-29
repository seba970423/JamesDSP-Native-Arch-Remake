#!/usr/bin/env bash
set -euo pipefail
repo_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
# shellcheck source=scripts/progress.sh
source "${repo_root}/scripts/progress.sh"
ref=${1:-master}
[[ ${ref} =~ ^[A-Za-z0-9._/-]+$ && ${ref} != -* ]] || { printf '%s\n' 'Invalid upstream ref.' >&2; exit 2; }
candidate_dir=$(mktemp -d)
cleanup() {
  rm -rf -- "${candidate_dir}"
  jdsp_cleanup_git_progress
}
trap cleanup EXIT
jdsp_setup_git_progress "${repo_root}"
git -C "${candidate_dir}" init -q
git -C "${candidate_dir}" fetch --progress --depth=1 https://github.com/Audio4Linux/JDSP4Linux.git "${ref}"
commit=$(git -C "${candidate_dir}" rev-parse FETCH_HEAD)
current=$(sed -n 's/^_commit=//p' "${repo_root}/packaging/PKGBUILD.source")
if [[ ${commit} == "${current}" ]]; then printf 'Upstream is already pinned to %s.\n' "${commit}"; exit 0; fi
git -C "${candidate_dir}" checkout -q --detach "${commit}"
git -C "${candidate_dir}" apply --check "${repo_root}/patches/0001-device-effects-policy.patch"
git -C "${candidate_dir}" apply "${repo_root}/patches/0001-device-effects-policy.patch"
git -C "${candidate_dir}" submodule update --init --depth=1 src/subprojects/GraphicEQWidget src/subprojects/FlatTabWidget
git -C "${candidate_dir}" apply --check "${repo_root}/patches/0003-responsive-interface.patch"
git -C "${candidate_dir}" apply "${repo_root}/patches/0003-responsive-interface.patch"
git -C "${candidate_dir}" apply --check "${repo_root}/patches/0002-optional-rt-scratch.patch"
python3 - "${repo_root}/packaging/PKGBUILD.source" "${candidate_dir}" "${commit}" <<'PY'
from pathlib import Path
import re
import subprocess
import sys
path, checkout, commit = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
if not re.fullmatch(r'[0-9a-f]{40}', commit):
    raise SystemExit('Invalid upstream commit')
text = path.read_text()
updates = {'_commit': commit}
for key, folder in {'_eq_commit': 'GraphicEQWidget', '_tabs_commit': 'FlatTabWidget',
                    '_liquid_commit': 'LiquidEqualizerWidget', '_eel_commit': 'EELEditor'}.items():
    line = subprocess.check_output(['git', '-C', checkout, 'ls-tree', commit, 'src/subprojects/' + folder], text=True)
    fields = line.split()
    if len(fields) < 3 or fields[0] != '160000' or not re.fullmatch(r'[0-9a-f]{40}', fields[2]):
        raise SystemExit('Unexpected upstream submodule: ' + folder)
    updates[key] = fields[2]
date = subprocess.check_output(['git', '-C', checkout, 'show', '-s', '--format=%cs', commit], text=True).strip().replace('-', '')
updates['pkgver'] = '0.2.2.r' + date + '.g' + commit[:7]
updates['pkgrel'] = '1'
for key, value in updates.items():
    text, count = re.subn(r'^' + re.escape(key) + r'=.*$', key + '=' + value, text, count=1, flags=re.M)
    if count != 1:
        raise SystemExit('Missing packaging field: ' + key)
staged = path.with_suffix('.new')
staged.write_text(text)
staged.replace(path)
PY
printf 'Source recipe pinned to %s. Run ./scripts/build-source.sh to compile and test it.\n' "${commit}"
