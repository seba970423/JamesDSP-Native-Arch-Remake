#!/usr/bin/env bash
# Scoped to this installer and its children; never replaces the system Git.
jdsp_setup_git_progress() {
  if [[ ${JDSP_GIT_PROGRESS_READY:-0} == 1 && -x ${JDSP_REAL_GIT:-} && -f ${JDSP_GIT_PROGRESS_HELPER:-} ]]; then
    return
  fi
  JDSP_REAL_GIT=$(type -P git) || return
  JDSP_GIT_PROGRESS_HELPER=$1/scripts/git_progress.py
  JDSP_PROGRESS_TTY=0
  [[ ! -t 2 ]] || JDSP_PROGRESS_TTY=1
  JDSP_CREATED_GIT_WRAPPER_DIR=$(mktemp -d "${TMPDIR:-/tmp}/jamesdsp-git-progress.XXXXXX") || return
  cat > "${JDSP_CREATED_GIT_WRAPPER_DIR}/git" <<'SHIM'
#!/usr/bin/env bash
exec python3 "${JDSP_GIT_PROGRESS_HELPER:?}" "$@"
SHIM
  chmod 755 "${JDSP_CREATED_GIT_WRAPPER_DIR}/git"
  export JDSP_REAL_GIT JDSP_GIT_PROGRESS_HELPER JDSP_PROGRESS_TTY
  export JDSP_GIT_PROGRESS_READY=1
  export PATH="${JDSP_CREATED_GIT_WRAPPER_DIR}:${PATH}"
}

jdsp_cleanup_git_progress() {
  if [[ -n ${JDSP_CREATED_GIT_WRAPPER_DIR:-} ]]; then
    rm -rf -- "${JDSP_CREATED_GIT_WRAPPER_DIR}"
  fi
}
