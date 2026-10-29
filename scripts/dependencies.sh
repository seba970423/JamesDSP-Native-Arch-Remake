#!/usr/bin/env bash
# Bootstrap with Bash and pacman before any Python or makepkg command is used.
jdsp_run_pacman() {
  if [[ -z ${JDSP_PRIVILEGE_TOOL:-} ]]; then
    if command -v sudo >/dev/null; then JDSP_PRIVILEGE_TOOL=sudo
    elif command -v su >/dev/null; then JDSP_PRIVILEGE_TOOL=su
    else
      printf '%s\n' 'Package installation needs sudo or su for authentication.' >&2
      return 1
    fi
  fi
  case ${JDSP_PRIVILEGE_TOOL} in
    sudo) sudo pacman "$@" ;;
    su)
      local pacman_command
      printf -v pacman_command '%q ' pacman "$@"
      su -c "${pacman_command}"
      ;;
    *) printf '%s\n' 'Invalid package authentication method.' >&2; return 1 ;;
  esac
}

jdsp_ensure_dependencies() {
  local mode=$1 dependency output status=0 executable
  shift
  local -a required=() missing=()
  local -A seen=()
  for dependency in base-devel "$@"; do
    if [[ -z ${seen[${dependency}]:-} ]]; then
      required+=("${dependency}")
      seen[${dependency}]=1
    fi
  done
  if ! command -v pacman >/dev/null; then
    if [[ ${mode} == dry-run ]]; then
      printf '%s\n' 'Dry run: on Arch, pacman would check and offer missing packaging/runtime dependencies, including base-devel and Python.'
      return 0
    fi
    printf '%s\n' 'pacman is required to install dependencies.' >&2
    return 1
  fi
  printf '%s\n' 'Checking packaging and runtime dependencies with pacman...'
  output=$(pacman -T "${required[@]}") || status=$?
  case ${status} in
    0) ;;
    127)
      [[ -n ${output} ]] || { printf '%s\n' 'pacman returned no missing dependency names.' >&2; return 1; }
      mapfile -t missing <<< "${output}"
      ;;
    *) printf 'Dependency check failed (pacman exit %s).\n' "${status}" >&2; return "${status}" ;;
  esac
  if ((${#missing[@]})); then
    printf 'Missing packages:\n'
    printf '  %s\n' "${missing[@]}"
    if [[ ${mode} == dry-run ]]; then
      printf '%s\n' 'Dry run: pacman would offer to install these packages. Nothing was installed.'
      return 0
    fi
    printf '%s\n' 'Pacman will show the package list, sizes and installation confirmation.'
    if ! jdsp_run_pacman -S --needed "${missing[@]}" >&3 2>&4; then
      printf '%s\n' 'Dependency installation did not complete. Installation stopped.' >&2
      return 1
    fi
    if ! pacman -T "${required[@]}"; then
      printf '%s\n' 'Required dependencies are still missing. Installation stopped.' >&2
      return 1
    fi
  else
    printf '%s\n' 'All required packages are already installed.'
  fi
  [[ ${mode} != dry-run ]] || return 0
  for executable in python3 makepkg; do
    command -v "${executable}" >/dev/null || {
      printf 'Required command is unavailable after dependency checks: %s\n' "${executable}" >&2
      return 1
    }
  done
}
