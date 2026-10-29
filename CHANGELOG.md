# 0.2.2 — tray icon appearance

- Add saved Automatic, Light, Dark and Color choices under Settings → Tray icon.
- Update the icon immediately when the choice changes, including after rebuilding
  the tray menu. Explicit choices bypass theme icons so a dark theme-provided
  icon cannot override the user's light choice.
- Keep automatic icon-theme lookup with a palette-based fallback; stop treating
  GTK_THEME as evidence of a KDE panel's appearance.
- Let the Tray settings page scroll at compact sizes or larger fonts, keep its
  explanation readable, and shorten the close-behavior labels to fit.
- Rebuild both prebuilt engines and supply the matching complete sources.
- Add rendered-icon checks for light/dark fallback, theme overrides, live changes,
  menu recreation and saved preferences.

# 0.2.1-2 — offer prerequisites through pacman

- Bootstrap dependency checks in Bash before requiring Python or makepkg.
- Offer missing `base-devel`, Python and declared runtime/packaging dependencies
  through pacman's normal package list and confirmation prompt.
- Stop if the transaction is declined, fails, or leaves required tools missing.
- Keep sudo authentication, with su available when sudo has not been installed.
- Let dry runs work before Python/makepkg are available. Remove the manual
  prerequisite installation step from the README.
- Add prerequisite-flow regression tests. Retain the existing prebuilt engines.

# 0.2.1 — settings layout and EQ readability

- Put the complete Devices page in a vertical scroll area so controls retain
  their layout when the settings panel is too small for all the content.
- Keep table rows on one line, expose full route names in tooltips, and make
  status text and control labels fit more naturally.
- Show only EQ ruler labels that fit, sized using the active font. Preserve all
  bands and gain values, including while resizing and zooming.
- Size ruler margins for the font, keep fixed frequency cells readable while
  preventing edits, and use normal text colors for enabled, unselected tabs.
- Preserve the application's palette in Graphic EQ.
- Test the actual settings form at three sizes and three font sizes. Add light
  and dark Graphic EQ tests for spacing, zoom, band preservation and tab colors.
- Rebuild both prebuilt engines; installation still does not compile JamesDSP.

# 0.2.0-2 — installer fixes and visible Home logs

- Fix package discovery after successful packaging: use pacman's supported
  `-Qpq` archive query instead of the invalid query/`--print-format` combination.
- Report missing/corrupt archives and package-list failures explicitly before
  attempting installation. Handle debug packages and cache paths with spaces.
- Keep logs directly in `~/jamesdsp-native-arch-logs/` for both install and source
  builds. Copy former XDG logs there without replacing existing files.
- Limit shell checks to maintained scripts, avoiding generated `src`/`pkg`
  directories and the reported permission warning.
- Retain the same verified engines; no source compilation added.

# 0.2.0 — prebuilt installation and visible progress

- Follow the `jamesdsp-pipewire-bin` packaging model: unpack the official binary
  base and install an already-patched engine. No local JamesDSP compilation,
  upstream checkout or submodule downloads in the normal install path.
- Bundle verified standard and optional RT engines, a build manifest and complete
  corresponding sources. Retain the in-app device/route controls.
- Select the optional RT engine only for confirmed running-kernel PREEMPT_RT;
  otherwise install the standard engine normally.
- Show download percentage, byte totals and speed; show completed-step progress
  for engine preparation and package assembly; preserve pacman's native bars.
- Keep noisy output in logs, report elapsed time every 30 seconds, and display
  the last log lines on failure.
- Keep source updates/builds in explicit maintainer scripts, with Git progress
  and the same quiet compile timer. Check project binary releases by default.
- Probe the selected executable before replacing the installed package.
- Add progress/download regression coverage. Real audio and Arch transaction
  testing remain required; Brave's replay issue remains unresolved.

# 0.1.0 — initial experimental patchset

- PipeWire-only native Arch/CachyOS packaging from pinned upstream/submodules.
- Persistent per-device/route effects policy with opt-in defaults.
- Default-output following while preserving explicit application destinations.
- Restore owned stream metadata on device exclusion and clean exit.
- Detect PREEMPT_RT and skip the optional patch when absent/unverifiable.
- Limited optional scratch-allocation optimization and thread diagnostics.
- Installer logs, validated upstream-pin updates, user-approved rollback copies,
  pacman-based removal, and kernel/policy/routing regression checks.
- Brave's audio-fragment replay remains under investigation.
