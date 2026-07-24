"""Require the independent group checker to reject missing raw evidence."""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
import tempfile
from pathlib import Path


SMOKE_FILES = (
    "route3_smoke_input_manifest.json",
    "route3_smoke_result.json",
    "route3_smoke_controls.json",
)
GROUP_FILES = (
    "route3_group_input_manifest.json",
    "route3_group_result.json",
    "route3_group_controls.json",
    "route3_group_aggregates.csv",
    "route3_group_power.csv",
    "route3_group_inference.csv",
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-dir", type=Path, required=True)
    args = parser.parse_args()
    full_group = (args.artifact_dir / "route3_group_result.json").exists()
    prefix = "route3_group" if full_group else "route3_smoke"
    source_csv = args.artifact_dir / f"{prefix}_trials.csv"
    files = GROUP_FILES if full_group else SMOKE_FILES
    with source_csv.open(encoding="utf-8", newline="") as source:
        rows = list(csv.DictReader(source))

    with tempfile.TemporaryDirectory() as temporary:
        target = Path(temporary)
        for name in files:
            (target / name).write_bytes((args.artifact_dir / name).read_bytes())
        with (target / source_csv.name).open(
            "w", encoding="utf-8", newline=""
        ) as output:
            writer = csv.DictWriter(output, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows[:-1])
        completed = subprocess.run(
            [
                sys.executable,
                str(Path(__file__).with_name("independent_check_claim6_group.py")),
                "--artifact-dir",
                str(target),
            ],
            text=True,
            capture_output=True,
            check=False,
        )
    result = {
        "claim_id": 6,
        "route": 3,
        "stage": (
            "full component verifier fail-closed control"
            if full_group
            else "smoke verifier fail-closed control"
        ),
        "mutation": "deleted one raw trial row",
        "checker_exit_code": completed.returncode,
        "error_detected": completed.returncode != 0,
    }
    (args.artifact_dir / f"{prefix}_fail_closed.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n"
    )
    label = (
        "CLAIM6_ROUTE3_GROUP_FAIL_CLOSED"
        if full_group
        else "CLAIM6_ROUTE3_SMOKE_FAIL_CLOSED"
    )
    print(label + "=" + json.dumps(result, sort_keys=True))
    if completed.returncode == 0:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
