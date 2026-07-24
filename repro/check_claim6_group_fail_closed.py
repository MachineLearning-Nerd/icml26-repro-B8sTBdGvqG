"""Require the independent smoke checker to reject missing raw evidence."""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
import tempfile
from pathlib import Path


FILES = (
    "route3_smoke_input_manifest.json",
    "route3_smoke_result.json",
    "route3_smoke_controls.json",
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-dir", type=Path, required=True)
    args = parser.parse_args()
    source_csv = args.artifact_dir / "route3_smoke_trials.csv"
    with source_csv.open(encoding="utf-8", newline="") as source:
        rows = list(csv.DictReader(source))

    with tempfile.TemporaryDirectory() as temporary:
        target = Path(temporary)
        for name in FILES:
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
        "stage": "smoke verifier fail-closed control",
        "mutation": "deleted one raw trial row",
        "checker_exit_code": completed.returncode,
        "error_detected": completed.returncode != 0,
    }
    (args.artifact_dir / "route3_smoke_fail_closed.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n"
    )
    print("CLAIM6_ROUTE3_SMOKE_FAIL_CLOSED=" + json.dumps(result, sort_keys=True))
    if completed.returncode == 0:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
