#!/usr/bin/env python3
"""Download a pinned binary with real byte progress, throughput and SHA-256 verification."""
import argparse
import hashlib
import os
from pathlib import Path
import sys
import time
import urllib.request


def size(value):
    for unit in ("B", "KiB", "MiB", "GiB"):
        if value < 1024 or unit == "GiB":
            return f"{value:.1f} {unit}"
        value /= 1024


def digest(path):
    result = hashlib.sha256()
    with Path(path).open("rb") as file:
        for chunk in iter(lambda: file.read(1024*1024), b""):
            result.update(chunk)
    return result.hexdigest()


def download(url, destination, expected, stream=sys.stdout):
    destination = Path(destination)
    if destination.is_file() and digest(destination) == expected:
        print(f"Download: [{'#' * 20}] 100%  cached and verified", file=stream, flush=True)
        return
    partial = destination.with_name(destination.name + ".part")
    start = time.monotonic()
    received = 0
    last = start
    last_count = 0
    interactive = os.environ.get("JDSP_PROGRESS_TTY") == "1" or stream.isatty()
    previous = 0

    def render(total, final=False):
        nonlocal last, last_count, previous
        now = time.monotonic()
        speed = (received-last_count) / max(now-last, 0.001)
        if total:
            percent = min(100, int(received*100/total))
            filled = percent//5
            text = f"Download: [{'#'*filled}{'-'*(20-filled)}] {percent:3d}%  {size(received)}/{size(total)} | {size(speed)}/s"
        else:
            text = f"Download: {size(received)} | {size(speed)}/s (total size not reported)"
        if interactive:
            stream.write("\r" + text + " "*max(0, previous-len(text)))
            previous = len(text)
            if final:
                stream.write("\n")
        else:
            stream.write(text+"\n")
        stream.flush()
        last, last_count = now, received

    try:
        request = urllib.request.Request(url, headers={"User-Agent": "JamesDSP-Native-Arch-Remake/0.2"})
        print("Connecting to binary download...", file=stream, flush=True)
        with urllib.request.urlopen(request, timeout=30) as response, partial.open("wb") as output:
            total = int(response.headers.get("Content-Length", "0"))
            for chunk in iter(lambda: response.read(65536), b""):
                output.write(chunk)
                received += len(chunk)
                if time.monotonic()-last >= 0.25:
                    render(total)
            if total and received != total:
                raise RuntimeError(f"Incomplete download: {received} of {total} bytes")
            render(total, final=True)
        if digest(partial) != expected:
            raise RuntimeError("Binary download checksum does not match the pinned SHA-256")
        partial.replace(destination)
        print("Download checksum verified.", file=stream, flush=True)
    finally:
        partial.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url")
    parser.add_argument("destination")
    parser.add_argument("sha256")
    args = parser.parse_args()
    if len(args.sha256) != 64 or any(c not in "0123456789abcdef" for c in args.sha256):
        parser.error("A lowercase SHA-256 is required")
    try:
        download(args.url, args.destination, args.sha256)
    except (OSError, RuntimeError, ValueError) as error:
        print(f"Download failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
