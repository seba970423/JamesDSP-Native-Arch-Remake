#!/usr/bin/env python3
"""Run a noisy packaging/build command with a log and 30-second heartbeats."""
import argparse
import os
from pathlib import Path
import selectors
import signal
import subprocess
import sys
import time


def elapsed(seconds):
    seconds = int(seconds)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def stage_line(record):
    if not record.startswith("@@JDSP_STEP@@"):
        return None
    try:
        label, completed, total = record.removeprefix("@@JDSP_STEP@@").strip().split("|")
        completed, total = int(completed), int(total)
        if not 0 <= completed <= total or total <= 0:
            return None
        percent = completed * 100 // total
        filled = percent // 5
        return f"{label}: [{'#' * filled}{'-' * (20-filled)}] {percent:3d}%"
    except ValueError:
        return None


def run(command, label, log_path, interval=30):
    log_path = Path(log_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    start = time.monotonic()
    deadline = start + interval
    print(f"{label} started. Full output: {log_path}", flush=True)
    env = dict(os.environ, JDSP_PROGRESS_PROTOCOL="1", PYTHONUNBUFFERED="1")
    with log_path.open("wb") as log:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   env=env, start_new_session=True)
        selector = selectors.DefaultSelector()
        selector.register(process.stdout, selectors.EVENT_READ)
        pending = b""
        try:
            while selector.get_map():
                for key, _ in selector.select(timeout=min(0.2, max(0, deadline-time.monotonic()))):
                    data = os.read(key.fd, 65536)
                    if not data:
                        selector.unregister(key.fileobj)
                        continue
                    log.write(data)
                    log.flush()
                    pending += data
                    records = pending.split(b"\n")
                    pending = records.pop()
                    for record in records:
                        rendered = stage_line(record.decode("utf-8", errors="replace").strip())
                        if rendered:
                            print(rendered, flush=True)
                now = time.monotonic()
                if now >= deadline and process.poll() is None:
                    print(f"{label} — elapsed {elapsed(now-start)} — still running", flush=True)
                    deadline = now + interval
            code = process.wait()
        except KeyboardInterrupt:
            os.killpg(process.pid, signal.SIGINT)
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
            return 130
        finally:
            selector.close()
            process.stdout.close()
    if code:
        print(f"{label} failed after {elapsed(time.monotonic()-start)}. Last log lines:", file=sys.stderr)
        print("\n".join(log_path.read_text(errors="replace").splitlines()[-20:]), file=sys.stderr)
        print(f"Full log: {log_path}", file=sys.stderr)
    else:
        print(f"{label} finished in {elapsed(time.monotonic()-start)}.", flush=True)
    return code if code >= 0 else 128-code


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--label", required=True)
    parser.add_argument("--log", required=True)
    parser.add_argument("--interval", type=float, default=30)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command or args.interval <= 0:
        parser.error("A command and a positive heartbeat interval are required")
    return run(command, args.label, args.log, args.interval)


if __name__ == "__main__":
    raise SystemExit(main())
