#!/usr/bin/env bash
set -euo pipefail
repo_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
source_tree=${1:-}
python3 -m unittest discover -s "${repo_root}/tests" -p 'test_*.py' -v
for script in "${repo_root}"/*.sh "${repo_root}"/scripts/*.sh; do
  bash -n "${script}"
done
bash -n "${repo_root}/PKGBUILD"
bash -n "${repo_root}/packaging/PKGBUILD.source"
if command -v shellcheck >/dev/null; then
  shellcheck -x -P "${repo_root}" "${repo_root}"/*.sh "${repo_root}"/scripts/*.sh
fi
if [[ -z ${source_tree} ]]; then
  printf '%s\n' 'Portable checks passed. Supply a patched upstream tree to run the C++ policy and routing tests.'
  exit 0
fi
source_tree=$(cd -- "${source_tree}" && pwd)
export JDSP_TEST_SOURCE_TREE="${source_tree}"
build_dir=$(mktemp -d)
trap 'rm -rf -- "${build_dir}"' EXIT
read -r -a qt_flags <<< "$(pkg-config --cflags --libs Qt6Core)"
g++ -std=c++20 -fPIC -I"${source_tree}/src/audio/pipewire" \
  "${repo_root}/tests/device_policy.cpp" "${source_tree}/src/audio/pipewire/DevicePolicy.cpp" \
  "${qt_flags[@]}" -o "${build_dir}/device-policy"
"${build_dir}/device-policy"
qt_libexec=$(pkg-config --variable=libexecdir Qt6Core)
if [[ -n ${PKG_CONFIG_SYSROOT_DIR:-} && -x ${PKG_CONFIG_SYSROOT_DIR}${qt_libexec}/moc ]]; then
  qt_libexec=${PKG_CONFIG_SYSROOT_DIR}${qt_libexec}
fi
"${qt_libexec}/moc" -DHEADLESS "${source_tree}/src/config/AppConfig.h" -o "${build_dir}/moc_AppConfig.cpp"
read -r -a routing_flags <<< "$(pkg-config --cflags --libs Qt6Core Qt6DBus glibmm-2.4 giomm-2.4 libpipewire-0.3)"
g++ -std=c++20 -fPIC -DHEADLESS -I"${source_tree}/src" -I"${source_tree}/src/audio/pipewire" \
  -I"${source_tree}/src/audio/base" "${repo_root}/tests/routing.cpp" \
  "${source_tree}/src/audio/pipewire/FilterContainer.cpp" "${source_tree}/src/audio/pipewire/DevicePolicy.cpp" \
  "${source_tree}/src/config/AppConfig.cpp" "${source_tree}/src/config/ConfigContainer.cpp" \
  "${source_tree}/src/config/ConfigIO.cpp" "${build_dir}/moc_AppConfig.cpp" \
  "${routing_flags[@]}" -o "${build_dir}/routing"
"${build_dir}/routing"
read -r -a widget_flags <<< "$(pkg-config --cflags --libs Qt6Widgets Qt6DBus)"
python3 - "${source_tree}/src/interface/fragment/SettingsFragment.ui" "${build_dir}/settings-form.ui" <<'PY'
import sys
import xml.etree.ElementTree as ET
tree = ET.parse(sys.argv[1])
# The unrelated tray-menu editor is replaced; all real Settings layouts remain.
for widget in tree.findall('.//widget'):
    if widget.get('class') == 'QMenuEditor':
        widget.set('class', 'QWidget')
custom = tree.find('customwidgets')
if custom is not None:
    tree.getroot().remove(custom)
tree.write(sys.argv[2])
PY
"${qt_libexec}/uic" "${build_dir}/settings-form.ui" -o "${build_dir}/ui_SettingsForm.h"
g++ -std=c++20 -fPIC -I"${source_tree}/src/audio/pipewire" -I"${source_tree}/src/audio/base" \
  -I"${source_tree}/src/interface/fragment" -I"${build_dir}" "${repo_root}/tests/device_widget.cpp" \
  "${source_tree}/src/interface/fragment/NativeDeviceWidget.cpp" "${source_tree}/src/audio/pipewire/DevicePolicy.cpp" \
  "${widget_flags[@]}" -o "${build_dir}/device-widget"
"${build_dir}/device-widget"
mkdir "${build_dir}/readability"
(
  cd "${build_dir}/readability"
  qmake6 "${repo_root}/tests/interface_readability.pro"
  make -j2
  ./interface-readability
)
mkdir "${build_dir}/tray"
(
  cd "${build_dir}/tray"
  qmake6 "${repo_root}/tests/tray_appearance.pro"
  make -j2
  ./tray-appearance
)
printf '%s\n' 'Kernel detection, device policy, stream routing, settings layout, EQ readability and tray appearance tests passed.'
