# JamesDSP Native Arch

[![Native PipeWire package CI](https://github.com/seba970423/JamesDSP-Native-Arch-Remake/actions/workflows/build.yml/badge.svg)](https://github.com/seba970423/JamesDSP-Native-Arch-Remake/actions/workflows/build.yml)

Upstream JamesDSP, patched and packaged natively for Arch Linux and CachyOS.
**PipeWire only. Experimental binary release: 0.2.2, x86_64.**

The normal installer uses prebuilt engines. It does not clone upstream, download
submodules, or compile JamesDSP on your machine. The packaging follows the AUR
[jamesdsp-pipewire-bin recipe](https://github.com/archlinux/aur/blob/jamesdsp-pipewire-bin/PKGBUILD):
unpack the official PipeWire binary package, then package its resources with this
project's already-patched engine. Installing the stock upstream binary alone
would not include the device controls below.

Both standard and optional RT engines are bundled and verified by SHA-256. The
source patches remain maintained separately; complete corresponding engine
sources accompany the binaries in `prebuilt/corresponding-source-v0.2.2.tar.xz`.

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

The [post-merge GitHub Actions run](https://github.com/seba970423/JamesDSP-Native-Arch-Remake/actions/runs/40945452708)
passed **all three checks** on `main`:

- `layout-smoke`: Quickly checks the patched Devices/Tray layouts and EQ
  readability without compiling the complete DSP application.
- `package (standard)`: Builds and checks the standard source package.
- `package (rt)`: Builds and checks the optional PREEMPT_RT source package.

The smoke check runs before the two full source builds, preventing expensive
compilation when those UI regression tests fail. **Passing CI does not prove
every runtime behavior is correct.** The source-built CI packages are also
**distinct from the Ubuntu-built, checksum-verified prebuilt engines** selected
by the normal `./install.sh` workflow.

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

It then checks this project's binary releases, detects the running kernel,
downloads and verifies the official binary base,
selects the patched engine, repackages the files, and installs with pacman.
`makepkg` prepares an Arch package here; it does not compile C++.

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
running kernel; rerun `./install.sh --no-update` to select the matching prebuilt
profile. Both engine variants can run on an ordinary kernel.

## Updates, rollback and removal

```bash
./update.sh                    # check for this project's binary releases
./install.sh --no-update        # package/install this bundle's prebuilt engine
./rollback.sh --known-good      # reinstall the latest user-approved package
./rollback.sh                   # reinstall the preceding approved generation
./uninstall.sh
```

After installation the script asks whether playback/device switching worked.
Only a package you approve becomes `known-good`; the prior approved generation
is retained as `previous`. Rollback verifies the stored package checksum before
asking pacman to install it. Uninstall removes package-owned files and keeps
your presets and device rules.

The release check reports a newer published bundle's link. Download and extract
that complete bundle to update. Until releases are published, the bundled
verified engines are used. The installer never substitutes an unpatched upstream
engine or starts a source compilation as an update fallback.

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

The binary package's `check()` verifies the selected engine, probes its loader
with `--help`, and runs the portable checks. These supplied engines were built
on Ubuntu 24.04 with GCC 13.3.0, Qt 6.4.2 and PipeWire 1.0.5; they use native
shared libraries and require glibc 2.38 or later. Initial Arch-based hardware
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
smoke gate followed by complete standard and RT source package checks; all three
passed on `main` on 2026-10-29. This does not mean the normal installer uses
those source-build artifacts.

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
