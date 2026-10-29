#!/usr/bin/env python3
"""Read the running kernel's preemption support. Never change kernel settings."""
import argparse
import gzip
import json
import platform
from pathlib import Path


def detect_kernel(root=Path("/"), release=None):
    release = release or platform.release()
    result = {"release": release, "preempt_rt": None, "model": "unknown", "evidence": []}
    realtime = root / "sys/kernel/realtime"
    try:
        value = realtime.read_text().strip()
        if value in ("0", "1"):
            result["preempt_rt"] = value == "1"
            result["evidence"].append("/sys/kernel/realtime=" + value)
    except OSError:
        pass
    config = None
    for name in ("proc/config.gz", "boot/config-" + release, "usr/lib/modules/" + release + "/config"):
        try:
            path = root / name
            data = gzip.decompress(path.read_bytes()) if name.endswith(".gz") else path.read_bytes()
            text = data.decode("utf-8")
            if "CONFIG_" not in text:
                continue
            config = set(text.splitlines())
            result["evidence"].append("/" + name)
            break
        except (OSError, EOFError, UnicodeError):
            pass
    if result["preempt_rt"] is None and config is not None:
        result["preempt_rt"] = "CONFIG_PREEMPT_RT=y" in config
    if result["preempt_rt"] is True:
        result["model"] = "PREEMPT_RT"
    elif config:
        if "CONFIG_PREEMPT_DYNAMIC=y" in config:
            result["model"] = "dynamic preemption (not PREEMPT_RT)"
        elif "CONFIG_PREEMPT=y" in config:
            result["model"] = "full preemption (not PREEMPT_RT)"
        elif "CONFIG_PREEMPT_VOLUNTARY=y" in config:
            result["model"] = "voluntary preemption"
        else:
            result["model"] = "standard kernel"
    elif result["preempt_rt"] is False:
        result["model"] = "standard kernel (PREEMPT_RT inactive)"
    result["patch_profile"] = "rt" if result["preempt_rt"] is True else "standard"
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("/"), help="Alternate filesystem root for offline tests")
    parser.add_argument("--release", help="Release name for offline config tests")
    parser.add_argument("--profile", action="store_true", help="Print rt or standard for the installer")
    args = parser.parse_args()
    result = detect_kernel(args.root, args.release)
    print(result["patch_profile"] if args.profile else json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
