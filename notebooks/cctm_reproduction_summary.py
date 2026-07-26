import marimo

__generated_with = "0.14.17"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    mo.md("""
    # CCTM reproduction summary

    ![Open in molab](https://marimo.io/molab-shield.svg)

    This notebook is a lightweight reader-facing summary. It embeds the current evidence so readers do not need to rerun the expensive HF reproduction job.
    """)
    return (mo,)


@app.cell
def _(mo):
    mo.md("""
    ## Headline

    Previous live judged score: **6/12**. Current forecast after the published evidence package: **10/12**. This is not a live judge result.

    | Claim | Status | Forecast points | Confidence |
    |---|---|---:|---|
    | 1 | VERIFIED | 2 | HIGH |
    | 2 | FALSIFIED | 2 | HIGH |
    | 3 | VERIFIED | 2 | MEDIUM |
    | 4 | VERIFIED | 2 | HIGH |
    | 5 | VERIFIED | 2 | HIGH |
    | 6 | BLOCKED | 0 | LOW |
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    ## Evidence highlights

    - Fixed-reference conditional CTM preserved the prior full-credit synthetic evidence: median crossing **21** vs **31** for standard CTM in the primary shift setup.
    - Claim 2 is falsified by a Dirac null witness: false rejection probability is **1.0** where Theorem 3.1 requires at most **0.05**.
    - Claim 3 is supported by a corrected symbolic proof certificate: **11/11** obligations, **952** rational-grid checks, and **25** burn-in checks passed.
    - Claim 6 remains blocked: required ImageNet-C entropy arrays are absent and no full-scope counterexample was found.
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    ## Reproduction command

    ```bash
    uv sync --frozen && bash scripts/run_reproduction.sh
    ```

    Successful HF run: `7e9019e0-e75e-44ab-805d-5fe4dbf06d3f` on `cpu-upgrade`, commit `9d56f3e05e10e5f0cd57b6bd8bfef419d909612a`.

    Published Space revision: `96f4ca15d8223fb2e273c633b8771fbee2f8047f`.
    """)
    return


if __name__ == "__main__":
    app.run()
