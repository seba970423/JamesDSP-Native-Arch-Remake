# Validation and hardware checks

This experimental release needs Arch/CachyOS and real hardware testing before
it can be called stable. Build and automated results for the delivered binary
bundle are recorded in VALIDATION.md.

## Binary installation and progress

On an Arch/CachyOS machine missing prerequisites, run `./install.sh` directly.
Pacman should offer `base-devel`, Python and any other missing dependencies
before kernel detection or Python checks begin. Declining that transaction
should stop the installer. `./install.sh --dry-run` should still work without
Python/makepkg and should not request authentication or install anything.

1. Cancel any older source installer before extracting the complete bundle.
2. Run `./install.sh --dry-run`, then `./install.sh --no-update` as your normal
   user. The normal path should not clone a repository or invoke a C++ compiler.
3. Check the official binary download's percentage, byte total and speed. A
   second run should report the verified download as cached.
4. Check the engine preparation and package assembly step bars. Slow operations
   should emit elapsed-time updates every 30 seconds. Percentages count finished
   steps; they do not estimate the time remaining.
5. Check that pacman's dependency and final installation bars and prompts remain
   visible. Do not use `--noconfirm` for this manual test.
6. Open `~/jamesdsp-native-arch-logs/` in your file manager. The installer prints
   each log path; failures should also show the last 20 log lines in the terminal.
   Existing logs from the old XDG state location should be copied here without
   replacing existing files.
7. Confirm `pacman -Q jamesdsp-native-arch` and inspect
   `/usr/share/jamesdsp-native-arch/build-profile.json`. It should identify the
   prebuilt distribution and selected RT flag.

The reported 0.2.0-1 failure happened after makepkg had created the package:
`pacman -Qp --print-format` rejected the incompatible option. Revision 2 queries
the archive with `pacman -Qpq`, then proceeds to pacman's installation prompt.

The bundle contains native shared-library executables built on Ubuntu 24.04.
The package checks the selected executable with `--help` before installation to
catch missing libraries or loader incompatibilities. This check does not prove
audio or Qt interface compatibility on the target machine.

## Settings and equalizer readability

1. Open Settings → Devices at the main window's usual compact size. The
   explanation, table, new-device toggle, status and refresh button must not
   overlap. Scroll down to reach application exclusions and back to the table.
2. Increase your desktop font size or scaling and repeat. Check that full device
   and route names can be read in tooltips when table cells are elided.
3. Open Graphic EQ in 31-band mode. The bottom frequency labels must remain
   separated; every band and gain value must remain present.
4. Resize the window and zoom the plot. Labels should adapt without changing
   the EQ curve. Test 15-band and variable modes as well.
5. Check that unselected tabs and fixed-frequency table values remain readable.
   Fixed frequencies should stay locked against editing; gain cells retain
   their usual editing behavior. Repeat with a dark palette if used.

Automated UI tests run against Qt 6.4.2 using its offscreen plugin. The Devices
test loads the real upstream Settings form, replacing only the unrelated tray
menu editor with a plain widget. Target Plasma/Qt rendering remains a hardware
check; the reported machine uses Qt 6.12.0.

## Tray icon appearance

1. Open Settings → Tray icon → Icon appearance. Try Automatic, Light, Dark and
   Color. Each change must update the system tray immediately.
2. Use Light on a dark panel and Dark on a light panel. Also check a mixed setup
   with a light application theme and dark panel. A manual selection must win
   over a theme-provided tray icon.
3. Close and relaunch JamesDSP; the selected appearance must be retained.
4. Change the desktop palette while JamesDSP is running. Automatic should use
   the icon theme, falling back to application colors when no themed icon is
   available. Manual choices must remain unchanged. Then edit the tray context
   menu and confirm the appearance is still retained.
5. Repeat at a larger font size or display scaling and check that the selector
   and its explanation remain readable.

Offscreen tests cover rendered light/dark fallback, a theme icon override,
manual choices, configuration notifications, menu recreation and persistence.
The actual Plasma tray host and panel recoloring still need a target check.

## Device routing

1. Start with the laptop output selected as default in Plasma.
2. Open Settings → Devices. Enable its speaker route and play audio.
3. Disable that route during playback. Audio should continue directly.
4. Enable the headphone route while leaving the speakers disabled. Plug/unplug
   headphones, checking that the selected route's saved choice takes effect.
5. Connect Bluetooth headphones and a speaker. Enable effects for headphones and
   leave the speaker disabled. Switch the default output through Plasma.
6. Assign a second application explicitly to a different physical output in
   Plasma. It should retain that output during default-device and effect changes.
   In this release that second output plays directly: there is one DSP engine.
7. Quit JamesDSP through its tray menu. Previously intercepted applications
   should return to their saved destinations. Restart and check saved rules.
8. Disconnect/reconnect Bluetooth and USB devices. Check that rules are tied to
   device/route names rather than old numeric node IDs.
9. Test Bluetooth A2DP versus a headset call profile. An unsupported link should
   keep native playback instead of leaving the app on an unconnected DSP sink.
10. Test application exclusion and allowlist mode, including an excluded app with
    a destination explicitly selected in Plasma.

## Kernel and scheduling

Run `./install.sh --dry-run` on ordinary and PREEMPT_RT kernels. Ordinary,
PREEMPT_DYNAMIC/full, and unverifiable configurations should select `standard`;
verified PREEMPT_RT should select `rt`. Check the installed build-profile JSON
and compare the app's running-kernel status after booting a different kernel.

Run `jamesdsp-native-diagnostics --json` during playback. Inspect the audio
data thread's actual policy/priority separately from the GUI thread. Compare
PipeWire errors/underruns and playback under CPU load at the same rate and quantum
before attempting a smaller buffer. RT scheduling or a successful build alone
does not prove an improvement.

## Brave repeats the preceding video's last audio fragment

Keep the same output device and repeat the same video transitions in Brave:

1. Effects enabled for the output.
2. Output's effects rule disabled, leaving native playback.
3. JamesDSP completely exited through its tray menu.

If it persists with JamesDSP exited, compare the same transitions in Firefox.
Record Brave, JamesDSP, PipeWire and WirePlumber versions, the active device,
and which cases reproduce. A difference between cases identifies a path to
investigate; it does not by itself identify the faulty component.

Do not automatically restart PipeWire or change global buffer settings during
this comparison, because that changes multiple variables at once.
