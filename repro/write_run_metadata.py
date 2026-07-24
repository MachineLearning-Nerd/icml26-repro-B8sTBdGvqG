#!/usr/bin/env python
"""Write non-secret, machine-readable CPU and provenance metadata."""

from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
from pathlib import Path


def git_output(*args: str) -> str:
    return subprocess.check_output(["git", *args], text=True).strip()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--started-at", required=True)
    parser.add_argument("--runtime-seconds", type=float, required=True)
    parser.add_argument("--expected-cores", type=int, required=True)
    parser.add_argument("--selected-backend", required=True)
    parser.add_argument("--selected-flavor", required=True)
    args = parser.parse_args()

    affinity = None
    if hasattr(os, "sched_getaffinity"):
        affinity = len(os.sched_getaffinity(0))

    payload = {
        "actual_cpu_allocation": {
            "affinity_count": affinity,
            "os_cpu_count": os.cpu_count(),
        },
        "expected_core_count": args.expected_cores,
        "git_branch": git_output("branch", "--show-current"),
        "git_sha": git_output("rev-parse", "HEAD"),
        "platform": platform.platform(),
        "python": platform.python_version(),
        "runtime_seconds": args.runtime_seconds,
        "selected_backend": args.selected_backend,
        "selected_flavor": args.selected_flavor,
        "started_at_utc": args.started_at,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload, sort_keys=True))


if __name__ == "__main__":
    main()
