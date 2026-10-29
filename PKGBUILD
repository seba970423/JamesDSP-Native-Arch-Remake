# Maintainer: Sebastian George
# Binary packaging based on the AUR jamesdsp-pipewire-bin recipe.
pkgname=jamesdsp-native-arch
pkgver=0.2.2
pkgrel=1
pkgdesc='Prebuilt patched JamesDSP with device effects rules (PipeWire only)'
arch=('x86_64')
url='https://github.com/seba970423/JamesDSP-Native-Arch-Remake'
license=('GPL-3.0-or-later')
provides=('jamesdsp')
conflicts=('jamesdsp' 'jamesdsp-git' 'jamesdsp-pipewire-bin' 'jdsp4linux' 'jdsp4linux-gui' 'gst-plugin-jamesdsp')
depends=('glibmm' 'hicolor-icon-theme' 'libarchive' 'libpipewire' 'libxcb' 'qt6-base' 'qt6-svg' 'python' 'pipewire')
makedepends=('binutils' 'fakeroot' 'zstd' 'desktop-file-utils')
optdepends=('pipewire-pulse: compatibility for applications using the PulseAudio API')
_engine_commit=3ea7d733c090409c00887db3bb3aaf3af79ea692
_base_filename=jamesdsp-pipewire_2.7.0-30a30a_ubuntu22-04_amd64.deb
_base_url="https://github.com/Audio4Linux/JDSP4Linux/releases/download/2.7.0/${_base_filename}"
_base_sha256=34ca987f55256ed27ae475e2f5eefcedbb8654a7f2a662a393ed863ef3537de8
source=("${_base_url}" 'native-engines-x86_64.tar.xz' 'kernel_info.py' 'diagnostics.py'
        'verify_prebuilt.py' 'LICENSE' 'SOURCE-INFO.txt')
sha256sums=(
  '34ca987f55256ed27ae475e2f5eefcedbb8654a7f2a662a393ed863ef3537de8'
  '9fa9b6c17fa42ef4af8c7fd3958412ce218bf54b452cc753301df8716e0aa01c'
  'd97ece470d1f1513d5e456b812aab70e2ed31e7cb3b7334802eda3ea48609112'
  '8241f0596f75daa9a0def50fe1a539d0c8213def547b5647aa77d926bdfc6cf6'
  '01cb2eb5817c65dc9ceda8c5732a73f275be598bed9f0efbd40b74b6bfb6f0bf'
  '3972dc9744f6499f0f9b2dbf76696f2ae7ad8af9b23dde66d6af86c9dfb36986'
  '6b80a735118665620accf0c1160aaaa6fb3dc9ca738f0a500bdcb36f582b9280'
)

native_step() {
  local label=$1 completed=$2 total=$3 percent filled bar empty
  if [[ ${JDSP_PROGRESS_PROTOCOL:-0} == 1 ]]; then
    printf '@@JDSP_STEP@@%s|%s|%s\n' "${label}" "${completed}" "${total}"
  else
    percent=$((completed * 100 / total))
    filled=$((percent / 5))
    printf -v bar '%*s' "${filled}" ''
    printf -v empty '%*s' "$((20-filled))" ''
    printf '%s: [%s%s] %3d%%\n' "${label}" "${bar// /#}" "${empty// /-}" "${percent}"
  fi
}

prepare() {
  cd "${srcdir}"
  native_step 'Preparing patched engine' 0 3
  local profile=${JDSP_NATIVE_PROFILE:-}
  [[ -n ${profile} ]] || profile=$(python kernel_info.py --profile)
  [[ ${profile} == rt || ${profile} == standard ]] || { printf 'Invalid profile: %s\n' "${profile}" >&2; return 1; }
  printf '%s\n' "${profile}" > .native-profile
  native_step 'Preparing patched engine' 1 3
  python verify_prebuilt.py engines "${profile}"
  native_step 'Preparing patched engine' 2 3
  [[ -f data.tar.xz ]] || { printf '%s\n' 'Upstream binary package payload is missing.' >&2; return 1; }
  native_step 'Preparing patched engine' 3 3
}

# No build() function: no compiler, qmake, source checkout or submodule download.
check() {
  cd "${srcdir}"
  local profile
  profile=$(<.native-profile)
  python verify_prebuilt.py engines "${profile}"
  mkdir -p .probe-config .probe-cache
  XDG_CONFIG_HOME="${srcdir}/.probe-config" XDG_CACHE_HOME="${srcdir}/.probe-cache" \
    "${srcdir}/engines/${profile}/jamesdsp" --help >/dev/null
  bash "${startdir}/test.sh"
}

package() {
  cd "${srcdir}"
  local profile rt=false
  profile=$(<.native-profile)
  [[ ${profile} != rt ]] || rt=true
  native_step 'Installing package files' 0 4
  tar --no-same-owner -xaf data.tar.xz -C "${pkgdir}"
  native_step 'Installing package files' 1 4
  install -Dm755 "engines/${profile}/jamesdsp" "${pkgdir}/usr/bin/jamesdsp"
  native_step 'Installing package files' 2 4
  install -Dm755 diagnostics.py "${pkgdir}/usr/bin/jamesdsp-native-diagnostics"
  install -Dm644 kernel_info.py "${pkgdir}/usr/lib/jamesdsp-native-arch/kernel_info.py"
  install -Dm644 engines/manifest.json "${pkgdir}/usr/share/${pkgname}/engine-manifest.json"
  printf '{"rt_patches":%s,"upstream_commit":"%s","distribution":"prebuilt"}\n' "${rt}" "${_engine_commit}" \
    > "${pkgdir}/usr/share/${pkgname}/build-profile.json"
  native_step 'Installing package files' 3 4
  install -Dm644 LICENSE "${pkgdir}/usr/share/licenses/${pkgname}/LICENSE"
  install -Dm644 SOURCE-INFO.txt "${pkgdir}/usr/share/doc/${pkgname}/SOURCE-INFO.txt"
  native_step 'Installing package files' 4 4
}
