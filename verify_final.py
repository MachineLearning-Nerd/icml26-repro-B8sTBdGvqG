#!/usr/bin/env python3
"""Verify the CCTM dossier and its live multi-branch GitHub state."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
REPOSITORY = "icml26-conditional-conformal-test-martingales"
CANONICAL = ("MachineLearning-Nerd", "MachineLearning-Nerd@users.noreply.github.com")
EXPECTED_BRANCHES = {
    "main",
    "baseline/validated-synthetic",
    "evidence/claim-2-counterexample",
    "audit/claim-3-imagenet-c",
    "counterexample/theorem-3-1",
    "fix/theorem-3-3-algebra",
    "proof/theorem-3-3",
    "release/claim-6-blocked",
    "evidence/claim-6-source-figure",
    "audit/claim-6-cpu-calibration",
    "audit/claim-6-pipeline-smoke",
    "experiment/claim-6-group-framework",
    "experiment/claim-6-noise-group",
    "experiment/claim-6-blur-group",
    "experiment/claim-6-weather-group",
    "experiment/claim-6-digital-group",
    "experiment/claim-6-gaussian-noise",
    "experiment/claim-6-shot-noise",
    "experiment/claim-6-impulse-noise",
    "experiment/claim-6-defocus-blur",
    "experiment/claim-6-glass-blur",
    "experiment/claim-6-motion-blur",
    "experiment/claim-6-zoom-blur",
    "experiment/claim-6-snow",
    "experiment/claim-6-frost",
    "experiment/claim-6-fog",
    "experiment/claim-6-brightness",
    "experiment/claim-6-contrast",
    "experiment/claim-6-elastic-transform",
    "experiment/claim-6-pixelate",
    "experiment/claim-6-jpeg-compression",
}
EXPECTED_STATUSES = {
    "C1": "VERIFIED_SCOPED",
    "C2": "FALSIFIED_AS_WRITTEN",
    "C3": "VERIFIED_PROOF_AUDIT",
    "C4": "VERIFIED_SCOPED",
    "C5": "VERIFIED_SCOPED",
    "C6": "BLOCKED",
}
REQUIRED_PATHS = [
    "README.md",
    "STATUS.md",
    "SOURCE_MANIFEST.md",
    "CLAIM_EVIDENCE.md",
    "ENVIRONMENT.md",
    "REPORT.md",
    "BRANCH_AUDIT.md",
    "CITATION.cff",
    "AUTHOR_THANK_YOU.md",
    "claims.json",
    "reproduction_verdicts.json",
    "AUTONOMOUS_STATE.json",
    "EVIDENCE_MANIFEST.json",
    "verify_final.py",
    "evidence/claim_summary.json",
    "evidence/synthetic/independent_verification.json",
    "evidence/claim_2/prior_run_verifier_output.json",
    "evidence/claim_3/verifier_output.json",
    "evidence/claim_6/final_blocked_verifier_output.json",
    "outputs/full_synthetic_summary.json",
    "outputs/independent_verification.json",
    "release_manifest.sha256",
    "upload_allowlist.txt",
]


def fail(message: str) -> None:
    print(f"FINAL_AUDIT=FAILED {message}", file=sys.stderr)
    raise SystemExit(1)


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def run(*args: str) -> str:
    result = subprocess.run(args, cwd=ROOT, check=False, capture_output=True, text=True)
    if result.returncode:
        fail(f"command failed: {' '.join(args)}\n{result.stderr.strip()}")
    return result.stdout.strip()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def current_json(path: str) -> object:
    try:
        return json.loads((ROOT / path).read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"invalid JSON in {path}: {exc}")


def verify_git() -> int:
    origin = run("git", "config", "--get", "remote.origin.url").removesuffix(".git")
    require(origin == f"https://github.com/MachineLearning-Nerd/{REPOSITORY}", f"unexpected origin: {origin}")
    require(run("git", "symbolic-ref", "--short", "HEAD") == "main", "current branch is not main")
    require(run("git", "symbolic-ref", "refs/remotes/origin/HEAD") == "refs/remotes/origin/main", "origin HEAD is not main")
    remote = {
        line.removeprefix("origin/")
        for line in run("git", "for-each-ref", "--format=%(refname:short)", "refs/remotes/origin").splitlines()
        if line.startswith("origin/") and line != "origin/HEAD"
    }
    require(remote == EXPECTED_BRANCHES, "remote branch set differs from branch audit")
    refs = run("git", "for-each-ref", "--format=%(refname)", "refs").splitlines()
    require(not any("orx/" in ref or "refs/original/" in ref or ref.endswith("/master") for ref in refs), "legacy refs remain")
    identities = {
        tuple(line.split("\t"))
        for line in run("git", "log", "--all", "--format=%an\t%ae\t%cn\t%ce").splitlines()
        if line.strip()
    }
    require(identities == {(CANONICAL[0], CANONICAL[1], CANONICAL[0], CANONICAL[1])}, f"non-canonical identity: {sorted(identities)}")
    require("co-authored-by:" not in run("git", "log", "--all", "--format=%B").lower(), "coauthor trailer remains")
    require(run("git", "status", "--porcelain") == "", "worktree is not clean")
    return len(remote)


def verify_artifacts() -> None:
    for path in REQUIRED_PATHS:
        require((ROOT / path).is_file(), f"required path missing: {path}")
    claims = current_json("claims.json")
    require(claims.get("repository") == f"MachineLearning-Nerd/{REPOSITORY}", "claims repository differs")
    require(claims.get("overall_verdict") == "MIXED_RESULTS_SCOPED_AUDIT", "claims overall verdict differs")
    require(claims.get("publication_allowed") is False, "claims publication gate changed")
    statuses = {row.get("id"): row.get("status") for row in claims.get("claims", [])}
    require(statuses == EXPECTED_STATUSES, f"claim statuses differ: {statuses}")
    summary = current_json("evidence/claim_summary.json")
    summary_statuses = {row.get("id"): row.get("status") for row in summary.get("claims", [])}
    require(summary_statuses == EXPECTED_STATUSES, "source claim summary differs")
    reproduction = current_json("reproduction_verdicts.json")
    require(reproduction.get("overall_verdict") == "MIXED_RESULTS_SCOPED_AUDIT" and reproduction.get("publication_allowed") is False, "reproduction verdict header differs")
    require({row.get("id"): row.get("status") for row in reproduction.get("claims", [])} == EXPECTED_STATUSES, "reproduction verdict statuses differ")
    state = current_json("AUTONOMOUS_STATE.json")
    require(state.get("phase") == "published_and_verified" and state.get("overall_verdict") == "MIXED_RESULTS_SCOPED_AUDIT", "state is not final")
    require(state.get("publication_allowed") is False and state.get("branch_count") == len(EXPECTED_BRANCHES), "state publication or branch count changed")
    source = (ROOT / "SOURCE_MANIFEST.md").read_text(encoding="utf-8")
    require("a9feb795d9fa98cc1d0c075f8f08a5c510c7a844" in source and "2602.13848" in source, "source pins changed")
    independent = current_json("outputs/independent_verification.json")
    require(
        all(value is True for value in independent.get("checks", {}).values())
        and independent.get("checks", {}).get("source_artifact_is_full") is True,
        "synthetic independent verification changed",
    )
    blocked = current_json("evidence/claim_6/final_blocked_verifier_output.json")
    require(blocked.get("verdict") == "BLOCKED" and blocked.get("passed") is True, "Claim 6 blocked gate changed")


def verify_manifest() -> None:
    manifest = current_json("EVIDENCE_MANIFEST.json")
    require(manifest.get("schema_version") == 1 and manifest.get("hash_algorithm") == "sha256", "manifest header changed")
    entries = manifest.get("files")
    require(isinstance(entries, dict) and entries, "evidence manifest is empty")
    for path, expected in entries.items():
        target = ROOT / path
        require(target.is_file(), f"manifest path missing: {path}")
        require(sha256(target) == expected, f"manifest hash mismatch: {path}")
    require("AUTONOMOUS_STATE.json" not in entries and "EVIDENCE_MANIFEST.json" not in entries, "manifest cycle detected")


def main() -> None:
    branches = verify_git()
    verify_artifacts()
    verify_manifest()
    commits = int(run("git", "rev-list", "--count", "--all"))
    require(commits >= 35, "reachable history is unexpectedly short")
    print(f"FINAL_AUDIT=VERIFIED branches={branches} commits={commits} C1:verified C2:falsified C3:proof_audit C4:verified C5:verified C6:blocked publication_allowed=false")


if __name__ == "__main__":
    main()
