#!/usr/bin/env bash
# Lightweight layout regression check for a prepared, patched upstream source tree.
set -euo pipefail
repo_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
source_tree=${1:?Usage: check-ui-layout.sh /path/to/patched/upstream}
source_tree=$(cd -- "${source_tree}" && pwd)
build_dir=$(mktemp -d)
trap 'rm -rf -- "${build_dir}"' EXIT
qt_libexec=$(pkg-config --variable=libexecdir Qt6Core)
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
