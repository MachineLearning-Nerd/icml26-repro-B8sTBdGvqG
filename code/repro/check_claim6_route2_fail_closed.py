"""Prove that the Route 2 verifier rejects tampered raw evidence."""

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

    with tempfile.TemporaryDirectory(prefix="claim6-route2-tamper-") as tmp:
        copied = Path(tmp) / "evidence"
        shutil.copytree(args.artifact_dir, copied)
        ratio_csv = copied / "route2_ratio_points.csv"
        lines = ratio_csv.read_text(encoding="utf-8").splitlines()
        ratio_csv.write_text("\n".join(lines[:-1]) + "\n", encoding="utf-8")
        completed = subprocess.run(
            [
                sys.executable,
                "repro/verify_claim6_route2.py",
                "--artifact-dir",
                str(copied),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        tampered_output = json.loads(
            (copied / "route2_verifier_output.json").read_text()
        )

    passed = (
        completed.returncode != 0
        and not tampered_output["passed"]
        and not tampered_output["checks"]["raw_ratio_rows_present"]
    )
    result = {
        "claim_id": 6,
        "route": 2,
        "control": "remove one raw ratio row",
        "tampered_verifier_returncode": completed.returncode,
        "tampered_verifier_passed": tampered_output["passed"],
        "missing_row_detected": not tampered_output["checks"][
            "raw_ratio_rows_present"
        ],
        "passed": passed,
    }
    (args.artifact_dir / "route2_verifier_fail_closed.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print("CLAIM6_ROUTE2_FAIL_CLOSED=" + json.dumps(result, sort_keys=True))
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
