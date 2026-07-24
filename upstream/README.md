# Conditional Conformal Test Martingales (CCTM)

Official code for the paper:

> **Testing For Distribution Shifts with Conditional Conformal Test Martingales**
> Shalev Shaer, Yarin Bar, Drew Prinster, Yaniv Romano.
> *Proceedings of the 43rd International Conference on Machine Learning (ICML), 2026.*
> 📄 arXiv: [https://arxiv.org/abs/2602.13848](https://arxiv.org/abs/2602.13848)

<p align="center">
  <img src="figs/power_three_panes.png" alt="Empirical power of standard CTM vs. our conditional CTM" width="85%">
</p>

## Overview

We propose a sequential test for detecting distribution shifts in a data stream relative
to a fixed reference dataset `D0`. Standard Conformal Test Martingales (CTMs) grow their reference set
with every incoming sample, which causes *test-time contamination*: after a shift, post-shift samples
dilute the evidence and slow detection.

Our **Conditional CTM** instead compares each new sample against a *fixed* null reference `D0`,
avoiding contamination by design. The key technical contribution is a robust betting function that
accounts for the estimation error of the empirical CDF of `D0` (via DKW confidence bands), yielding:

- anytime-valid type-I error control,
- guarantees of asymptotic power one, and
- bounded expected detection delay.

Empirically, the method detects shifts faster than standard CTMs and competitive baselines.

## Repository structure

| Path | Description |
| --- | --- |
| [`cond_ctm.py`](cond_ctm.py) | **Our method**: conditional CTM with ONS-optimized betting and DKW confidence bands. |
| [`conformal_test.py`](conformal_test.py) | Standard / "invalid" CTM baselines (online conformal p-values + martingale). |
| [`pairwise.py`](pairwise.py) | Pairwise-betting baseline (Saha & Ramdas, 2024) and AR(1) process simulators. |
| [`optimization.py`](optimization.py) | Online Newton Step (ONS) optimizer for the betting parameter. |
| [`utils.py`](utils.py) | Helpers: empirical CDF, DKW confidence bands, betting function. |
| [`experiments.py`](experiments.py) | Sweep functions that generate the synthetic-experiment figures. |
| [`synth_exps.ipynb`](synth_exps.ipynb) | Notebook reproducing all synthetic figures (Figs. 1, 2, 3, 5, 6). |
| [`sudden_shift_experiment.py`](sudden_shift_experiment.py) | CLI runner for sudden-shift ImageNet-C experiments. |
| [`continuous_shift_experiment.ipynb`](continuous_shift_experiment.ipynb) | ImageNet-C gradual-severity and cross-corruption experiments. |
| [`slurm_scripts/`](slurm_scripts/) | SLURM sweep scripts for the ImageNet-C experiments on an HPC cluster. |
| [`figs/`](figs/) | Output figures. |

## Installation

The code targets **Python 3.12**.

```bash
# Clone
git clone https://github.com/shaersh/cctm.git
cd cctm

# Create and activate a virtual environment
python -m venv .venv
# Linux / macOS
source .venv/bin/activate
# Windows (PowerShell)
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

## Synthetic experiments

All figures of the synthetic experiments are produced by [`synth_exps.ipynb`](synth_exps.ipynb).
Figures are written to [`figs/`](figs/).


## ImageNet-C experiments

These experiments monitor a test stream of **entropy scores** from a fixed pre-trained
ViT-Base (`vit_base_patch16_224`, from `timm`) on clean vs. corrupted ImageNet images.
Each seed uses a different hold-out out of the validation set of ImageNet.

### Expected data layout

```
offline_imagenet/
└── vitbase_timm/
    ├── holdout_ents.npy                          # clean-image entropies → calibration set D0
    └── imagenet_c/
        ├── s1_gaussian_noise_ents.npy            # severity 1..5 × 15 corruptions
        ├── s5_gaussian_noise_ents.npy
        └── ...                                    # 5 levels × 15 corruptions
```

The 15 corruption names are defined in `IMAGENET_C_CORRUPTIONS` in
[`sudden_shift_experiment.py`](sudden_shift_experiment.py): `gaussian_noise`, `shot_noise`,
`impulse_noise`, `defocus_blur`, `glass_blur`, `motion_blur`, `zoom_blur`, `snow`, `frost`, `fog`,
`brightness`, `contrast`, `elastic_transform`, `pixelate`, `jpeg_compression`.

### Sudden-shift experiment (CLI)

[`sudden_shift_experiment.py`](sudden_shift_experiment.py) runs one configuration and appends a row of
results to a CSV.

```bash
# Single corruption, severity 5
python sudden_shift_experiment.py \
    --model vitbase_timm \
    --corruptions gaussian_noise \
    --level 5 \
    --calibration-size 1000 \
    --alpha 0.05 \
    --D 0.5 --C 0.05 --warmup 10 \
    --seed 0 \
    --output exp_results/sudden_shift.csv

# All 15 corruptions at once
python sudden_shift_experiment.py \
    --model vitbase_timm \
    --corruptions all \
    --level 5 \
    --calibration-size 1000 \
    --seed 0
```

Main flags (see `--help` for the full list):

| Flag | Default | Meaning |
| --- | --- | --- |
| `--model` | `vitbase_timm` | Model identifier (selects the entropy directory). |
| `--corruptions` | `gaussian_noise` | One or more corruption names, or `all`. |
| `--level` | `5` | ImageNet-C severity level (1–5). |
| `--calibration-size` | `100` | Number of holdout entropies used as `D0`. |
| `--shift-delay` | `0` | In-distribution samples streamed before the shift. |
| `--alpha` | `0.05` | Test level. |
| `--D`, `--C` | `0.5`, `0.05` | ONS diameter and sparsification threshold. |
| `--warmup` | `10` | Warmup samples (state updates, no betting). |
| `--smooth-param` | `1e-6` | Betting-function smoothing. |
| `--seed` | `0` | RNG seed. |
| `--output` | `exp_results/sudden_shift.csv` | CSV log (appended). |

### Running sweeps on a cluster (SLURM)

[`slurm_scripts/run_sudden_shift_sweep.sh`](slurm_scripts/run_sudden_shift_sweep.sh) loops over models,
severity levels, calibration sizes, warmups, and seeds, submitting jobs through
[`slurm_scripts/sbatch_sudden_shift_wrapper.sh`](slurm_scripts/sbatch_sudden_shift_wrapper.sh).
Hyperparameters can be overridden via environment variables, e.g.:

```bash
N_SEEDS=10 ALPHA=0.05 D_VAL=0.5 C_VAL=0.05 \
    bash slurm_scripts/run_sudden_shift_sweep.sh
```

Adjust the cluster account/partition and resource settings in the wrapper script to match your
environment before running.

## Citation

If you use this code, please cite the paper:

```bibtex
@inproceedings{shaer2026cctm,
  title     = {Testing For Distribution Shifts with Conditional Conformal Test Martingales},
  author    = {Shaer, Shalev and Bar, Yarin and Prinster, Drew and Romano, Yaniv},
  booktitle = {Proceedings of the 43rd International Conference on Machine Learning (ICML)},
  year      = {2026},
  note      = {arXiv:2602.13848},
  url       = {https://arxiv.org/abs/2602.13848}
}
```
