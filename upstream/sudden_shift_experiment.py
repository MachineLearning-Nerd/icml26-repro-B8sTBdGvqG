# %%
"""Single sudden shift experiment runner with CSV logging."""

import argparse
import json
import random
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple
import uuid

import numpy as np
import pandas as pd
from loguru import logger

from conformal_test import ConformalTest
from cond_ctm import CondCTM

IMAGENET_C_CORRUPTIONS: Tuple[str, ...] = (
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


# %%
@dataclass
class ExperimentConfig:
    model: str
    corruptions: Tuple[str, ...]
    level: int
    calibration_size: int
    shift_delay: int
    alpha: float
    D: float
    C: float
    warmup: int
    gamma: float
    smooth_param: float
    seed: int
    output: Path


@dataclass
class ExperimentArtifacts:
    calibration_ents_path: str
    severity_ents_path: str
    n_total_holdout: int
    n_total_severity: int
    in_dist_length: int
    total_test_length: int


@dataclass
class ExperimentResults:
    cond_ctm_results: Dict[str, Any]
    conformal_results: Dict[str, Any]
    timestamp: str
    config: ExperimentConfig
    artifacts: ExperimentArtifacts
    corruption: str


def resolve_corruptions(selections: Sequence[str]) -> Tuple[str, ...]:
    print(selections)
    if not selections:
        raise ValueError("At least one corruption must be specified")

    expanded: List[str] = []
    for name in selections:
        if name.lower() == "all":
            expanded.extend(IMAGENET_C_CORRUPTIONS)
        else:
            expanded.append(name)

    resolved: List[str] = []
    seen = set()
    for name in expanded:
        if name not in IMAGENET_C_CORRUPTIONS:
            raise ValueError(f"Unknown corruption '{name}'. Expected one of: {', '.join(IMAGENET_C_CORRUPTIONS)}")
        if name not in seen:
            resolved.append(name)
            seen.add(name)

    return tuple(resolved)


# %%
def parse_args() -> ExperimentConfig:
    parser = argparse.ArgumentParser(
        description=(
            "Run a single sudden-shift ImageNet experiment and append the results to a CSV."
        )
    )
    parser.add_argument("--model", default="vitbase_timm", help="Model identifier used for loading entropy files")
    parser.add_argument("--corruption", default="gaussian_noise", help="Corruption name inside imagenet_c directory (deprecated, use --corruptions)")
    parser.add_argument(
        "--corruptions",
        nargs="+",
        help="Space-separated list of corruptions to evaluate (use 'all' for every ImageNet-C corruption)",
    )
    parser.add_argument("--level", type=int, default=5, help="Severity level (1-5) for imagenet_c entropies")
    parser.add_argument("--calibration-size", type=int, default=100, help="Number of calibration entropies")
    parser.add_argument("--shift-delay", type=int, default=0, help="Number of in-distribution samples before shift")
    parser.add_argument("--alpha", type=float, default=0.05, help="Significance level")
    parser.add_argument("--D", type=float, default=0.5, help="ONS diameter parameter")
    parser.add_argument("--C", type=float, default=0.05, help="ONS sparsification threshold")
    parser.add_argument("--warmup", type=int, default=10, help="Number of warmup samples (no martingale updates)")
    parser.add_argument("--smooth-param", type=float, default=1e-6, help="Smoothing parameter for betting function")
    parser.add_argument("--seed", type=int, default=0, help="Seed controlling every shuffle in the experiment")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("exp_results") / "sudden_shift.csv",
        help="CSV file used for logging (appends when file exists)",
    )

    args = parser.parse_args()

    corruption_inputs = args.corruptions if args.corruptions else [args.corruption]
    resolved_corruptions = resolve_corruptions(corruption_inputs)

    logger.info(
        "Parsed arguments: model={}, corruptions={}, level={}, calibration_size={}, shift_delay={}, alpha={}, D={}, C={}, warmup={}, gamma={}, smooth_param={}, seed={}, output={}",
        args.model,
        list(resolved_corruptions),
        args.level,
        args.calibration_size,
        args.shift_delay,
        args.alpha,
        args.D,
        args.C,
        args.warmup,
        args.gamma,
        args.smooth_param,
        args.seed,
        args.output,
    )
    return ExperimentConfig(
        model=args.model,
        corruptions=resolved_corruptions,
        level=args.level,
        calibration_size=args.calibration_size,
        shift_delay=args.shift_delay,
        alpha=args.alpha,
        D=args.D,
        C=args.C,
        warmup=args.warmup,
        gamma=args.gamma,
        smooth_param=args.smooth_param,
        seed=args.seed,
        output=args.output,
    )


# %%
def seed_everything(seed: int) -> np.random.Generator:
    np.random.seed(seed)
    random.seed(seed)
    logger.debug("Seeding all RNGs with seed={}", seed)
    try:
        import torch
        import uuid

        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
            logger.debug("CUDA available; seeded all CUDA devices")
    except Exception:
        logger.debug("Torch not available for seeding or an exception occurred; continuing without torch seed")
    return np.random.default_rng(seed)


# %%
def load_and_shuffle_entropies(
    config: ExperimentConfig, rng: np.random.Generator, corruption: str
) -> Tuple[np.ndarray, np.ndarray]:
    holdout_path = Path("offline_imagenet") / config.model / "holdout_ents.npy"
    severity_path = (
        Path("offline_imagenet")
        / config.model
        / "imagenet_c"
        / f"s{config.level}_{corruption}_ents.npy"
    )

    if not holdout_path.exists():
        logger.error("Holdout entropy file missing: {}", holdout_path)
        raise FileNotFoundError(f"Missing holdout entropies at {holdout_path}")
    if not severity_path.exists():
        logger.error("Severity entropy file missing: {}", severity_path)
        raise FileNotFoundError(f"Missing severity entropies at {severity_path}")

    holdout_ents = np.load(holdout_path).astype(np.float64)
    severity_ents = np.load(severity_path).astype(np.float64)

    rng.shuffle(holdout_ents)
    rng.shuffle(severity_ents)

    logger.info(
        "Loaded entropies: corruption={}, holdout_count={}, severity_count={}",
        corruption,
        len(holdout_ents),
        len(severity_ents),
    )

    if config.calibration_size > len(holdout_ents):
        logger.error("Calibration size {} exceeds holdout set size {}", config.calibration_size, len(holdout_ents))
        raise ValueError(
            f"Calibration size {config.calibration_size} exceeds holdout set ({len(holdout_ents)})"
        )

    return holdout_ents, severity_ents


# %%
def run_conformal(
    config: ExperimentConfig,
    calibration_ents: np.ndarray,
    in_dist: np.ndarray,
    severity_ents: np.ndarray,
) -> Dict[str, Any]:
    logger.info("Running conformal test: calibration_size={}, in_dist_length={}, severity_length={}",
                len(calibration_ents), len(in_dist), len(severity_ents))
    conformal = ConformalTest(alpha=config.alpha, D=config.D)
    full_sequence = np.concatenate((calibration_ents, in_dist, severity_ents))

    first_crossing, martingales = conformal.test_exchangeability(
        full_sequence,
        C=config.C,
        cal_set_size=config.calibration_size,
        warmup_samples=config.warmup,
    )
    # Skip calibration portion entirely (align with notebook behavior)
    post_cal_martingales = martingales[config.calibration_size:]
    post_cal_ut = conformal.p_values[config.calibration_size:]
    # Adjust first crossing index to be relative to post-calibration sequence
    adj_first_crossing = (
        -1 if first_crossing == -1 else max(0, first_crossing - config.calibration_size)
    )

    if adj_first_crossing != -1:
        logger.info("Conformal martingale crossed threshold at post-cal index {} (raw index {})", adj_first_crossing, first_crossing)
    else:
        logger.info("Conformal martingale never crossed threshold (length={})", len(post_cal_martingales))

    return {
        "martingales": post_cal_martingales.tolist(),
        "ut": post_cal_ut.tolist(),
        "first_crossing_index": int(adj_first_crossing),
        "threshold": float(1.0 / config.alpha),
    }


# %%
def run_cond_ctm(
    config: ExperimentConfig,
    calibration_ents: np.ndarray,
    in_dist: np.ndarray,
    severity_ents: np.ndarray,
) -> Dict[str, Any]:
    logger.info("Running CondCTM method: calibration_size={}, in_dist_length={}, severity_length={}",
                len(calibration_ents), len(in_dist), len(severity_ents))
    cond_ctm = CondCTM(
        config.alpha,
        calibration_ents,
        smooth_param=config.smooth_param,
        D=config.D,
        C=config.C,
    )

    martingales = []
    martingale_value = 1.0
    all_ents = np.concatenate((in_dist, severity_ents))
    total_len = len(all_ents)
    progress_log_interval = max(1, total_len // 10)  # 10% steps
    first_crossing = -1
    threshold = 1.0 / config.alpha

    for idx, ent in enumerate(all_ents):
        bet_res, _ = cond_ctm.step(float(ent))

        if idx <= config.warmup:
            martingales.append(martingale_value)
            continue

        martingale_value = min(martingale_value * bet_res, 1e250)
        martingales.append(martingale_value)

        if first_crossing == -1 and martingale_value >= threshold:
            first_crossing = idx

        if idx % progress_log_interval == 0 and idx > 0:
            logger.debug("CondCTM progress: idx={}, martingale_value={:.3e}", idx, martingale_value)

    if first_crossing != -1:
        logger.info("CondCTM martingale crossed threshold at index {}", first_crossing)
    else:
        logger.info("CondCTM martingale never crossed threshold (length={})", len(martingales))

    logger.info("Completed CondCTM method run: final_martingale={:.3e}", martingale_value)

    return {
        "martingales": martingales,
        "ut": cond_ctm.p_values,
        "first_crossing_index": int(first_crossing),
        "threshold": float(threshold),
    }


# %%
def build_record_row(record: ExperimentResults) -> Dict[str, Any]:

    def subsample_metrics(
        martingales: Sequence[float],
        ut: Sequence[float],
        threshold: float = 100.0,
        stride: int = 100,
    ) -> Tuple[List[float], List[float]]:
        max_len = min(len(martingales), len(ut))
        if max_len == 0:
            return [], []

        sub_mart: List[float] = []
        sub_ut: List[float] = []
        cross_idx: Optional[int] = None

        for idx in range(max_len):
            value = martingales[idx]
            include_point = cross_idx is None or (idx - cross_idx) % stride == 0
            if include_point:
                sub_mart.append(value)
                sub_ut.append(ut[idx])

            if cross_idx is None and value > threshold:
                cross_idx = idx

        return sub_mart, sub_ut

    # Extract and subsample martingales/p-values with threshold-aware strategy
    cond_ctm_martingales = record.cond_ctm_results.get("martingales", [])
    cond_ctm_ut = record.cond_ctm_results.get("ut", [])
    conformal_martingales = record.conformal_results.get("martingales", [])
    conformal_ut = record.conformal_results.get("ut", [])

    # Subsample according to threshold/stride rule
    cond_ctm_martingales_sub, cond_ctm_ut_sub = subsample_metrics(cond_ctm_martingales, cond_ctm_ut)
    conformal_martingales_sub, conformal_ut_sub = subsample_metrics(conformal_martingales, conformal_ut)

    row: Dict[str, Any] = {
        "timestamp": record.timestamp,
        "seed": record.config.seed,
        "model": record.config.model,
        "corruption": record.corruption,
        "level": record.config.level,
        "calibration_size": record.config.calibration_size,
        "shift_delay": record.config.shift_delay,
        "alpha": record.config.alpha,
        "D": record.config.D,
        "C": record.config.C,
        "warmup": record.config.warmup,
        "gamma": record.config.gamma,
        "smooth_param": record.config.smooth_param,
        "in_dist_length": record.artifacts.in_dist_length,
        "total_test_length": record.artifacts.total_test_length,
        "n_total_holdout": record.artifacts.n_total_holdout,
        "n_total_severity": record.artifacts.n_total_severity,
        "calibration_ents_path": record.artifacts.calibration_ents_path,
        "severity_ents_path": record.artifacts.severity_ents_path,
        "cond_ctm_martingales": json.dumps(cond_ctm_martingales_sub),
        "cond_ctm_ut": json.dumps(cond_ctm_ut_sub),
        "cond_ctm_first_crossing": record.cond_ctm_results.get("first_crossing_index", -1),
        "cond_ctm_threshold": record.cond_ctm_results.get("threshold", 0.0),
        "conformal_martingales": json.dumps(conformal_martingales_sub),
        "conformal_ut": json.dumps(conformal_ut_sub),
        "conformal_first_crossing": record.conformal_results.get("first_crossing_index", -1),
        "conformal_threshold": record.conformal_results.get("threshold", 0.0),
    }

    return row


# %%
def run_single_experiment(config: ExperimentConfig, corruption: str) -> ExperimentResults:
    logger.info("Starting single experiment run (seed={}, corruption={})", config.seed, corruption)
    rng = seed_everything(config.seed)
    holdout_ents, severity_ents = load_and_shuffle_entropies(config, rng, corruption)

    calibration_ents = holdout_ents[: config.calibration_size]
    rest_of_holdout = holdout_ents[config.calibration_size :]

    if config.shift_delay > len(rest_of_holdout):
        logger.error("Shift delay {} exceeds available post-calibration holdout size {}", config.shift_delay, len(rest_of_holdout))
        raise ValueError(
            f"Shift delay {config.shift_delay} exceeds available post-calibration holdout entropies ({len(rest_of_holdout)})."
        )

    in_dist = rest_of_holdout[: config.shift_delay]
    logger.debug("Prepared in-distribution segment length={}", len(in_dist))

    conformal_results = run_conformal(config, calibration_ents, in_dist, severity_ents)
    cond_ctm_results = run_cond_ctm(config, calibration_ents, in_dist, severity_ents)

    artifacts = ExperimentArtifacts(
        calibration_ents_path=str(Path("offline_imagenet") / config.model / "holdout_ents.npy"),
        severity_ents_path=str(
            Path("offline_imagenet") / config.model / "imagenet_c" / f"s{config.level}_{corruption}_ents.npy"
        ),
        n_total_holdout=int(len(holdout_ents)),
        n_total_severity=int(len(severity_ents)),
        in_dist_length=int(len(in_dist)),
        total_test_length=int(len(in_dist) + len(severity_ents)),
    )

    timestamp = datetime.now(timezone.utc).isoformat()

    return ExperimentResults(
        cond_ctm_results=cond_ctm_results,
        conformal_results=conformal_results,
        timestamp=timestamp,
        config=config,
        artifacts=artifacts,
        corruption=corruption,
    )


# %%
def main() -> None:
    # Basic logger setup (can be extended to file sinks if needed)
    logger.remove()
    logger.add(sys.stderr, level="INFO", format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | {message}")
    config = parse_args()
    try:
        rows: List[Dict[str, Any]] = []
        for corruption in config.corruptions:
            logger.info("Processing corruption '{}'", corruption)
            record = run_single_experiment(config, corruption)
            row = build_record_row(record)
            rows.append(row)
            logger.success(
                "Finished experiment run: corruption={}, timestamp={}, seed={}, total_test_length={}",
                corruption,
                record.timestamp,
                record.config.seed,
                record.artifacts.total_test_length,
            )

        # Once all corruptions are processed, write a single CSV per run
        unique_id = str(uuid.uuid4()).replace("-", "")[:16]
        filename = f"{config.seed}_{unique_id}.csv"
        output_path = config.output.parent / filename
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df = pd.DataFrame(rows)
        df.to_csv(output_path, mode="w", header=True, index=False)
        logger.success("Wrote per-run combined results CSV: {} (rows={})", output_path, len(rows))
        print(
            "Saved combined experiment runs",
            {
                "seed": config.seed,
                "corruptions": [row["corruption"] for row in rows],
                "output": str(output_path),
                "num_rows": len(rows),
            },
        )
    except Exception as e:
        logger.exception("Experiment failed with an exception")
        raise e


# %%
if __name__ == "__main__":
    main()
