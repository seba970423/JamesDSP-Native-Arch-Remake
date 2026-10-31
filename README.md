# JamesDSP Native Arch

[![Native PipeWire package CI](https://github.com/seba970423/JamesDSP-Native-Arch-Remake/actions/workflows/build.yml/badge.svg)](https://github.com/seba970423/JamesDSP-Native-Arch-Remake/actions/workflows/build.yml)

Upstream JamesDSP, patched and packaged natively for Arch Linux and CachyOS.
**PipeWire only. Latest release: [v0.2.3](https://github.com/seba970423/JamesDSP-Native-Arch-Remake/releases/tag/v0.2.3), x86_64 (experimental).**

The normal installer selects the SHA-256-verified **standard or PREEMPT_RT
package from the latest published GitHub Release** based on your running kernel.
It does not compile JamesDSP or download the upstream source on your machine.
[Release v0.2.3](https://github.com/seba970423/JamesDSP-Native-Arch-Remake/releases/tag/v0.2.3)
was built and checked by GitHub Actions and includes the setup-wizard fix.

For offline-bundle compatibility when no newer release is available (or when
using `--no-update`), this repository still contains the **older 0.2.2**
standard and RT engines, verified by SHA-256. That fallback follows the AUR
[jamesdsp-pipewire-bin recipe](https://github.com/archlinux/aur/blob/jamesdsp-pipewire-bin/PKGBUILD):
it unpacks the official PipeWire package and replaces the stock executable
with this project's patched engine. The corresponding sources for those
**0.2.2 fallback engines** are in
`prebuilt/corresponding-source-v0.2.2.tar.xz`; the v0.2.3 source and patches
are available from the tagged Git repository.

Choose the tray icon under **Settings → Tray icon → Icon appearance**:
Automatic, Light (for dark panels), Dark (for light panels), or Color (app icon).
The choice takes effect immediately and is saved for the next launch. Automatic
uses the icon theme, with the application's colors as a fallback. A manual choice
is useful when the panel and application use different color schemes.

## Hardware and CI status (updated 2026-10-31)

The maintainer reports working installations on **three machines**, all running
the custom **PREEMPT_RT + BORE (RT-BORE)** kernel with a hardware-specific build
profile for each system. Arch Linux and Arch-based distributions remain the
supported installation targets:

| System | RT-BORE hardware profile | Real-hardware results |
| --- | --- | --- |
| Desktop PC (CachyOS/KDE Plasma) | Desktop-specific | Installed and working for music playback. Device-effects controls are available; previously intermittent audio glitches and hissing have not been observed in recent listening. |
| Dell Latitude 7490 | Dell-specific | Successfully cloned and installed. Playback and the interface are working in initial use; no audio glitches have been noticed so far. |
| Lenovo ThinkPad T590 | ThinkPad-specific | Installed and confirmed working during real-world use. |

These are **maintainer-reported observations**, not exhaustive compatibility
certification or a guarantee of glitch-free playback. Longer-duration testing,
different Bluetooth/wired routes, application switching and other hardware
configurations still matter.

The [v0.2.3 GitHub Actions run](https://github.com/seba970423/JamesDSP-Native-Arch-Remake/actions/runs/41224024136)
passed the following checks on `main`, then published both release packages:

- `layout-smoke`: Quickly checks the patched Devices/Tray layouts and EQ
  readability without compiling the complete DSP application.
- `package (standard)`: Builds and checks the standard source package.
- `package (rt)`: Builds and checks the optional PREEMPT_RT source package.

The smoke check runs before the two full source builds, avoiding expensive
compilation when a known UI regression is detected. **Passing CI does not prove
every runtime behavior is correct.** Current v0.2.3 release packages are built
from the tested source; they are distinct from the older Ubuntu-built 0.2.2
fallback engines bundled in the repository.

## Install

From this project's directory, run as your normal user:

```bash
git clone https://github.com/seba970423/JamesDSP-Native-Arch-Remake
cd JamesDSP-Native-Arch-Remake
./install.sh
```

The installer first checks dependencies using Bash and pacman. Missing
prerequisites, including `base-devel` and Python, are offered through pacman's
normal package list and confirmation prompt. You do not need to install them
manually beforehand. Kernel detection and Python-based checks run after this
step. If you decline the package transaction or it fails, installation stops.

The installer detects the running kernel and checks published GitHub Releases.
When a newer release exists, it selects the matching **standard or PREEMPT_RT**
Arch package, verifies its SHA-256 against that release's `SHA256SUMS`, and installs
with pacman **without compiling JamesDSP**. A failed verification stops the
installation instead of silently downgrading. When there is no newer release,
it falls back to the bundled, checksum-verified 0.2.2 engines: the official base
is downloaded, its engine is replaced with the bundled patched executable, and
`makepkg` packages the result without compiling C++. `--no-update` explicitly
selects this bundled fallback. Debug-symbol packages are excluded from GitHub
Release downloads.

Downloads show a progress bar, percentage, transferred bytes and speed. Engine
preparation and package assembly show percentages based on completed steps.
Pacman's own download and installation bars stay connected to your terminal.
Noisy preparation output goes to a log, with elapsed-time updates every 30
seconds and the last log lines displayed on failure. A preparation or engine
compatibility failure stops before replacing the installed package.

If an older source-build installer is already running, cancel it with Ctrl+C,
extract this complete bundle, and start the new `install.sh`. Replacing files
does not change a script that is already running.

Quit the old JamesDSP instance before launching the newly installed one. Native
and Flatpak instances use the same upstream D-Bus service name; run one instance.
The installer does not remove a Flatpak installation or change PipeWire settings.

Useful options:

```bash
./install.sh --dry-run
./install.sh --no-update
./install.sh --no-countdown
```

Logs are saved in **`~/jamesdsp-native-arch-logs/`**, directly visible in Home.
The installer and source-build script also copy existing logs from the former
XDG state location into this folder, retaining the originals and leaving any
existing destination files untouched.

## Choose which devices get effects

Open **Settings → Devices**. Each device/route has an independent **Effects**
checkbox. New devices start with effects disabled; an optional checkbox changes
that default. All decisions are user settings; no device or brand is hardcoded.
The page scrolls vertically when its contents exceed the available height, so
the table, status and application controls remain separate at small window
sizes and with larger text. Long device/route names have tooltips.

Examples:

| Device / output | Possible setting |
| --- | --- |
| Bluetooth headphones | Effects enabled |
| JBL GO 4 | Effects disabled |
| Laptop headphone jack | Effects enabled |
| Laptop speakers | Effects disabled |

Use KDE Plasma or your desktop's normal audio controls to switch destinations.
The DSP engine follows the desktop's default output and checks its saved rule.
When an excluded device becomes default, applications return to their original
native routing. Applications explicitly assigned to another device retain that
destination; JamesDSP does not force them onto its own selected output.

Rules use device names and output-route names, not temporary PipeWire numeric
IDs. They survive reconnects and restarts. **All other routes** is a device-wide
fallback; a specific speaker/headphone/A2DP route overrides that fallback.
Disconnected devices with saved rules remain listed. Rules are stored in
`~/.config/jamesdsp/device_rules.json` separately from effects presets. Writes
are atomic; a malformed rules file disables processing and is not overwritten.

Version 0.2 retains upstream's **single stereo DSP engine** and shared effects
configuration. It processes the default output only. An app explicitly routed
to another output plays directly, even if that device's effects rule is enabled;
that rule takes effect when the device becomes the default. Simultaneous DSP
processing of several independent outputs and independent concurrent presets
are outside this version. Multichannel and unsupported output links are left
on their native path.

The Graphic EQ ruler displays only frequency labels that fit at the current
width and font size. All EQ bands remain present and editable through their gain
controls; fixed band frequencies remain readable and cannot be edited. Enabled
tabs use normal text colors, with the underline indicating the selected tab.

## Automatic PREEMPT_RT detection

Every installation includes device rules and diagnostics. The installer selects
the prebuilt engine containing the optional scratch-buffer patch only when it
confirms PREEMPT_RT in the **running kernel**:

1. Read `/sys/kernel/realtime` when available.
2. Otherwise inspect `/proc/config.gz`, `/boot/config-$(uname -r)`, or the running
   kernel's `/usr/lib/modules/$(uname -r)/config`.
3. If support is absent or cannot be verified, install the standard profile.

Full/dynamic preemption and a kernel name containing "rt" do not by themselves
prove PREEMPT_RT. An ordinary kernel remains fully supported. The optional patch
does not set process-wide SCHED_FIFO, modify rtkit, change scheduler services,
or modify kernel/PipeWire configuration. Upstream already requests PipeWire's
real-time data thread; the OS may or may not grant real-time scheduling.

The optional patch avoids unused probe scratch allocation on JamesDSP's audio
callback and prewarms probe capacity outside it. This is a limited optimization:
upstream sample-rate setup, DSP effect changes, and larger probe blocks can still
allocate or lock. This release does not promise fully real-time-safe processing,
lower latency, or measured performance gains.

The Devices page reports the running kernel, the installed package profile, and
observed real-time threads. Detailed per-thread scheduling is available through:

```bash
jamesdsp-native-diagnostics
jamesdsp-native-diagnostics --json
```

FF/FIFO and RR describe real-time scheduling; ordinary scheduling of the GUI is
expected. A PREEMPT_RT kernel alone does not establish the audio worker's policy.

Patches are already included in the distributed engines. Booting a different
kernel does not change the installed engine. The app still detects the new
running kernel; rerun `./install.sh` to select the matching verified release
profile. `--no-update` intentionally selects the older bundled 0.2.2 engines
and is not the normal update path. Both profiles can run on an ordinary kernel.

## Updates, rollback and removal

```bash
./update.sh                    # check GitHub Releases
./install.sh                   # install the latest verified package for your kernel
./install.sh --no-update       # use bundled 0.2.2 fallback (downgrades blocked)
./rollback.sh --known-good     # reinstall the latest user-approved package
./rollback.sh                  # reinstall the preceding approved generation
./uninstall.sh
```

After installation the script asks whether playback/device switching worked.
Only a package you approve becomes `known-good`; the prior approved generation
is retained as `previous`. Rollback verifies the stored package checksum before
asking pacman to install it. Uninstall removes package-owned files and keeps
your presets and device rules.

The installer checks GitHub Releases and downloads the current standard or RT
package with SHA-256 verification. If no newer release exists, it can use the
bundled 0.2.2 fallback, but refuses to downgrade an already-installed newer
package. A broken checksum stops installation. The installer never substitutes
an unpatched upstream executable or starts a source compilation as a fallback.

## Publishing tested packages

The `Native PipeWire package` workflow first runs the fast UI smoke gate, then
builds and checks both Arch source profiles in separate jobs. Artifacts contain
the application packages, **not** the optional 186 MiB debug-symbol package.

**Publishing is automatic after successful CI on `main`.** After the fast
layout smoke gate and **both** the standard and PREEMPT_RT package jobs succeed,
the same workflow invokes the release publisher. Pull requests run the checks
but never publish packages. The publisher verifies both package versions, their
recorded build profiles, the pinned upstream commit and SHA-256 checksums before
creating the GitHub Release. Debug packages are excluded.

The GitHub Release tag comes from `pkgver` in `packaging/PKGBUILD.source`
(currently `0.2.3`). A tag is **never overwritten**. If the version has
already been published, the publisher skips it; to release new changes, bump
`pkgver` and keep `pkgrel=1`. A superseded `main` build also skips publishing.
No separate manual workflow dispatch is necessary. The normal installer
also refuses an accidental downgrade to bundled 0.2.2 when a newer version is
already installed; intentional recovery remains available via `./rollback.sh`.

The fast smoke job now runs `actionlint` on the workflow definitions to catch
malformed GitHub Actions syntax before starting either expensive build.

**v0.2.3 is published.** The setup-wizard signal fix is included in its
verified standard and RT packages; `./install.sh` selects them automatically.
The bundled 0.2.2 fallback remains available separately.

## Development and testing

```bash
./test.sh
./test.sh /path/to/patched/JDSP4Linux
```

The first command runs kernel detection, packaging, progress and shell checks.
The second also compiles and runs the device-policy and routing regression tests. Routing
tests execute the production controller against a deterministic PipeWire
boundary: default changes, user-selected destinations, app exclusions, exit
restoration, and reused node IDs. They supplement real PipeWire/hardware tests.

The bundled 0.2.2 fallback package's `check()` verifies the selected engine,
probes its loader with `--help`, and runs the portable checks. Those fallback
engines were built on Ubuntu 24.04 with GCC 13.3.0, Qt 6.4.2 and PipeWire
1.0.5; they use native shared libraries and require glibc 2.38 or later. Initial Arch-based hardware
playback has been reported working on the desktop, Dell Latitude 7490 and
ThinkPad T590, all with their respective RT-BORE hardware profiles. Broader
compatibility, configuration-specific behavior, and long-term stability remain
unverified. See
[VALIDATION.md](VALIDATION.md) for build-environment test details.

Maintainers can explicitly build the source recipe instead:

```bash
./scripts/update-source.sh      # validate/update the source recipe's pin
./scripts/build-source.sh       # compile and check the source recipe
```

The source path is separate from the normal installer. It forces Git transfer
progress and records compilation output in a log with 30-second elapsed-time
updates. Arch CI uses `packaging/PKGBUILD.source` and now runs the fast Qt/EQ
smoke gate followed by complete standard and RT source package checks. The
successful [v0.2.3 release run](https://github.com/seba970423/JamesDSP-Native-Arch-Remake/actions/runs/41224024136)
then published those packages, which the normal installer now downloads and
verifies. Subsequent versions require a version bump before publishing.

See [docs/testing.md](docs/testing.md) for the hardware checklist and Brave's audio
replay investigation. The maintainer reports no recurrence of earlier audio
glitches in recent use, but the specific Brave replay issue has not been
systematically confirmed fixed across setups.

## Credits and license

Upstream: [Audio4Linux/JDSP4Linux](https://github.com/Audio4Linux/JDSP4Linux),
Linux port by Tim Schneeberger; DSP engine by James Fung. PipeWire integration
includes code derived from EasyEffects by Wellington Wallace. Original notices
are retained. Distributed under GPL-3.0-or-later; see [LICENSE](LICENSE).
The upstream binary packaging approach is credited to the AUR
`jamesdsp-pipewire-bin` recipe. See [SOURCE-INFO.txt](SOURCE-INFO.txt) for the
matching engine source archive and checksum.
