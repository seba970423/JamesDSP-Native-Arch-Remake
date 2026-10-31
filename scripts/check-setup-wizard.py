#!/usr/bin/env python3
"""Static guard for the Settings -> Run setup wizard Qt signal path.

The source build additionally checks Qt connect signatures at compile time;
a real GUI test is still needed to confirm the wizard is displayed.
"""
import argparse
from pathlib import Path
import re
import sys


def require(pattern: str, source: str, description: str) -> None:
    if not re.search(pattern, source, re.MULTILINE):
        raise AssertionError(f"Missing setup-wizard wiring: {description}")


def check(root: Path) -> None:
    mw = (root / "src/MainWindow.cpp").read_text()
    settings = (root / "src/interface/fragment/SettingsFragment.cpp").read_text()
    wizard = (root / "src/interface/fragment/FirstLaunchWizard.cpp").read_text()
    require(
        r"^\s*connect\s*\(\s*_settingsFragment->fragment\(\)\s*,"
        r"\s*&SettingsFragment::launchSetupWizard\s*,\s*this\s*,"
        r"\s*&MainWindow::launchFirstRunSetup\s*\)\s*;",
        mw,
        "SettingsFragment::launchSetupWizard -> MainWindow::launchFirstRunSetup",
    )
    require(
        r"^\s*connect\s*\(\s*ui->run_first_launch\s*,"
        r"\s*&QPushButton::clicked\s*,\s*this\s*,"
        r"\s*&SettingsFragment::onSetupWizardLaunchClicked\s*\)\s*;",
        settings,
        "Run setup wizard button -> click handler",
    )
    require(
        r"QTimer::singleShot\s*\(\s*300\s*,\s*this\s*,"
        r"\s*&SettingsFragment::launchSetupWizard\s*\)",
        settings,
        "click handler -> delayed launch signal",
    )
    require(r"void\s+MainWindow::launchFirstRunSetup\s*\(\s*\)", mw,
            "wizard launch method")
    launch = mw.split("void MainWindow::launchFirstRunSetup()", 1)[1]
    require(r"new\s+FirstLaunchWizard\s*\(", launch, "wizard constructed")
    require(r"lightBox->show\s*\(", launch, "wizard overlay shown")
    require(r"wizardFinished", wizard, "wizard completion logic")
    print("Setup-wizard wiring contract passed (static guard).")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("source_tree", type=Path)
    args = parser.parse_args()
    try:
        check(args.source_tree)
    except (OSError, AssertionError, IndexError) as exc:
        print(f"Setup wizard regression: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
