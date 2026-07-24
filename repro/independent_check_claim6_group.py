"""Independent structural/arithmetic checker for Claim 6 group artifacts."""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

import numpy as np


PINNED_REVISIONS = {
    "model": "063c6c38a5d8510b2e57df480445e94b231dad2c",
    "clean": "55405c49dece42420e68ddd5f80174f19b29ebaf",
    "corruption": "bb0fa9db6d8f94ef279a1f6bbb8024736d542fd7",
}
FULL_REFERENCE_SIZES = [100, 250, 500, 1000, 4000]
FULL_SEEDS = list(range(10))
POWER_HORIZONS = [100, 250, 500, 1000, 2000, 5000, 10000, 20000, 37500]
GROUPS = {
    "Noise": ["gaussian_noise", "shot_noise", "impulse_noise"],
    "Blur": ["defocus_blur", "glass_blur", "motion_blur", "zoom_blur"],
    "Weather": ["snow", "frost", "fog"],
    "Digital": [
        "brightness",
        "contrast",
        "elastic_transform",
        "pixelate",
        "jpeg_compression",
    ],
}


def csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as source:
        return list(csv.DictReader(source))


def run_full_check(artifact_dir: Path) -> None:
    manifest = json.loads(
        (artifact_dir / "route3_group_input_manifest.json").read_text()
    )
    result = json.loads(
        (artifact_dir / "route3_group_result.json").read_text()
    )
    controls = json.loads(
        (artifact_dir / "route3_group_controls.json").read_text()
    )
    trials = csv_rows(artifact_dir / "route3_group_trials.csv")
    aggregates = csv_rows(artifact_dir / "route3_group_aggregates.csv")
    power = csv_rows(artifact_dir / "route3_group_power.csv")
    inference = csv_rows(artifact_dir / "route3_group_inference.csv")
    group = manifest["config"]["group"]
    config = manifest["config"]
    corruptions = config.get("corruptions", [])
    canonical_group = GROUPS.get(group, [])

    observed_grid = {
        (
            row["corruption"],
            int(row["seed"]),
            int(row["reference_size"]),
        )
        for row in trials
    }
    expected_grid = {
        (corruption, seed, reference_size)
        for corruption in corruptions
        for seed in FULL_SEEDS
        for reference_size in FULL_REFERENCE_SIZES
    }
    trial_arithmetic = []
    for row in trials:
        conditional = int(row["conditional_capped_crossing"])
        standard = int(row["standard_capped_crossing"])
        horizon = int(row["horizon"])
        trial_arithmetic.append(
            int(row["conditional_first_crossing"]) < horizon
            and int(row["standard_first_crossing"]) < horizon
            and 1 <= conditional <= horizon + 1
            and 1 <= standard <= horizon + 1
            and math.isclose(
                float(row["standard_over_conditional_ratio"]),
                standard / conditional,
                rel_tol=1e-12,
                abs_tol=1e-12,
            )
        )

    aggregate_exact = []
    bootstrap_rng = np.random.default_rng(260_213_848)
    expected_entities = corruptions + ["__group__"]
    aggregate_lookup = {
        (row["entity"], int(row["reference_size"])): row
        for row in aggregates
    }
    for entity in expected_entities:
        for reference_size in FULL_REFERENCE_SIZES:
            raw = [
                row
                for row in trials
                if int(row["reference_size"]) == reference_size
                and (
                    entity == "__group__"
                    or row["corruption"] == entity
                )
            ]
            conditional = np.asarray(
                [int(row["conditional_capped_crossing"]) for row in raw],
                dtype=float,
            )
            standard = np.asarray(
                [int(row["standard_capped_crossing"]) for row in raw],
                dtype=float,
            )
            ratios = []
            for _ in range(2000):
                sampled_seeds = bootstrap_rng.choice(FULL_SEEDS, 10, replace=True)
                sampled = [
                    row
                    for seed in sampled_seeds
                    for row in raw
                    if int(row["seed"]) == int(seed)
                ]
                sampled_conditional = np.asarray(
                    [
                        int(row["conditional_capped_crossing"])
                        for row in sampled
                    ],
                    dtype=float,
                )
                sampled_standard = np.asarray(
                    [
                        int(row["standard_capped_crossing"])
                        for row in sampled
                    ],
                    dtype=float,
                )
                ratios.append(
                    float(
                        np.median(sampled_standard)
                        / np.median(sampled_conditional)
                    )
                )
            reported = aggregate_lookup[(entity, reference_size)]
            median_conditional = float(np.median(conditional))
            median_standard = float(np.median(standard))
            aggregate_exact.append(
                int(reported["trials"]) == len(raw)
                and math.isclose(
                    float(reported["conditional_median_capped_crossing"]),
                    median_conditional,
                    rel_tol=0.0,
                    abs_tol=1e-12,
                )
                and math.isclose(
                    float(reported["standard_median_capped_crossing"]),
                    median_standard,
                    rel_tol=0.0,
                    abs_tol=1e-12,
                )
                and math.isclose(
                    float(
                        reported[
                            "standard_over_conditional_median_ratio"
                        ]
                    ),
                    median_standard / median_conditional,
                    rel_tol=1e-12,
                    abs_tol=1e-12,
                )
                and math.isclose(
                    float(reported["conditional_detection_rate"]),
                    float(np.mean(conditional <= 37_500)),
                    rel_tol=1e-12,
                    abs_tol=1e-12,
                )
                and math.isclose(
                    float(reported["standard_detection_rate"]),
                    float(np.mean(standard <= 37_500)),
                    rel_tol=1e-12,
                    abs_tol=1e-12,
                )
                and math.isclose(
                    float(reported["ratio_seed_cluster_bootstrap_ci_low"]),
                    float(np.quantile(ratios, 0.025)),
                    rel_tol=1e-12,
                    abs_tol=1e-12,
                )
                and math.isclose(
                    float(reported["ratio_seed_cluster_bootstrap_ci_high"]),
                    float(np.quantile(ratios, 0.975)),
                    rel_tol=1e-12,
                    abs_tol=1e-12,
                )
            )

    power_lookup = {
        (int(row["reference_size"]), int(row["horizon"])): row
        for row in power
    }
    power_exact = []
    for reference_size in FULL_REFERENCE_SIZES:
        raw = [
            row
            for row in trials
            if int(row["reference_size"]) == reference_size
        ]
        for horizon in POWER_HORIZONS:
            reported = power_lookup[(reference_size, horizon)]
            conditional = np.mean(
                [
                    0 <= int(row["conditional_first_crossing"]) <= horizon
                    for row in raw
                ]
            )
            standard = np.mean(
                [
                    0 <= int(row["standard_first_crossing"]) <= horizon
                    for row in raw
                ]
            )
            power_exact.append(
                int(reported["trials"]) == len(raw)
                and math.isclose(
                    float(reported["conditional_power"]),
                    float(conditional),
                    rel_tol=1e-12,
                    abs_tol=1e-12,
                )
                and math.isclose(
                    float(reported["standard_power"]),
                    float(standard),
                    rel_tol=1e-12,
                    abs_tol=1e-12,
                )
            )

    canonical_scope = (
        config["mode"] == "full-group"
        and corruptions == canonical_group
    ) or (
        config["mode"] == "full-corruption"
        and len(corruptions) == 1
        and corruptions[0] in canonical_group
    )
    checks = {
        "checker_is_independent": True,
        "pinned_revisions_reconstructed": (
            manifest["model"]["revision"] == PINNED_REVISIONS["model"]
            and manifest["clean"]["revision"] == PINNED_REVISIONS["clean"]
            and manifest["corruption"]["revision"]
            == PINNED_REVISIONS["corruption"]
        ),
        "canonical_scope_reconstructed": (
            canonical_scope
            and config["reference_sizes"] == FULL_REFERENCE_SIZES
            and config["seeds"] == FULL_SEEDS
            and config["clean_pool_size"] == 12_500
            and config["stream_size"] == 37_500
        ),
        "manifest_checks_pass": all(manifest["checks"].values()),
        "exact_trial_grid": (
            len(trials) == len(expected_grid)
            and observed_grid == expected_grid
        ),
        "trial_arithmetic_recomputed": all(trial_arithmetic),
        "aggregate_grid_and_bootstrap_recomputed": (
            len(aggregates)
            == (len(corruptions) + 1) * len(FULL_REFERENCE_SIZES)
            and all(aggregate_exact)
        ),
        "power_grid_recomputed": (
            len(power)
            == len(FULL_REFERENCE_SIZES) * len(POWER_HORIZONS)
            and all(power_exact)
        ),
        "inference_counts_and_hashes_present": (
            len(inference) == 1 + len(corruptions)
            and all(int(row["images"]) == 50_000 for row in inference)
            and all(
                len(row["entropy_float64_sha256"]) == 64 for row in inference
            )
        ),
        "controls_reconstructed": (
            controls["full_label_alignment"]["all_match"]
            and controls["rolled_corruption_labels"]["error_detected"]
            and controls["disjoint_partition"][
                "all_cover_50000_without_overlap"
            ]
            and controls["entropy_extremes"]["error_detected"]
            and controls["reversed_ratio_interpretation"]["error_detected"]
        ),
        "result_checks_pass": all(result["checks"].values()),
        "component_cannot_decide_full_claim": (
            manifest["mode"] in {"full-group", "full-corruption"}
            and result["claim_verdict"] == "BLOCKED"
        ),
    }
    passed = all(checks.values())
    output = {
        "claim_id": 6,
        "route": 3,
        "stage": (
            f"independent full-group check: {group}"
            if config["mode"] == "full-group"
            else "independent full-corruption check: " + corruptions[0]
        ),
        "imports_runner_or_author_code": False,
        "checks": checks,
        "passed": passed,
        "claim_verdict": "BLOCKED",
    }
    (artifact_dir / "route3_group_independent_checker.json").write_text(
        json.dumps(output, indent=2, sort_keys=True) + "\n"
    )
    print("CLAIM6_ROUTE3_GROUP_INDEPENDENT=" + json.dumps(output, sort_keys=True))
    if not passed:
        raise SystemExit(1)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-dir", type=Path, required=True)
    args = parser.parse_args()
    if (args.artifact_dir / "route3_group_input_manifest.json").exists():
        run_full_check(args.artifact_dir)
        return
    manifest = json.loads(
        (args.artifact_dir / "route3_smoke_input_manifest.json").read_text()
    )
    result = json.loads(
        (args.artifact_dir / "route3_smoke_result.json").read_text()
    )
    controls = json.loads(
        (args.artifact_dir / "route3_smoke_controls.json").read_text()
    )
    with (args.artifact_dir / "route3_smoke_trials.csv").open(
        encoding="utf-8", newline=""
    ) as source:
        rows = list(csv.DictReader(source))

    observed_grid = {
        (int(row["seed"]), int(row["reference_size"])) for row in rows
    }
    expected_grid = {(seed, size) for seed in (0, 1) for size in (32, 64)}
    row_arithmetic = []
    for row in rows:
        conditional = int(row["conditional_capped_crossing"])
        standard = int(row["standard_capped_crossing"])
        horizon = int(row["horizon"])
        ratio = float(row["standard_over_conditional_ratio"])
        row_arithmetic.append(
            0 <= conditional <= horizon + 1
            and 0 <= standard <= horizon + 1
            and math.isclose(
                ratio, standard / conditional, rel_tol=1e-12, abs_tol=1e-12
            )
        )

    checks = {
        "checker_is_independent": True,
        "pinned_revisions_reconstructed": (
            manifest["model"]["revision"] == PINNED_REVISIONS["model"]
            and manifest["clean"]["revision"] == PINNED_REVISIONS["clean"]
            and manifest["corruption"]["revision"]
            == PINNED_REVISIONS["corruption"]
        ),
        "manifest_checks_pass": all(manifest["checks"].values()),
        "exact_smoke_grid": len(rows) == 4 and observed_grid == expected_grid,
        "row_arithmetic_recomputed": all(row_arithmetic),
        "scope_counts_reconstructed": (
            result["scope"]["clean_images"] == 128
            and result["scope"]["corruption_images"] == 256
            and result["paper_scope"]["corruptions"] == 15
        ),
        "controls_reconstructed": (
            controls["aligned_labels"]["labels_match"]
            and controls["rolled_corruption_labels"]["error_detected"]
            and controls["entropy_extremes"]["error_detected"]
            and controls["reversed_ratio_interpretation"]["error_detected"]
        ),
        "result_checks_pass": all(result["checks"].values()),
        "smoke_cannot_be_claim_evidence": (
            manifest["mode"] == "smoke"
            and result["stage"] == "end-to-end pipeline smoke validation"
            and result["claim_verdict"] == "BLOCKED"
        ),
    }
    passed = all(checks.values())
    output = {
        "claim_id": 6,
        "route": 3,
        "stage": "independent smoke-artifact check",
        "imports_runner_or_author_code": False,
        "checks": checks,
        "passed": passed,
        "claim_verdict": "BLOCKED",
    }
    (args.artifact_dir / "route3_smoke_independent_checker.json").write_text(
        json.dumps(output, indent=2, sort_keys=True) + "\n"
    )
    print("CLAIM6_ROUTE3_SMOKE_INDEPENDENT=" + json.dumps(output, sort_keys=True))
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
