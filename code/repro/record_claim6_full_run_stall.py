"""Record Claim 6 Route 3 full-reconstruction stall evidence.

The raw evidence channel for local OpenResearch runs is `orx logs`; this script
does not re-query provider state from inside a remote run. It freezes the
audited run identifiers and the invariant facts observed before the release
prep branch was created, then fail-closes if the record is incomplete or
overclaims a Claim 6 verdict.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


COMPONENT_RUNS = [
    ("gaussian_noise", "98293293-7f81-4c36-a2ec-3a4a741f91c4", 66696),
    ("shot_noise", "ec485fb7-aed7-4d62-bc11-db24857213bf", 66764),
    ("impulse_noise", "dbcd0fb0-9c92-4032-92fa-22bf4a03cca5", 66699),
    ("defocus_blur", "fd62248b-888b-48fe-9da1-1812b2f0d08e", 66650),
    ("glass_blur", "c8caee94-8974-4a6e-a457-89c2340316cc", 66640),
    ("motion_blur", "0503cc0d-f0d3-4820-856c-67eb478f450c", 66699),
    ("zoom_blur", "6f2f522e-637b-468a-8b8a-768157647a9a", 66659),
    ("snow", "25eaca56-6a05-4bbb-bb56-bd14539107e0", 66646),
    ("frost", "1786946a-9716-434b-b8ef-9d7c68b9dbce", 66649),
    ("fog", "7ea602c8-0e5a-4def-8b9b-ee86a5f6fe54", 66635),
    ("brightness", "62b90f5e-675b-4eee-b40c-841d91e7a98b", 66704),
    ("contrast", "e1aa95a8-353e-41ca-a3bd-d1c263830924", 66722),
    ("elastic_transform", "2afb935a-d180-4376-8328-19720f1bf23d", 66761),
    ("pixelate", "c0196538-109a-4d46-aad6-b99bd9a04272", 66700),
    ("jpeg_compression", "52059e09-134b-4e18-91af-c98db7a0867e", 66780),
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-dir", type=Path, required=True)
    args = parser.parse_args()
    args.artifact_dir.mkdir(parents=True, exist_ok=True)

    runs = [
        {
            "component": component,
            "run_id": run_id,
            "log_bytes_before_cancel": log_bytes,
            "status_before_cancel_request": "running",
            "duration_before_cancel_request": "about 25h48m to 26h03m",
            "clean_checkpoint_found": False,
            "corruption_checkpoint_found": False,
            "terminal_summary_found": False,
            "traceback_or_oom_marker_found": False,
            "cancel_requested": True,
        }
        for component, run_id, log_bytes in COMPONENT_RUNS
    ]
    checks = {
        "all_15_components_recorded": len(runs) == 15,
        "all_cancel_requested": all(run["cancel_requested"] for run in runs),
        "no_run_reached_clean_checkpoint": not any(
            run["clean_checkpoint_found"] for run in runs
        ),
        "no_run_reached_corruption_checkpoint": not any(
            run["corruption_checkpoint_found"] for run in runs
        ),
        "no_terminal_claim6_summary_found": not any(
            run["terminal_summary_found"] for run in runs
        ),
        "log_lengths_are_nonempty": all(
            run["log_bytes_before_cancel"] > 60000 for run in runs
        ),
    }
    result = {
        "claim_id": 6,
        "route": 3,
        "route_name": "full ImageNet-C reconstruction attempt",
        "claim_verdict": "BLOCKED",
        "passed": all(checks.values()),
        "checks": checks,
        "observed_from": {
            "project_id": "bb7fdc4c-b42f-461a-a45f-5fdcd907f3c2",
            "evidence_channel": "orx runs plus orx logs --bytes 1000000",
            "observed_at_local_time": "2026-07-26 Asia/Kolkata",
        },
        "runs": runs,
        "reason": (
            "All 15 full-reconstruction component jobs remained marked running "
            "after roughly 26 hours, exceeded the intended 16-hour HF timeout, "
            "and their logs stopped before the first clean-inference checkpoint. "
            "No full-scope ImageNet-C numerical evidence was produced."
        ),
    }
    (args.artifact_dir / "route3_full_reconstruction_stall.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print("CLAIM6_ROUTE3_FULL_RECONSTRUCTION_STALL=" + json.dumps(result, sort_keys=True))
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
