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
