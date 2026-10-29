#!/usr/bin/env bash
# Locate the main package through its metadata, including custom PKGDEST paths.
jdsp_find_package() {
  local package_list package name
  package_list=$(makepkg --packagelist) || {
    printf '%s\n' 'Could not list the prepared packages.' >&2
    return 1
  }
  while IFS= read -r package; do
    [[ -n ${package} ]] || continue
    if [[ ! -f ${package} ]]; then
      printf 'Prepared package is missing: %s\n' "${package}" >&2
      return 1
    fi
    name=$(pacman -Qpq -- "${package}") || {
      printf 'Could not inspect prepared package: %s\n' "${package}" >&2
      return 1
    }
    if [[ ${name} == jamesdsp-native-arch ]]; then
      printf '%s\n' "${package}"
      return 0
    fi
  done <<< "${package_list}"
  printf '%s\n' 'No prepared JamesDSP package found.' >&2
  return 1
}
