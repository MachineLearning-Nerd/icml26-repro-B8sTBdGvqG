#!/usr/bin/env bash
set -euo pipefail

started_at="$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
started_seconds="${SECONDS}"

uv run pytest -q
uv run python repro/run_full_synthetic.py --output outputs/full_synthetic_summary.json
uv run python repro/verify_full_synthetic.py \
  --input outputs/full_synthetic_summary.json \
  --output outputs/independent_verification.json

mkdir -p .openresearch/artifacts/baseline
cp outputs/full_synthetic_summary.json .openresearch/artifacts/baseline/full_synthetic_summary.json
cp outputs/independent_verification.json .openresearch/artifacts/baseline/independent_verification.json

elapsed_seconds="$((SECONDS - started_seconds))"
uv run python repro/write_run_metadata.py \
  --output .openresearch/artifacts/baseline/run_metadata.json \
  --started-at "${started_at}" \
  --runtime-seconds "${elapsed_seconds}" \
  --expected-cores 4 \
  --selected-backend hf \
  --selected-flavor cpu-upgrade

printf 'BASELINE_VERDICT=VERIFIED\n'
printf 'BASELINE_RUNTIME_SECONDS=%s\n' "${elapsed_seconds}"
printf 'BASELINE_EXPECTED_CORES=4\n'
printf 'BASELINE_SELECTED_FLAVOR=cpu-upgrade\n'

claim2_started_seconds="${SECONDS}"
uv run python repro/run_claim2_counterexample.py \
  --output-dir .openresearch/artifacts/claim_2
uv run python repro/verify_claim2_counterexample.py \
  --artifact-dir .openresearch/artifacts/claim_2
uv run python repro/independent_check_claim2.py \
  --artifact-dir .openresearch/artifacts/claim_2
uv run python repro/verify_frozen_claim2.py \
  --artifact-dir .openresearch/artifacts/claim_2
printf 'CLAIM2_TRAJECTORY_CSV_BEGIN\n'
cat .openresearch/artifacts/claim_2/trajectory.csv
printf 'CLAIM2_TRAJECTORY_CSV_END\n'
claim2_elapsed_seconds="$((SECONDS - claim2_started_seconds))"
uv run python repro/write_run_metadata.py \
  --output .openresearch/artifacts/claim_2/run_metadata.json \
  --started-at "${started_at}" \
  --runtime-seconds "${claim2_elapsed_seconds}" \
  --expected-cores 4 \
  --selected-backend hf \
  --selected-flavor cpu-upgrade

printf 'CLAIM2_RUN_METADATA='
tr -d '\n' < .openresearch/artifacts/claim_2/run_metadata.json
printf '\n'
printf 'CLAIM2_VERDICT=FALSIFIED\n'
printf 'CLAIM2_RUNTIME_SECONDS=%s\n' "${claim2_elapsed_seconds}"

claim3_started_seconds="${SECONDS}"
mkdir -p .openresearch/artifacts/claim_3
uv run python repro/verify_claim3_proof.py \
  --artifact-dir .openresearch/artifacts/claim_3
uv run python repro/independent_check_claim3.py \
  --artifact-dir .openresearch/artifacts/claim_3
uv run python repro/verify_claim3_contract.py \
  --artifact-dir .openresearch/artifacts/claim_3
uv run python repro/verify_frozen_claim3.py \
  --artifact-dir .openresearch/artifacts/claim_3
claim3_elapsed_seconds="$((SECONDS - claim3_started_seconds))"
uv run python repro/write_run_metadata.py \
  --output .openresearch/artifacts/claim_3/run_metadata.json \
  --started-at "${started_at}" \
  --runtime-seconds "${claim3_elapsed_seconds}" \
  --expected-cores 4 \
  --selected-backend hf \
  --selected-flavor cpu-upgrade
printf 'CLAIM3_RUN_METADATA='
tr -d '\n' < .openresearch/artifacts/claim_3/run_metadata.json
printf '\n'
printf 'CLAIM3_VERDICT=VERIFIED\n'
printf 'CLAIM3_RUNTIME_SECONDS=%s\n' "${claim3_elapsed_seconds}"

claim6_route1_started_seconds="${SECONDS}"
mkdir -p .openresearch/artifacts/claim_6
uv run python repro/audit_claim6_release.py \
  --artifact-dir .openresearch/artifacts/claim_6 \
  --source-dir upstream
uv run python repro/independent_check_claim6_release.py \
  --artifact-dir .openresearch/artifacts/claim_6 \
  --source-dir upstream
claim6_route1_elapsed_seconds="$((SECONDS - claim6_route1_started_seconds))"
uv run python repro/write_run_metadata.py \
  --output .openresearch/artifacts/claim_6/route1_run_metadata.json \
  --started-at "${started_at}" \
  --runtime-seconds "${claim6_route1_elapsed_seconds}" \
  --expected-cores 1 \
  --selected-backend hf \
  --selected-flavor cpu-upgrade
printf 'CLAIM6_ROUTE1_RUN_METADATA='
tr -d '\n' < .openresearch/artifacts/claim_6/route1_run_metadata.json
printf '\n'
printf 'CLAIM6_ROUTE1_AUDIT=PASSED\n'
printf 'CLAIM6_CURRENT_VERDICT=BLOCKED\n'
printf 'CLAIM6_ROUTE1_RUNTIME_SECONDS=%s\n' "${claim6_route1_elapsed_seconds}"

claim6_route2_started_seconds="${SECONDS}"
uv run python repro/digitize_claim6_figure.py \
  --artifact-dir .openresearch/artifacts/claim_6
uv run python repro/independent_check_claim6_figure.py \
  --artifact-dir .openresearch/artifacts/claim_6
uv run python repro/verify_claim6_route2.py \
  --artifact-dir .openresearch/artifacts/claim_6
uv run python repro/check_claim6_route2_fail_closed.py \
  --artifact-dir .openresearch/artifacts/claim_6
printf 'CLAIM6_ROUTE2_POWER_CSV_BEGIN\n'
cat .openresearch/artifacts/claim_6/route2_power_crossings.csv
printf 'CLAIM6_ROUTE2_POWER_CSV_END\n'
printf 'CLAIM6_ROUTE2_RATIO_CSV_BEGIN\n'
cat .openresearch/artifacts/claim_6/route2_ratio_points.csv
printf 'CLAIM6_ROUTE2_RATIO_CSV_END\n'
claim6_route2_elapsed_seconds="$((SECONDS - claim6_route2_started_seconds))"
uv run python repro/write_run_metadata.py \
  --output .openresearch/artifacts/claim_6/route2_run_metadata.json \
  --started-at "${started_at}" \
  --runtime-seconds "${claim6_route2_elapsed_seconds}" \
  --expected-cores 1 \
  --selected-backend hf \
  --selected-flavor cpu-upgrade
printf 'CLAIM6_ROUTE2_RUN_METADATA='
tr -d '\n' < .openresearch/artifacts/claim_6/route2_run_metadata.json
printf '\n'
printf 'CLAIM6_ROUTE2_AUDIT=PASSED\n'
printf 'CLAIM6_CURRENT_VERDICT=BLOCKED\n'
printf 'CLAIM6_ROUTE2_RUNTIME_SECONDS=%s\n' "${claim6_route2_elapsed_seconds}"

claim6_route3_profile_started_seconds="${SECONDS}"
uv run python repro/profile_claim6_cpu.py \
  --artifact-dir .openresearch/artifacts/claim_6
uv run python repro/independent_check_claim6_cpu_profile.py \
  --artifact-dir .openresearch/artifacts/claim_6
uv run python repro/verify_claim6_cpu_profile.py \
  --artifact-dir .openresearch/artifacts/claim_6
uv run python repro/check_claim6_profile_fail_closed.py \
  --artifact-dir .openresearch/artifacts/claim_6
claim6_route3_profile_elapsed_seconds="$((SECONDS - claim6_route3_profile_started_seconds))"
uv run python repro/write_run_metadata.py \
  --output .openresearch/artifacts/claim_6/route3_profile_run_metadata.json \
  --started-at "${started_at}" \
  --runtime-seconds "${claim6_route3_profile_elapsed_seconds}" \
  --expected-cores 64 \
  --selected-backend hf \
  --selected-flavor cpu-upgrade
printf 'CLAIM6_ROUTE3_PROFILE_RUN_METADATA='
tr -d '\n' < .openresearch/artifacts/claim_6/route3_profile_run_metadata.json
printf '\n'
printf 'CLAIM6_ROUTE3_PROFILE=PASSED\n'
printf 'CLAIM6_CURRENT_VERDICT=BLOCKED\n'
printf 'CLAIM6_ROUTE3_PROFILE_RUNTIME_SECONDS=%s\n' "${claim6_route3_profile_elapsed_seconds}"
