# Validation — 2026-10-29

Release 0.2.2 adds persistent tray icon appearance choices. It retains the Devices
and EQ layout fixes, Bash dependency bootstrapping, package-query fix and visible
Home log folder. Both engine profiles were rebuilt for this release.

Upstream source: `Audio4Linux/JDSP4Linux`, commit
`3ea7d733c090409c00887db3bb3aaf3af79ea692`, with the four exact submodule commits
pinned in `packaging/PKGBUILD.source`. Release 0.2.2 distributes prebuilt native
engines and an Arch binary-repack recipe. The supplied engines were compiled
on Ubuntu, not in Arch CI. The normal installer does not compile JamesDSP.

Completed in the build environment (Ubuntu 24.04, GCC 13.3.0, Qt 6.4.2,
PipeWire headers/library 1.0.5):

| Check | Result |
| --- | --- |
| Full Qt/PipeWire application, standard patch profile | Compiled and linked |
| Full Qt/PipeWire application, optional RT patch profile | Compiled and linked |
| Kernel detection and scheduling diagnostics | 10 Python tests passed |
| Binary package inputs, checksums and absence of source compilation | 2 Python tests passed |
| Download percentage/speed, checksum rejection, Git progress and quiet-runner heartbeat | 8 Python tests passed |
| Real pacman archive/dependency queries, invalid archive/list failures, visible Home logs and non-overwriting migration | 5 Python tests passed |
| Bash dependency bootstrap, missing Python/makepkg, declined transactions, query errors, dry runs and su fallback | 7 Python tests passed |
| Device policy persistence, route precedence and malformed-file handling | C++ regression executable passed |
| Production routing controller against a deterministic PipeWire boundary | C++ regression executable passed |
| Tray icon theme lookup, light/dark fallback, manual overrides, immediate updates, menu recreation and saved preferences | C++/Qt rendered-icon regression passed |
| Actual Qt checkbox updates and route isolation | C++ GUI test passed |
| Devices widget inside the real Settings form | Passed at 685×365, 700×450 and 1000×650 with 9, 12 and 16 point fonts; preview inspected |
| Graphic EQ labels, fonts, zoom and band preservation | Passed in light/dark palettes at compact and larger sizes; previews inspected |
| Enabled-tab colors and fixed-frequency table readability | Passed; frequency cells remain read-only |
| Responsive-interface patch against the original nine source files | Applied cleanly; patched bytes match build inputs |
| New tray patch against the exact 0.2.1 corresponding-source baseline | Applied cleanly; all five changed files match build inputs |
| Fresh upstream checkout, common source-patch baseline retained from 0.2.1 | Source recipe prepare passed for standard and RT profiles in 0.2.1; these patches are unchanged |
| Binary recipe prepare/check/package, standard profile | Passed; selected engine checksum and installed profile verified |
| Binary recipe prepare/check/package, RT profile | Passed; selected engine checksum and installed profile verified |
| Selected prebuilt executables' loader probes (`--help`) | Both profiles passed on the build host |
| Official binary base download over HTTPS with new progress helper | Passed; 5,579,292 bytes, pinned SHA-256 verified |
| Bash syntax and ShellCheck | Passed |
| Installer dry run on the ordinary build-host kernel | Selected standard profile; no compilation or installation changes |

All 32 portable tests passed, including queries of real synthetic
Arch package archives using pacman 6.0.2/libalpm 13.0.2. The package-list boundary
is supplied by a test command; archive reads use the real pacman executable.
Checks cover a debug archive before the main archive, paths containing spaces,
corrupt archives and package-list errors. Shell syntax and ShellCheck also pass.
The shell scan checks maintained script locations rather than traversing
generated package trees.

Bootstrap tests run with an isolated command path containing no Python or
makepkg. A controlled pacman transaction supplies these tools, and subsequent
steps are reached only after the dependency/tool checks pass. Cancellation,
dependency-query failure and dry-run cases perform no installation. The su
fallback preserves arguments containing spaces. Package writes/authentication
are simulated in these tests; the additional real-pacman dependency query is
read-only. A full fresh Arch/CachyOS prerequisite transaction remains a target
machine check.

The former Devices layout was reproduced at 685×365, with three intersecting
pairs of child controls. The replacement uses the same Settings form and a
scroll area; automated checks found no intersecting controls across all nine
size/font combinations and confirmed the lower application controls can be
scrolled into view. Only the unrelated tray-menu editor is replaced in this
form test. The original standalone-widget preview did not cover this parent
layout constraint.

Graphic EQ checks run the real GraphicEQWidget and FlatTabWidget components.
They verify non-overlapping, bounded frequency labels; sufficient ruler height;
normal text colors for enabled tabs; readable, non-editable fixed frequencies;
and unchanged band data during resizing and zooming. The test also exercises
15-band, 31-band and variable modes. These checks and visual inspection used
Qt 6.4.2's offscreen plugin. They do not establish the exact appearance under
the target machine's Qt 6.12.0/Plasma theme.

Subsequent user screenshots and feedback confirm the Devices page is usable
under the target Qt 6.12.0/Plasma environment, including automatic discovery,
saved disconnected-device rules, PREEMPT_RT detection, the matching installed
profile and one reported real-time thread. This is user-reported desktop
validation; testing on the Dell is still pending.

The tray regression renders the actual QSystemTrayIcon image. It verifies that
Automatic uses a supplied theme icon and falls back to contrasting light/dark
resources without one. Explicit Light, Dark and Color choices bypass the theme
and stay fixed across palette changes and tray-menu recreation. Reloaded
configuration retains the choice. The real Settings form's tray page is also
checked at three window sizes and three font sizes, including readable wrapped
text and scrolling to the selector without horizontal clipping. Native Plasma
tray-host rendering still requires a target-machine check.

The supplied target-machine logs show that the RT engine passed verification
and its loader probe, and makepkg completed the actual 0.2.0-1 Arch package in
four seconds. Installation then stopped at the invalid query option before
`pacman -U`. Revision 2 replaces this query with `pacman -Qpq`; the target-machine
installation still needs to be rerun to confirm the complete transaction.

Binary staging executed the real `prepare()`, `check()` and `package()` functions
for each profile with the official release payload. The recipe has no `build()`
function. It did not invoke a compiler. Pacman's actual transaction bars could
not be exercised on this Ubuntu host; the installer preserves its original
terminal file descriptors for pacman's own bars and prompts.

The base resources come from the same official 2.7.0 PipeWire `.deb` referenced
by `jamesdsp-pipewire-bin`; the executable is replaced with the patched engine
at the commit above. The engine archive, each profile, helper inputs and complete
corresponding-source archive have recorded SHA-256 checksums. ELF inspection
found ordinary native shared-library dependencies, Qt 6/6.4 public symbol
versions (no Qt private symbol versions), and a minimum glibc symbol requirement
of 2.38. This inspection is not a substitute for running on Arch/CachyOS.

The routing regression covers default-device changes, exact destination
restoration, app exclusions, shutdown restoration, destroyed/reused stream IDs,
and modern or legacy session managers updating only one target-metadata key.

The kernel fixtures cover active PREEMPT_RT, a matching running-kernel config,
ordinary/full/dynamic preemption, missing/corrupt data, kernel names that merely
contain "rt", and runtime evidence taking precedence over config. Diagnostics
also recognize RTKit's RESET_ON_FORK scheduling flag and report inaccessible
thread information as unavailable.

Limits of this validation:

- This environment prohibits the Unix sockets required to start an isolated
  D-Bus/PipeWire audio session. A live graph test could not start. The automated
  routing tests replace the PipeWire boundary; they do not prove real playback.
- No real Bluetooth, USB audio, laptop route switching, or Brave playback was
  tested here. Follow docs/testing.md on the target machine.
- Both variants were compiled on an ordinary kernel. Positive PREEMPT_RT
  detection was tested with fixtures; scheduler latency and performance gains
  were not measured on an actual PREEMPT_RT system.
- Arch's complete makepkg/pacman installation transaction was not executed on
  this Ubuntu build host. Both profiles passed the binary recipe's preparation,
  checks and package staging; the included Arch source-build CI matrix is
  configured but has not run here. A loader probe before installation helps
  catch target-library mismatches but cannot prove GUI or audio compatibility.
- No fix for Brave's replayed audio fragment is claimed.
