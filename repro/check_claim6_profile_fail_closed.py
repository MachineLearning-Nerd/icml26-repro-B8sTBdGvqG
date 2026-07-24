"""Prove that the independent CPU profile checker rejects a truncated sweep."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-dir", type=Path, required=True)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="claim6-profile-tamper-") as tmp:
        copied = Path(tmp) / "evidence"
        shutil.copytree(args.artifact_dir, copied)
        profile_csv = copied / "route3_inference_profile.csv"
        lines = profile_csv.read_text(encoding="utf-8").splitlines()
        profile_csv.write_text("\n".join(lines[:-1]) + "\n", encoding="utf-8")
        completed = subprocess.run(
            [
                sys.executable,
                "repro/independent_check_claim6_cpu_profile.py",
                "--artifact-dir",
                str(copied),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        output = json.loads(
            (copied / "route3_profile_independent_checker.json").read_text()
        )
    passed = (
        completed.returncode != 0
        and not output["passed"]
        and not output["checks"]["inference_grid_has_12_points"]
    )
    result = {
        "claim_id": 6,
        "route": 3,
        "stage": "cpu calibration",
        "control": "remove one measured inference configuration",
        "tampered_checker_returncode": completed.returncode,
        "tampered_checker_passed": output["passed"],
        "truncation_detected": not output["checks"]["inference_grid_has_12_points"],
        "passed": passed,
    }
    (args.artifact_dir / "route3_profile_fail_closed.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print("CLAIM6_ROUTE3_PROFILE_FAIL_CLOSED=" + json.dumps(result, sort_keys=True))
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
