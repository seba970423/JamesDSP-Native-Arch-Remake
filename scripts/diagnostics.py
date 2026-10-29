#!/usr/bin/env python3
"""Report the running kernel and actual JamesDSP thread scheduling."""
import argparse
import importlib.util
import json
import os
from pathlib import Path


def load_kernel_helper():
    paths = [Path(__file__).resolve().with_name("kernel_info.py"),
             Path("/usr/lib/jamesdsp-native-arch/kernel_info.py")]
    for path in paths:
        if path.is_file():
            spec = importlib.util.spec_from_file_location("jdsp_kernel_info", path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module.detect_kernel()
    return {"model": "unknown", "preempt_rt": None, "evidence": [], "patch_profile": "standard"}


def collect_threads(proc=Path("/proc")):
    threads = []
    available = False
    try:
        processes = list(proc.iterdir())
    except OSError:
        return threads, available
    names = {getattr(os, key, -99): key.removeprefix("SCHED_")
             for key in ("SCHED_OTHER", "SCHED_FIFO", "SCHED_RR", "SCHED_BATCH", "SCHED_IDLE", "SCHED_DEADLINE")}
    names[6] = "DEADLINE"
    for process in processes:
        if not process.name.isdigit():
            continue
        try:
            if process.joinpath("comm").read_text().strip() != "jamesdsp":
                continue
            for task in process.joinpath("task").iterdir():
                tid = int(task.name)
                try:
                    raw_policy = os.sched_getscheduler(tid)
                    policy = raw_policy & ~getattr(os, "SCHED_RESET_ON_FORK", 0x40000000)
                    priority = os.sched_getparam(tid).sched_priority
                    threads.append({"pid": int(process.name), "tid": tid,
                        "name": task.joinpath("comm").read_text().strip(),
                        "policy": names.get(policy, str(policy)), "priority": priority,
                        "reset_on_fork": policy != raw_policy,
                        "realtime": policy in (getattr(os, "SCHED_FIFO", -1), getattr(os, "SCHED_RR", -1), 6)})
                    available = True
                except (OSError, ValueError):
                    pass
        except (OSError, ValueError):
            pass
    return threads, available


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    profile = "unknown"
    try:
        metadata = json.loads(Path("/usr/share/jamesdsp-native-arch/build-profile.json").read_text())
        profile = "PREEMPT_RT" if metadata["rt_patches"] else "standard"
    except (OSError, ValueError, KeyError):
        pass
    threads, available = collect_threads()
    result = {"kernel": load_kernel_helper(), "build_profile": profile,
              "threads": threads, "threads_available": available}
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print("Kernel:", result["kernel"]["model"])
        print("Optional RT patch build:", profile)
        if not available:
            print("Thread scheduling unavailable; start JamesDSP and run this as the same user.")
        for thread in threads:
            print(f"  TID {thread['tid']}: {thread['name']} — {thread['policy']} priority {thread['priority']}")


if __name__ == "__main__":
    main()
