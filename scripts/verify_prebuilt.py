#!/usr/bin/env python3
import argparse
import hashlib
import json
from pathlib import Path
import struct


def verify(root, profile):
    root = Path(root)
    manifest = json.loads((root / "manifest.json").read_text())
    if manifest["architecture"] != "x86_64" or profile not in ("standard", "rt"):
        raise ValueError("Unsupported prebuilt engine profile")
    entry = manifest["profiles"][profile]
    path = root / profile / "jamesdsp"
    data = path.read_bytes()
    if data[:6] != b"\x7fELF\x02\x01" or struct.unpack_from("<H", data, 18)[0] != 62:
        raise ValueError("The engine is not an x86_64 ELF executable")
    if hashlib.sha256(data).hexdigest() != entry["sha256"]:
        raise ValueError("The prebuilt engine checksum does not match its manifest")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Verify a prebuilt patched JamesDSP engine")
    parser.add_argument("root")
    parser.add_argument("profile", choices=("standard", "rt"))
    args = parser.parse_args()
    verify(args.root, args.profile)
    print("Prebuilt patched engine verified:", args.profile)
