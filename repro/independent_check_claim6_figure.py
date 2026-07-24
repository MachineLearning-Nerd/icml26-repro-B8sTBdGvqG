"""Independent arithmetic checker for Claim 6 Route 2 digitization outputs."""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path


METHOD_LEVELS = {0.1, 0.3, 0.5, 0.7, 0.8}
SIZE_LEVELS = {0.1, 0.4, 0.5, 0.6}
SOURCE_SHA256 = "850ea40712686ee84543348bf39550ead19e6240ad5f085c07654ef3ed1e4b4e"
IMAGE_HASHES = {
    "power_vs_step_by_calibsize_logx_w50.png": (
        "3ec26c59a6101229a024cd6493a4db55cffb6b35700ee9b50281c432b5e6600c"
    ),
    "rejection_time_ratio_vs_ctm_by_group_logy_logx.png": (
        "842f96dc197d8dd1cc24d59d722024f33e5a83d6876a86326436874dee5be96a"
    ),
}
CALIBRATION = {
    "ratio_y_one": 550.0,
    "ratio_half_span_pixels": 415.0,
    "power_x_zero": 272.0,
    "power_pixels_per_decade": 318.5,
    "power_y_zero": 892.0,
    "power_y_one": 56.0,
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as source:
        return list(csv.DictReader(source))


def close(left: float, right: float, tolerance: float = 1e-10) -> bool:
    return math.isclose(left, right, rel_tol=tolerance, abs_tol=tolerance)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-dir", type=Path, required=True)
    args = parser.parse_args()

    audit = json.loads(
        (args.artifact_dir / "route2_figure_audit.json").read_text()
    )
    controls = json.loads(
        (args.artifact_dir / "route2_negative_controls.json").read_text()
    )
    power = read_csv(args.artifact_dir / "route2_power_crossings.csv")
    ratios = read_csv(args.artifact_dir / "route2_ratio_points.csv")
    ratio_recomputed = all(
        close(
            float(row["ratio"]),
            2.0
            ** (
                (CALIBRATION["ratio_y_one"] - float(row["marker_y"]))
                / CALIBRATION["ratio_half_span_pixels"]
            ),
        )
        for row in ratios
    )
    time_recomputed = all(
        close(
            float(row["conditional_time"]),
            10.0
            ** (
                (float(row["conditional_x"]) - CALIBRATION["power_x_zero"])
                / CALIBRATION["power_pixels_per_decade"]
            ),
        )
        and (
            row["standard_time"] == ""
            or close(
                float(row["standard_time"]),
                10.0
                ** (
                    (float(row["standard_x"]) - CALIBRATION["power_x_zero"])
                    / CALIBRATION["power_pixels_per_decade"]
                ),
            )
        )
        for row in power
    )
    method_rows = [
        row
        for row in power
        if int(row["reference_size"]) in (500, 4000)
        and float(row["power"]) in METHOD_LEVELS
    ]
    power_lookup = {
        (int(row["reference_size"]), float(row["power"])): row for row in power
    }
    ratio_scope = [
        row
        for row in ratios
        if row["group"] in ("Blur", "Weather")
        and int(row["reference_size"]) >= 500
    ]
    reversed_method_hypothesis = all(
        row["standard_x"] != ""
        and float(row["standard_x"]) < float(row["conditional_x"])
        for row in method_rows
    )
    inverted_ratio_hypothesis = all(
        2.0
        ** (
            (float(row["marker_y"]) - CALIBRATION["ratio_y_one"])
            / CALIBRATION["ratio_half_span_pixels"]
        )
        > 1.0
        for row in ratio_scope
    )
    checks = {
        "audit_remains_nonclaiming": audit["claim_verdict"] == "BLOCKED",
        "route_audit_passed": audit["route_audit_passed"],
        "source_hash_reconstructed": audit["retrieval"]["source_sha256"]
        == SOURCE_SHA256,
        "image_hashes_reconstructed": audit["retrieval"]["image_sha256"]
        == IMAGE_HASHES,
        "axis_calibration_reconstructed": audit["calibration"] == CALIBRATION,
        "raw_row_counts_match": len(power) == 21 and len(ratios) == 20,
        "ratio_transform_recomputed": ratio_recomputed,
        "time_transform_recomputed": time_recomputed,
        "method_grid_nonvacuous": len(method_rows) == 10,
        "conditional_precedes_standard": all(
            row["standard_x"] != ""
            and float(row["conditional_x"]) < float(row["standard_x"])
            for row in method_rows
        ),
        "size_grid_nonvacuous": all(
            (size, level) in power_lookup
            for size in (100, 500, 4000)
            for level in SIZE_LEVELS
        ),
        "larger_reference_crosses_earlier": all(
            float(power_lookup[(4000, level)]["conditional_x"])
            < float(power_lookup[(500, level)]["conditional_x"])
            < float(power_lookup[(100, level)]["conditional_x"])
            for level in SIZE_LEVELS
        ),
        "ratio_grid_nonvacuous": len(ratio_scope) == 6,
        "blur_weather_ratios_above_one": all(
            float(row["ratio"]) > 1.0 for row in ratio_scope
        ),
        "reversed_method_control_detected": not reversed_method_hypothesis
        and controls["reversed_method_labels"]["error_detected"]
        and not controls["reversed_method_labels"]["wrong_hypothesis_passed"],
        "inverted_axis_control_detected": not inverted_ratio_hypothesis
        and controls["inverted_log_y_axis"]["error_detected"]
        and not controls["inverted_log_y_axis"]["wrong_hypothesis_passed"],
    }
    passed = all(checks.values())
    result = {
        "claim_id": 6,
        "route": 2,
        "independent": True,
        "imports_digitizer_or_author_code": False,
        "checks": checks,
        "passed": passed,
        "claim_verdict": "BLOCKED",
    }
    (args.artifact_dir / "route2_independent_checker.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print("CLAIM6_ROUTE2_INDEPENDENT=" + json.dumps(result, sort_keys=True))
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
