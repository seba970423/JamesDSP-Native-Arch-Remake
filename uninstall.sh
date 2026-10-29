#!/usr/bin/env bash
set -euo pipefail
printf '%s\n' 'Quit JamesDSP using its tray menu first. Your effects presets and device rules will be kept.'
sudo pacman -R jamesdsp-native-arch
