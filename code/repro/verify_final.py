"""Fail-closed package verifier for the final repository surface."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EXPECTED_STATUSES = {
    "C1": "VERIFIED_SCOPED",
    "C2": "FALSIFIED_AS_WRITTEN",
    "C3": "VERIFIED_PROOF_AUDIT",
    "C4": "VERIFIED_SCOPED",
    "C5": "VERIFIED_SCOPED",
    "C6": "BLOCKED",
}


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def main() -> int:
    errors: list[str] = []

    required = [
        "README.md",
        "STATUS.md",
        "BRANCH_AUDIT.md",
        "CLAIM_EVIDENCE.md",
        "SOURCE_MANIFEST.md",
        "CITATION.cff",
        "evidence/claim_summary.json",
        "evidence/synthetic/full_synthetic_summary.json",
        "evidence/synthetic/independent_verification.json",
        "evidence/claim_2/prior_run_raw_results.json",
        "evidence/claim_2/prior_run_independent_checker_output.json",
        "evidence/claim_3/proof_certificate.json",
        "evidence/claim_3/independent_checker_output.json",
        "evidence/claim_6/final_blocked_verifier_output.json",
        "code/pyproject.toml",
        "logbook.json",
    ]
    for relative in required:
        if not (ROOT / relative).is_file():
            errors.append(f"missing required file: {relative}")

    summary = json.loads((ROOT / "evidence/claim_summary.json").read_text())
    statuses = {claim["id"]: claim["status"] for claim in summary["claims"]}
    if statuses != EXPECTED_STATUSES:
        errors.append(f"claim statuses differ: {statuses}")
    if summary["repository"]["final_name"] != "icml26-conditional-conformal-test-martingales":
        errors.append("final repository name is not recorded consistently")
    if summary["repository"]["owner"] != "MachineLearning-Nerd":
        errors.append("repository owner is not MachineLearning-Nerd")

    readme = (ROOT / "README.md").read_text()
    for phrase in (
        "icml26-conditional-conformal-test-martingales",
        "CLAIM_EVIDENCE.md",
        "BRANCH_AUDIT.md",
        "SOURCE_MANIFEST.md",
        "CITATION.cff",
        "Thank you to Shalev Shaer",
        "FALSIFIED_AS_WRITTEN",
        "ImageNet-C",
    ):
        if phrase not in readme:
            errors.append(f"README missing required phrase: {phrase}")

    branch_lines = [
        line
        for line in (ROOT / "BRANCH_AUDIT.md").read_text().splitlines()
        if line.startswith("| `")
    ]
    if len(branch_lines) != 31:
        errors.append(f"branch audit contains {len(branch_lines)} rows, expected 31")

    synthetic = json.loads(
        (ROOT / "evidence/synthetic/independent_verification.json").read_text()
    )
    headline = synthetic["headline"]
    primary = headline["primary"]
    if not (
        synthetic["checks"]
        and all(synthetic["checks"].values())
        and primary["conditional_median_delay"] == 21.0
        and primary["standard_median_delay"] == 31.0
        and headline["max_conditional_type1_rate"] <= 0.01
        and headline["max_naive_type1_rate"] >= 0.88
    ):
        errors.append("synthetic independent verification does not pass its headline checks")

    claim2 = json.loads(
        (ROOT / "evidence/claim_2/prior_run_independent_checker_output.json").read_text()
    )
    if not (
        claim2["passed"]
        and claim2["verdict"] == "FALSIFIED"
        and claim2["checks"]["finite_witness_contradicts_inner_bound"]
        and claim2["checks"]["deterministic_reference_contradicts_outer_bound"]
    ):
        errors.append("Claim 2 independent counterexample check does not pass")

    claim3 = json.loads(
        (ROOT / "evidence/claim_3/independent_checker_output.json").read_text()
    )
    if not (
        claim3["passed"]
        and claim3["verdict"] == "VERIFIED"
        and claim3["rational_grid_checks"] == 952
        and claim3["burn_in_checks"] == 25
    ):
        errors.append("Claim 3 independent proof audit does not pass")

    claim6 = json.loads(
        (ROOT / "evidence/claim_6/final_blocked_verifier_output.json").read_text()
    )
    if not claim6["passed"] or claim6["verdict"] != "BLOCKED":
        errors.append("Claim 6 final blocked verifier does not pass")

    logbook = json.loads((ROOT / "logbook.json").read_text())
    for child in logbook["root"].get("children", []):
        if not (ROOT / child["file"]).is_file():
            errors.append(f"logbook path is missing: {child['file']}")

    tracked = git("ls-files").splitlines()
    forbidden_tracked = [
        path
        for path in tracked
        if ".trackio/" in path
        or path == ".serve.log"
        or path.endswith("/.serve.log")
        or path.endswith("/.env")
    ]
    if forbidden_tracked:
        errors.append(f"generated/private files are tracked: {forbidden_tracked}")

    package = (ROOT / "code/pyproject.toml").read_text()
    if 'name = "icml26-conditional-conformal-test-martingales"' not in package:
        errors.append("code package name is stale")

    refs = git("for-each-ref", "--format=%(refname)", "refs/remotes/origin").splitlines()
    remote_branches = sorted(
        ref.removeprefix("refs/remotes/origin/")
        for ref in refs
        if ref.startswith("refs/remotes/origin/") and ref != "refs/remotes/origin/HEAD"
    )
    if remote_branches and len(remote_branches) != 31:
        errors.append(f"final remote branch count is {len(remote_branches)}, expected 31")
    if any(branch.startswith("orx/") or branch == "master" for branch in remote_branches):
        errors.append("old orx/master branch remains in the remote refs")

    identities = set(git("log", "--all", "--format=%an <%ae>").splitlines())
    expected_identity = "MachineLearning-Nerd <MachineLearning-Nerd@users.noreply.github.com>"
    if identities and identities != {expected_identity}:
        errors.append(f"reachable commit identities are not canonical: {sorted(identities)}")

    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1

    print("PASS: scoped claims, source evidence, documentation, branch map, and cleanup invariants")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
