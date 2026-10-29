#!/usr/bin/env bash
# Shared log location for the installer and maintainer source builds.
jdsp_setup_logs() {
  JDSP_LOG_DIR="${HOME}/jamesdsp-native-arch-logs"
  mkdir -p -- "${JDSP_LOG_DIR}"
  local old_logs=${XDG_STATE_HOME:-"${HOME}/.local/state"}/jamesdsp-native-arch/logs
  local old_file
  [[ -d ${old_logs} && ${old_logs} != "${JDSP_LOG_DIR}" ]] || return 0
  for old_file in "${old_logs}"/*.log; do
    [[ -f ${old_file} && ! -e ${JDSP_LOG_DIR}/${old_file##*/} ]] || continue
    if ! cp -n -- "${old_file}" "${JDSP_LOG_DIR}/"; then
      printf 'Could not copy old log: %s\n' "${old_file}" >&2
    fi
  done
}
