#!/usr/bin/env python3
"""Keep Git source-download progress visible when installer output is logged."""
import codecs
import os
import re
import signal
import subprocess
import sys


PROGRESS = re.compile(
    r"^(?:remote:\s*)?(Counting objects|Compressing objects|Receiving objects|"
    r"Resolving deltas|Updating files|Checking out files|Indexing objects):\s*(\d{1,3})%\s*(.*)$"
)
TRANSFER = re.compile(r",\s*([\d.]+\s*[KMGTPE]?i?B)(?:\s*\|\s*([\d.]+\s*[KMGTPE]?i?B/s))?")
ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")


def with_progress(arguments):
    """Return forced-progress download arguments, or None for other Git calls."""
    index = 0
    takes_value = {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--config-env", "--super-prefix"}
    while index < len(arguments) and arguments[index].startswith("-"):
        index += 2 if arguments[index] in takes_value else 1
    if index >= len(arguments):
        return None
    command = arguments[index]
    offset = index + 1
    if command == "submodule":
        if offset >= len(arguments) or arguments[offset] != "update":
            return None
        offset += 1
    elif command not in {"clone", "fetch", "pull"}:
        return None
    result = arguments[:offset] + [arg for arg in arguments[offset:] if arg not in {"-q", "--quiet"}]
    if "--progress" not in result[offset:]:
        result.insert(offset, "--progress")
    return result


def progress_line(record):
    match = PROGRESS.match(ANSI.sub("", record).strip())
    if not match:
        return None
    phase, value, details = match.groups()
    percent = int(value)
    if not 0 <= percent <= 100:
        return None
    width = 20
    filled = percent * width // 100
    bar = "#" * filled + "-" * (width - filled)
    label = "Download" if phase == "Receiving objects" else phase
    result = f"{label}: [{bar}] {percent:3d}%"
    transfer = TRANSFER.search(details)
    if transfer:
        size, speed = transfer.groups()
        result += "  " + size
        if speed:
            result += " | " + speed
    return result


class Display:
    def __init__(self, stream, interactive):
        self.stream = stream
        self.interactive = interactive
        self.previous_width = 0
        self.last_progress = None

    def record(self, record):
        if not record:
            return
        rendered = progress_line(record)
        if rendered:
            if rendered == self.last_progress:
                return
            self.last_progress = rendered
            if self.interactive:
                padding = " " * max(0, self.previous_width - len(rendered))
                self.stream.write("\r" + rendered + padding)
                self.previous_width = len(rendered)
            else:
                self.stream.write(rendered + "\n")
        else:
            self.finish_line()
            self.stream.write(record + "\n")
        self.stream.flush()

    def finish_line(self):
        if self.previous_width:
            self.stream.write("\n")
            self.previous_width = 0
        self.stream.flush()


def run(real_git, arguments, stream=sys.stderr):
    forced = with_progress(arguments)
    if forced is None or os.environ.get("JDSP_GIT_PROGRESS_ACTIVE") == "1":
        os.execv(real_git, [real_git, *arguments])
    interactive = os.environ.get("JDSP_PROGRESS_TTY") == "1" or stream.isatty()
    display = Display(stream, interactive)
    display.record("Source download: waiting for Git transfer statistics...")
    env = dict(os.environ, LC_ALL="C", JDSP_GIT_PROGRESS_ACTIVE="1")
    child = subprocess.Popen([real_git, *forced], stderr=subprocess.PIPE, env=env)
    decoder = codecs.getincrementaldecoder("utf-8")("replace")
    pending = ""
    try:
        while True:
            chunk = os.read(child.stderr.fileno(), 4096)
            if not chunk:
                break
            pending += decoder.decode(chunk)
            records = re.split(r"[\r\n]", pending)
            pending = records.pop()
            for record in records:
                display.record(record)
        pending += decoder.decode(b"", final=True)
        display.record(pending)
        code = child.wait()
        display.finish_line()
        if code == 0 and display.last_progress is None:
            display.record("Git source check complete (no object-transfer statistics reported).")
        return code if code >= 0 else 128 - code
    except KeyboardInterrupt:
        child.send_signal(signal.SIGINT)
        try:
            child.wait(timeout=5)
        except subprocess.TimeoutExpired:
            child.kill()
            child.wait()
        display.finish_line()
        return 130
    finally:
        child.stderr.close()


def main():
    real_git = os.environ.get("JDSP_REAL_GIT")
    if not real_git or not os.path.isabs(real_git):
        print("Missing absolute JDSP_REAL_GIT path.", file=sys.stderr)
        return 2
    return run(real_git, sys.argv[1:])


if __name__ == "__main__":
    raise SystemExit(main())
