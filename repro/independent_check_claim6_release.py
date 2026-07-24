"""Independent, fail-closed checker for the Claim 6 release audit."""

from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-dir", type=Path, required=True)
    parser.add_argument("--source-dir", type=Path, required=True)
    args = parser.parse_args()

    audit = json.loads((args.artifact_dir / "release_audit.json").read_text())
    inventory = json.loads(
        (args.artifact_dir / "public_data_inventory.json").read_text()
    )
    control = json.loads(
        (args.artifact_dir / "negative_control_output.json").read_text()
    )
    runner_path = args.source_dir / "sudden_shift_experiment.py"
    tree = ast.parse(runner_path.read_text(encoding="utf-8"))

    gamma_loads = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Name)
        and node.value.id == "args"
        and node.attr == "gamma"
        and isinstance(node.ctx, ast.Load)
    ]
    gamma_declarations = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "add_argument"
        and any(
            isinstance(arg, ast.Constant) and arg.value == "--gamma"
            for arg in node.args
        )
    ]
    expected_paths = audit["required_paths"]
    checks = {
        "audit_route_is_nonclaiming": audit["claim_verdict"] == "BLOCKED",
        "required_input_count_is_16": len(expected_paths) == 16,
        "all_required_inputs_are_numpy": all(
            path.endswith(".npy") for path in expected_paths
        ),
        "none_of_required_inputs_present": not audit["required_paths_present"],
        "gamma_load_reconstructed": len(gamma_loads) >= 1,
        "gamma_parser_declaration_absent": not gamma_declarations,
        "negative_control_failed_for_expected_reason": control["passed"]
        and control["returncode"] != 0,
        "remote_tree_has_no_numpy": inventory["official_code"]["tree_npy_count"] == 0,
        "remote_tree_has_no_raw_results": inventory["official_code"][
            "tree_raw_result_count"
        ]
        == 0,
        "raw_reconstruction_sources_distinct": inventory[
            "public_corrupted_images"
        ]["revision"]
        != inventory["public_clean_images"]["revision"],
    }
    passed = all(checks.values())
    output = {
        "claim_id": 6,
        "route": 1,
        "independent": True,
        "imports_author_code": False,
        "checks": checks,
        "passed": passed,
        "claim_verdict": "BLOCKED",
    }
    (args.artifact_dir / "independent_release_audit.json").write_text(
        json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print("CLAIM6_INDEPENDENT_RELEASE_AUDIT=" + json.dumps(output, sort_keys=True))
    if not passed:
        sys.exit(1)


if __name__ == "__main__":
    main()
