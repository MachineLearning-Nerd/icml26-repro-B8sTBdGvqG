"""Audit whether the official release can regenerate Figure 4."""

from __future__ import annotations

import argparse
import ast
import json
import os
import subprocess
import sys
from pathlib import Path


CORRUPTIONS = (
    "gaussian_noise",
    "shot_noise",
    "impulse_noise",
    "defocus_blur",
    "glass_blur",
    "motion_blur",
    "zoom_blur",
    "snow",
    "frost",
    "fog",
    "brightness",
    "contrast",
    "elastic_transform",
    "pixelate",
    "jpeg_compression",
)


def parsed_cli_flags(tree: ast.AST) -> set[str]:
    flags: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Attribute) or node.func.attr != "add_argument":
            continue
        for arg in node.args:
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                flags.add(arg.value)
    return flags


def args_attributes(tree: ast.AST) -> set[str]:
    return {
        node.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Name)
        and node.value.id == "args"
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-dir", type=Path, required=True)
    parser.add_argument("--source-dir", type=Path, required=True)
    args = parser.parse_args()
    args.artifact_dir.mkdir(parents=True, exist_ok=True)

    source_dir = args.source_dir.resolve()
    runner = source_dir / "sudden_shift_experiment.py"
    readme = source_dir / "README.md"
    source_commit = (args.source_dir / "SOURCE_COMMIT").read_text().strip()
    runner_text = runner.read_text(encoding="utf-8")
    readme_text = readme.read_text(encoding="utf-8")
    tree = ast.parse(runner_text)
    flags = parsed_cli_flags(tree)
    attrs = args_attributes(tree)

    required_relative_paths = [
        "offline_imagenet/vitbase_timm/holdout_ents.npy",
        *[
            f"offline_imagenet/vitbase_timm/imagenet_c/s5_{name}_ents.npy"
            for name in CORRUPTIONS
        ],
    ]
    released_files = {
        path.relative_to(source_dir).as_posix()
        for path in source_dir.rglob("*")
        if path.is_file()
    }
    required_present = [
        path for path in required_relative_paths if (source_dir / path).exists()
    ]

    command = [
        sys.executable,
        str(runner),
        "--model",
        "vitbase_timm",
        "--corruptions",
        "gaussian_noise",
        "--level",
        "5",
        "--calibration-size",
        "500",
        "--alpha",
        "0.05",
        "--D",
        "0.5",
        "--C",
        "0.05",
        "--warmup",
        "50",
        "--seed",
        "0",
    ]
    completed = subprocess.run(
        command,
        cwd=source_dir,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    combined = completed.stdout + "\n" + completed.stderr
    gamma_failure = (
        completed.returncode != 0
        and "AttributeError" in combined
        and "gamma" in combined
    )
    control = {
        "name": "documented_cli_must_expose_release_defect",
        "command_redacted": (
            "python upstream/sudden_shift_experiment.py --model vitbase_timm "
            "--corruptions gaussian_noise --level 5 --calibration-size 500 "
            "--alpha 0.05 --D 0.5 --C 0.05 --warmup 50 --seed 0"
        ),
        "returncode": completed.returncode,
        "expected_failure": "args.gamma is referenced but --gamma is not declared",
        "gamma_attribute_error_detected": gamma_failure,
        "passed": gamma_failure,
    }
    (args.artifact_dir / "negative_control_output.json").write_text(
        json.dumps(control, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    checks = {
        "official_commit_pinned": source_commit
        == "a9feb795d9fa98cc1d0c075f8f08a5c510c7a844",
        "all_15_corruptions_declared": all(name in runner_text for name in CORRUPTIONS),
        "expected_layout_documented": "holdout_ents.npy" in readme_text
        and "s5_gaussian_noise_ents.npy" in readme_text,
        "no_required_arrays_released": not required_present,
        "no_npy_files_released": not any(path.endswith(".npy") for path in released_files),
        "runner_requires_gamma": "gamma" in attrs,
        "cli_omits_gamma": "--gamma" not in flags,
        "documented_cli_negative_control": gamma_failure,
    }
    passed = all(checks.values())
    result = {
        "claim_id": 6,
        "route": 1,
        "route_name": "official release and data-identity audit",
        "checks": checks,
        "required_paths": required_relative_paths,
        "required_paths_present": required_present,
        "released_file_count_in_vendored_snapshot": len(released_files),
        "cli_flags": sorted(flags),
        "args_attributes": sorted(attrs),
        "runtime_context": {
            "expected_core_count": 1,
            "selected_backend": "hf",
            "selected_flavor": "cpu-upgrade",
            "os_cpu_count": os.cpu_count(),
            "affinity_count": len(os.sched_getaffinity(0))
            if hasattr(os, "sched_getaffinity")
            else None,
        },
        "route_audit_passed": passed,
        "claim_verdict": "BLOCKED",
        "reason": (
            "The official release has neither required entropy arrays nor a "
            "working acquisition/runner path; numerical Figure 4 results "
            "cannot be regenerated from it."
        ),
    }
    (args.artifact_dir / "release_audit.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print("CLAIM6_RELEASE_AUDIT=" + json.dumps(result, sort_keys=True))
    print("CLAIM6_RELEASE_NEGATIVE_CONTROL=" + json.dumps(control, sort_keys=True))
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
