"""Digitize the two pinned Figure 4 source images without author result data."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import tarfile
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from PIL import Image


SOURCE_URL = "https://export.arxiv.org/e-print/2602.13848"
SOURCE_SHA256 = "850ea40712686ee84543348bf39550ead19e6240ad5f085c07654ef3ed1e4b4e"
USER_AGENT = (
    "OpenResearch-Reproduction/1.0 "
    "(claim audit; contact via MachineLearning-Nerd/icml26-repro-B8sTBdGvqG)"
)
POWER_MEMBER = "power_vs_step_by_calibsize_logx_w50.png"
RATIO_MEMBER = "rejection_time_ratio_vs_ctm_by_group_logy_logx.png"
IMAGE_HASHES = {
    POWER_MEMBER: "3ec26c59a6101229a024cd6493a4db55cffb6b35700ee9b50281c432b5e6600c",
    RATIO_MEMBER: "842f96dc197d8dd1cc24d59d722024f33e5a83d6876a86326436874dee5be96a",
}
POWER_COLORS = {
    100: (81, 18, 124),
    500: (183, 55, 121),
    4000: (252, 137, 97),
}
RATIO_COLORS = {
    "Noise": (102, 194, 165),
    "Blur": (252, 141, 98),
    "Weather": (141, 160, 203),
    "Digital": (231, 138, 195),
}
RATIO_X = {100: 371, 250: 623, 500: 814, 1000: 1004, 4000: 1385}
RATIO_Y_ONE = 550.0
RATIO_HALF_SPAN = 415.0
POWER_X_ZERO = 272.0
POWER_PIXELS_PER_DECADE = 318.5
POWER_Y_ZERO = 892.0
POWER_Y_ONE = 56.0
POWER_LEVELS = (0.1, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8)
METHOD_LEVELS = (0.1, 0.3, 0.5, 0.7, 0.8)
SIZE_LEVELS = (0.1, 0.4, 0.5, 0.6)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def download_source() -> bytes:
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            request = urllib.request.Request(
                SOURCE_URL, headers={"User-Agent": USER_AGENT}
            )
            with urllib.request.urlopen(request, timeout=120) as response:
                return response.read()
        except Exception as error:  # pragma: no cover - network retry
            last_error = error
            if attempt < 2:
                time.sleep(2**attempt)
    raise RuntimeError("arXiv source retrieval failed after three attempts") from last_error


def archive_member(archive: bytes, member: str) -> bytes:
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:*") as source:
        extracted = source.extractfile(member)
        if extracted is None:
            raise RuntimeError(f"missing source member: {member}")
        return extracted.read()


def image_array(data: bytes) -> np.ndarray:
    return np.asarray(Image.open(io.BytesIO(data)).convert("RGB"))


def ratio_from_y(y: float) -> float:
    return 2.0 ** ((RATIO_Y_ONE - y) / RATIO_HALF_SPAN)


def time_from_x(x: float) -> float:
    return 10.0 ** ((x - POWER_X_ZERO) / POWER_PIXELS_PER_DECADE)


def exact_color_mask(image: np.ndarray, color: tuple[int, int, int]) -> np.ndarray:
    return np.all(image == np.asarray(color, dtype=np.uint8), axis=2)


def digitize_ratio(image: np.ndarray) -> list[dict[str, object]]:
    yy, xx = np.indices(image.shape[:2])
    rows: list[dict[str, object]] = []
    for group, color in RATIO_COLORS.items():
        color_mask = exact_color_mask(image, color)
        for reference_size, center_x in RATIO_X.items():
            window = (
                color_mask
                & (xx >= center_x - 11)
                & (xx <= center_x + 11)
                & (yy >= 130)
                & (yy <= 970)
            )
            # The legend overlaps only the n=1000 x-window and begins below y=500.
            if reference_size == 1000:
                window &= yy < 500
            marker_y = np.where(window)[0]
            if marker_y.size < 25:
                raise RuntimeError(
                    f"too few exact marker pixels for {group}, n={reference_size}"
                )
            center_y = float(np.median(marker_y))
            rows.append(
                {
                    "group": group,
                    "reference_size": reference_size,
                    "marker_x": center_x,
                    "marker_y": center_y,
                    "ratio": ratio_from_y(center_y),
                    "exact_pixel_count": int(marker_y.size),
                }
            )
    return rows


def x_groups(columns: np.ndarray, maximum_gap: int = 7) -> list[tuple[int, int]]:
    if columns.size == 0:
        return []
    groups: list[tuple[int, int]] = []
    start = previous = int(columns[0])
    for value in columns[1:]:
        current = int(value)
        if current - previous > maximum_gap:
            groups.append((start, previous))
            start = current
        previous = current
    groups.append((start, previous))
    return groups


def digitize_power(image: np.ndarray) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for reference_size, color in POWER_COLORS.items():
        color_mask = exact_color_mask(image, color)
        for power in POWER_LEVELS:
            center_y = round(
                POWER_Y_ZERO - power * (POWER_Y_ZERO - POWER_Y_ONE)
            )
            columns = np.where(
                np.any(color_mask[center_y - 3 : center_y + 4, 270:950], axis=0)
            )[0] + 270
            groups = x_groups(columns)
            if not groups:
                raise RuntimeError(
                    f"no curve pixels for n={reference_size}, power={power}"
                )
            centers = [(left + right) / 2.0 for left, right in groups]
            conditional_x = centers[0]
            standard_x = centers[-1] if len(centers) >= 2 else None
            rows.append(
                {
                    "reference_size": reference_size,
                    "power": power,
                    "sampled_y": center_y,
                    "conditional_x": conditional_x,
                    "standard_x": standard_x,
                    "conditional_time": time_from_x(conditional_x),
                    "standard_time": (
                        time_from_x(standard_x) if standard_x is not None else None
                    ),
                    "x_group_count": len(groups),
                }
            )
    return rows


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-dir", type=Path, required=True)
    args = parser.parse_args()
    args.artifact_dir.mkdir(parents=True, exist_ok=True)

    archive = download_source()
    archive_hash = sha256(archive)
    if archive_hash != SOURCE_SHA256:
        raise SystemExit(
            f"source archive hash mismatch: {archive_hash} != {SOURCE_SHA256}"
        )
    image_bytes = {
        member: archive_member(archive, member)
        for member in (POWER_MEMBER, RATIO_MEMBER)
    }
    observed_hashes = {name: sha256(data) for name, data in image_bytes.items()}
    if observed_hashes != IMAGE_HASHES:
        raise SystemExit("Figure 4 image hash mismatch")

    power_rows = digitize_power(image_array(image_bytes[POWER_MEMBER]))
    ratio_rows = digitize_ratio(image_array(image_bytes[RATIO_MEMBER]))
    write_csv(args.artifact_dir / "route2_power_crossings.csv", power_rows)
    write_csv(args.artifact_dir / "route2_ratio_points.csv", ratio_rows)

    method_rows = [
        row
        for row in power_rows
        if row["reference_size"] in (500, 4000)
        and row["power"] in METHOD_LEVELS
    ]
    size_rows = {
        (int(row["reference_size"]), float(row["power"])): row
        for row in power_rows
    }
    ratio_scope = [
        row
        for row in ratio_rows
        if row["group"] in ("Blur", "Weather")
        and int(row["reference_size"]) >= 500
    ]
    method_comparisons = all(
        row["standard_x"] is not None
        and float(row["conditional_x"]) < float(row["standard_x"])
        for row in method_rows
    )
    size_comparisons = all(
        float(size_rows[(4000, level)]["conditional_x"])
        < float(size_rows[(500, level)]["conditional_x"])
        < float(size_rows[(100, level)]["conditional_x"])
        for level in SIZE_LEVELS
    )
    ratio_comparisons = all(float(row["ratio"]) > 1.0 for row in ratio_scope)

    reversed_method_hypothesis = all(
        row["standard_x"] is not None
        and float(row["standard_x"]) < float(row["conditional_x"])
        for row in method_rows
    )
    inverted_ratio_values = [
        2.0 ** ((float(row["marker_y"]) - RATIO_Y_ONE) / RATIO_HALF_SPAN)
        for row in ratio_scope
    ]
    inverted_ratio_hypothesis = all(value > 1.0 for value in inverted_ratio_values)
    controls = {
        "reversed_method_labels": {
            "wrong_hypothesis": "standard CTM crosses earlier at every audited point",
            "wrong_hypothesis_passed": reversed_method_hypothesis,
            "error_detected": not reversed_method_hypothesis,
        },
        "inverted_log_y_axis": {
            "wrong_hypothesis": "Blur and Weather remain above one after inverting the log-y calibration",
            "wrong_ratios": inverted_ratio_values,
            "wrong_hypothesis_passed": inverted_ratio_hypothesis,
            "error_detected": not inverted_ratio_hypothesis,
        },
    }
    controls_passed = all(
        control["error_detected"] for control in controls.values()
    )
    checks = {
        "source_archive_hash_matches": archive_hash == SOURCE_SHA256,
        "source_image_hashes_match": observed_hashes == IMAGE_HASHES,
        "all_20_ratio_markers_extracted": len(ratio_rows) == 20,
        "all_21_power_rows_extracted": len(power_rows) == 21,
        "conditional_earlier_at_10_method_points": len(method_rows) == 10
        and method_comparisons,
        "conditional_crossings_improve_with_size_at_4_levels": size_comparisons,
        "blur_weather_ratios_above_one_for_n_ge_500": len(ratio_scope) == 6
        and ratio_comparisons,
        "negative_controls_detected": controls_passed,
    }
    passed = all(checks.values())
    (args.artifact_dir / "route2_negative_controls.json").write_text(
        json.dumps(controls, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    result = {
        "claim_id": 6,
        "route": 2,
        "route_name": "pinned source-figure digitization",
        "retrieval": {
            "url": SOURCE_URL,
            "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
            "user_agent": USER_AGENT,
            "source_sha256": archive_hash,
            "image_sha256": observed_hashes,
        },
        "calibration": {
            "ratio_y_one": RATIO_Y_ONE,
            "ratio_half_span_pixels": RATIO_HALF_SPAN,
            "power_x_zero": POWER_X_ZERO,
            "power_pixels_per_decade": POWER_PIXELS_PER_DECADE,
            "power_y_zero": POWER_Y_ZERO,
            "power_y_one": POWER_Y_ONE,
        },
        "audited_counts": {
            "method_points": len(method_rows),
            "size_levels": len(SIZE_LEVELS),
            "blur_weather_ratio_points": len(ratio_scope),
        },
        "checks": checks,
        "route_audit_passed": passed,
        "claim_verdict": "BLOCKED",
        "reason": (
            "The pinned published figure encodes the claimed comparisons, "
            "but digitizing the authors' plot is not an independent ImageNet-C run."
        ),
        "runtime_context": {
            "expected_core_count": 1,
            "selected_backend": "hf",
            "selected_flavor": "cpu-upgrade",
            "os_cpu_count": os.cpu_count(),
            "affinity_count": len(os.sched_getaffinity(0))
            if hasattr(os, "sched_getaffinity")
            else None,
        },
    }
    (args.artifact_dir / "route2_figure_audit.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print("CLAIM6_ROUTE2_FIGURE_AUDIT=" + json.dumps(result, sort_keys=True))
    print("CLAIM6_ROUTE2_NEGATIVE_CONTROLS=" + json.dumps(controls, sort_keys=True))
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
