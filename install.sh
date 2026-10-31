#!/usr/bin/env bash
set -euo pipefail
repo_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
update=true
dry_run=false
countdown=true
for argument in "$@"; do
  case ${argument} in
    --no-update) update=false ;;
    --dry-run) dry_run=true ;;
    --no-countdown) countdown=false ;;
    *) printf 'Usage: %s [--no-update] [--dry-run] [--no-countdown]\n' "${0##*/}" >&2; exit 2 ;;
  esac
done
# shellcheck source=PKGBUILD
source "${repo_root}/PKGBUILD"
# shellcheck source=scripts/dependencies.sh
source "${repo_root}/scripts/dependencies.sh"
detect_kernel() {
  export JDSP_NATIVE_PROFILE
  JDSP_NATIVE_PROFILE=$(python3 "${repo_root}/scripts/kernel_info.py" --profile)
  python3 "${repo_root}/scripts/kernel_info.py"
  printf 'Selected optional patch profile: %s\n' "${JDSP_NATIVE_PROFILE}"
}
if ${dry_run}; then
  jdsp_ensure_dependencies dry-run "${depends[@]}" "${makedepends[@]}"
  if command -v python3 >/dev/null; then detect_kernel
  else printf '%s\n' 'Dry run: kernel detection would run after pacman installs Python.'; fi
  printf '%s\n' 'Dry run: would download the binary base, verify/select the prebuilt patched engine, repackage it, and install with pacman. No compilation or files changed.'
  exit 0
fi
if (( EUID == 0 )); then
  printf '%s\n' 'Run as your normal user; makepkg and pacman handle dependency/package installation.' >&2
  exit 1
fi
if [[ ! -r /etc/arch-release ]] || ! command -v pacman >/dev/null; then
  printf '%s\n' 'Arch Linux or an Arch-based distribution with pacman is required.' >&2
  exit 1
fi
# Keep pacman's real terminal so its percentage bars and prompts stay visible.
exec 3>&1 4>&2
export JDSP_PROGRESS_TTY=0
[[ ! -t 1 ]] || JDSP_PROGRESS_TTY=1
# shellcheck source=scripts/logs.sh
source "${repo_root}/scripts/logs.sh"
jdsp_setup_logs
log_file="${JDSP_LOG_DIR}/install-$(date +%Y%m%d-%H%M%S).log"
exec > >(tee -a "${log_file}") 2>&1
printf 'Log: %s\n' "${log_file}"
cd -- "${repo_root}"
backup=$(mktemp)
cp PKGBUILD "${backup}"
installed=false
cleanup() {
  local status=$?
  if ! ${installed}; then cp -- "${backup}" "${repo_root}/PKGBUILD"; fi
  rm -f -- "${backup}"
  if (( status != 0 )); then printf 'Installation stopped. See %s\n' "${log_file}" >&2; fi
}
trap cleanup EXIT
jdsp_ensure_dependencies install "${depends[@]}" "${makedepends[@]}"
detect_kernel
candidate=
if ${update}; then
  ./update.sh
  release_file="${repo_root}/jamesdsp-native-arch-${JDSP_NATIVE_PROFILE}-release.pkg.tar.zst"
  release_status=0
  python3 scripts/fetch_release.py --profile "${JDSP_NATIVE_PROFILE}" --destination "${release_file}" || release_status=$?
  case "$release_status" in
    0) candidate=$release_file; printf 'Verified GitHub Release selected: %s\n' "$candidate" ;;
    3) printf '%s\n' 'No newer published release; using the bundled, verified engine.' ;;
    *) printf '%s\n' 'Release verification failed; refusing silent downgrade.' >&2; exit 1 ;;
  esac
else
  printf '%s\n' 'Release checks disabled (--no-update); selecting bundled 0.2.2 engine.'
fi
if [[ -z "$candidate" ]]; then
  python3 scripts/run_logged.py --label 'Checking installer' --log "${JDSP_LOG_DIR}/checks-$(date +%Y%m%d-%H%M%S).log" -- ./test.sh
python3 scripts/download.py "${_base_url}" "${repo_root}/${_base_filename}" "${_base_sha256}"
if ${countdown}; then
  printf '%s\n' 'Preparing the prebuilt native package in 5 seconds. Ctrl+C cancels.'
  for ((i=5; i>0; i--)); do printf '%s ' "${i}"; sleep 1; done
  printf '\n'
fi
python3 scripts/run_logged.py --label 'Preparing binary package' --log "${JDSP_LOG_DIR}/package-$(date +%Y%m%d-%H%M%S).log" -- \
  makepkg --cleanbuild --clean --force
# shellcheck source=scripts/package.sh
source "${repo_root}/scripts/package.sh"
candidate=$(jdsp_find_package)
fi
# Check the package's internal metadata, not the downloaded filename.
[[ $(pacman -Qpq -- "$candidate") == jamesdsp-native-arch ]] || {
  printf 'Unexpected package name in %s; refusing installation.\n' "$candidate" >&2
  exit 1
}
# Never let a bundled fallback silently replace a newer, source-built install.
# Explicit rollbacks remain available through rollback.sh.
candidate_version=$(pacman -Qp -- "$candidate" | awk '{print $2}')
installed_version=$(pacman -Q jamesdsp-native-arch 2>/dev/null | awk '{print $2}' || true)
if [[ -n $installed_version ]] && (( $(vercmp "$candidate_version" "$installed_version") < 0 )); then
  printf 'Refusing to downgrade JamesDSP from %s to %s. Use rollback.sh for an intentional rollback.\n' \
    "$installed_version" "$candidate_version" >&2
  exit 1
fi
printf '%s\n' 'Exit any running JamesDSP instance before launching the newly installed version.'
printf '%s\n' 'Installing the native package; pacman will show percentage bars.'
jdsp_run_pacman -U "${candidate}" >&3 2>&4
installed=true
version=$(pacman -Q jamesdsp-native-arch | cut -d ' ' -f 2)
printf 'Installed jamesdsp-native-arch %s. Open Settings > Devices to enable your preferred outputs.\n' "${version}"
read -r -p 'After testing playback and device switching, mark this package as known good? [y/N] ' reply || reply=n
if [[ ${reply} == [Yy] || ${reply} == [Yy][Ee][Ss] ]]; then
  ./mark-known-good.sh "${candidate}" "${version}"
fi
