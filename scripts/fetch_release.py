#!/usr/bin/env python3
"""Download verified, profile-matched packages from published GitHub Releases.

Exit 0: verified newer package; 3: no newer release; 1: validation failure.
"""
import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

from download import download

REPO = "seba970423/JamesDSP-Native-Arch-Remake"
API_URL = f"https://api.github.com/repos/{REPO}/releases/latest"
BUNDLED_VERSION = (0, 2, 2)
UA = "JamesDSP-Native-Arch-Remake/release-fetch"


def version_tuple(tag):
    if not re.fullmatch(r"v?[0-9]+\.[0-9]+\.[0-9]+", tag):
        raise ValueError(f"Unsupported release tag: {tag!r}")
    return tuple(int(v) for v in tag.removeprefix("v").split("."))


def release_asset(release, name):
    matches = [a for a in release.get("assets", []) if a.get("name") == name]
    if len(matches) != 1:
        raise ValueError(f"Missing or duplicate release asset: {name}")
    url = matches[0].get("browser_download_url", "")
    tag = release["tag_name"]
    if not url.startswith(f"https://github.com/{REPO}/releases/download/{tag}/"):
        raise ValueError(f"Untrusted release asset URL: {name}")
    return url


def package_asset_name(tag, profile):
    if profile not in ("standard", "rt"):
        raise ValueError("Invalid kernel profile")
    return f"jamesdsp-native-arch-{tag.removeprefix('v')}-{profile}-x86_64.pkg.tar.zst"


def expected_hash(text, name):
    matches = []
    for line in text.splitlines():
        match = re.fullmatch(r"([0-9a-f]{64})  (\S+)", line)
        if match and match.group(2) == name:
            matches.append(match.group(1))
    if len(matches) != 1:
        raise ValueError(f"Missing or duplicate SHA-256 checksum for {name}")
    return matches[0]


def fetch(profile, destination):
    request = urllib.request.Request(API_URL, headers={"User-Agent": UA, "Accept": "application/vnd.github+json"})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            release = json.load(response)
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            print("No published stable release; bundled 0.2.2 remains available.")
            return 3
        raise
    tag = release["tag_name"]
    if version_tuple(tag) <= BUNDLED_VERSION:
        print(f"No release newer than bundled 0.2.2 (latest: {tag}).")
        return 3
    if release.get("draft") or release.get("prerelease"):
        raise ValueError("Release must be stable and published")
    name = package_asset_name(tag, profile)
    archive = release_asset(release, name)
    checksum_url = release_asset(release, "SHA256SUMS")
    with urllib.request.urlopen(urllib.request.Request(checksum_url, headers={"User-Agent": UA}), timeout=20) as response:
        manifest = response.read(65537)
    if len(manifest) > 65536:
        raise ValueError("Oversized checksum manifest")
    expected = expected_hash(manifest.decode("utf-8"), name)
    print(f"Verified release selected: {tag} ({profile})")
    download(archive, destination, expected)
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=["standard", "rt"], required=True)
    parser.add_argument("--destination", type=Path, required=True)
    options = parser.parse_args()
    try:
        return fetch(options.profile, options.destination)
    except (OSError, ValueError, KeyError, RuntimeError, urllib.error.URLError) as exc:
        print(f"Release download or verification failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
