# Branch audit and rename map

This table is the branch-level audit for the original public repository. The
tip hashes below are the original remote tips before the final documentation
commit and canonical attribution rewrite; the commit IDs necessarily change
when the reachable history is rewritten to
`MachineLearning-Nerd <MachineLearning-Nerd@users.noreply.github.com>`.

The final remote is intended to contain exactly `main` plus the purpose-based
branches in the **Final branch** column. No `master` or `orx/*` branch is kept.
Branches are retained individually because each one records a distinct audit
route, shard, control, or release state; they are not silently merged into
`main`.

| Original branch | Original tip | Final branch | Purpose |
|---|---|---|---|
| `main` | `c5e890c007b2f84c4a58ee96d3b96e7ce3ca55dc` | `main` | Reader-facing publication surface and cumulative current evidence |
| `orx/validated-synthetic-baseline` | `3cefe11a1fc7c6902c7ef967c939d2ff0f6670ee` | `baseline/validated-synthetic` | Self-contained full synthetic baseline and independent aggregation |
| `orx/claim-2-evaluator-visible-evidence-freeze` | `f1afbd3efaaa994d632ea3b380141c861904fef2` | `evidence/claim-2-counterexample` | Evaluator-visible Claim 2 falsification artifact freeze |
| `orx/claim-3-evidence-freeze-and-imagenet-c-data-audi` | `ec4e230c826ea26e0bcd98d18d9c1f1590a7224c` | `audit/claim-3-imagenet-c` | Claim 3 evidence freeze and ImageNet-C source/data audit |
| `orx/theorem-3-1-discrete-null-counterexample` | `491e1fe27e4bd6785bd621b0a94d9069c6bcf1c8` | `counterexample/theorem-3-1` | Dirac-null counterexample to the printed universal theorem |
| `orx/theorem-3-3-algebraic-equality-fix` | `a693f6e7060b4241fb6defcb37229d3efbcf07ee` | `fix/theorem-3-3-algebra` | Algebraic comparison and correction of the printed proof |
| `orx/theorem-3-3-corrected-proof-certificate` | `291bae16a3e14f471851160c2d06769426aa4721` | `proof/theorem-3-3` | Corrected proof certificate and symbolic obligations for Theorem 3.3 |
| `orx/release-prep-with-claim-6-blocked-record` | `9d56f3e05e10e5f0cd57b6bd8bfef419d909612a` | `release/claim-6-blocked` | Cumulative release candidate with Claim 6's four blocked routes |
| `orx/claim-6-source-figure-digitization` | `4f27ad8210ef189a03edd5dc96f97390d33cad33` | `evidence/claim-6-source-figure` | Non-claiming digitization and independent arithmetic check of Figure 4 |
| `orx/claim-6-full-reconstruction-cpu-calibration` | `26c20c77ebc3b00b10fb9e1396620247fdd1231b` | `audit/claim-6-cpu-calibration` | CPU throughput and reconstruction calibration |
| `orx/claim-6-full-pipeline-smoke-validation` | `02fdb451be7ef62aa1a2c5e53898e471211bd02f` | `audit/claim-6-pipeline-smoke` | Small pipeline smoke validation, explicitly not full benchmark evidence |
| `orx/claim-6-full-group-framework` | `15334dce12eb091f7f5d19a087df37bd0e2accb8` | `experiment/claim-6-group-framework` | Full corruption-group reconstruction framework |
| `orx/claim-6-full-noise-group` | `ca9fa19f591b44ac9df1381ec4f2d35d87eed16b` | `experiment/claim-6-noise-group` | Noise-group reconstruction configuration |
| `orx/claim-6-full-blur-group` | `7dfcff01a39fd18a9affe24253dc207c8a2dc105` | `experiment/claim-6-blur-group` | Blur-group reconstruction configuration |
| `orx/claim-6-full-weather-group` | `31d05e7b7874c7aa42ec2095719a7258af9cf599` | `experiment/claim-6-weather-group` | Weather-group reconstruction configuration |
| `orx/claim-6-full-digital-group` | `e01f62881aba47f64abc594b5daf2a41b77308a6` | `experiment/claim-6-digital-group` | Digital-group reconstruction configuration |
| `orx/claim-6-full-gaussian-noise-component` | `f06a2d84ab01ed0e58e28e6b52f606b236422dc2` | `experiment/claim-6-gaussian-noise` | Gaussian-noise component shard |
| `orx/claim-6-full-shot-noise-component` | `2c13512114f75393a4bd4a1e59c39f1de9383460` | `experiment/claim-6-shot-noise` | Shot-noise component shard |
| `orx/claim-6-full-impulse-noise-component` | `3dccf66f3831c1db97d26a87c3294d62672a51df` | `experiment/claim-6-impulse-noise` | Impulse-noise component shard |
| `orx/claim-6-full-defocus-blur-component` | `f89ca8eb49258c1810ea1c099fd0e59d9e0d1d42` | `experiment/claim-6-defocus-blur` | Defocus-blur component shard |
| `orx/claim-6-full-glass-blur-component` | `7e2c192dba49808033dc27f3112d2f04dfbcd22a` | `experiment/claim-6-glass-blur` | Glass-blur component shard |
| `orx/claim-6-full-motion-blur-component` | `1f50a13639b722bd5340ca77dff9e99fa28602e5` | `experiment/claim-6-motion-blur` | Motion-blur component shard |
| `orx/claim-6-full-zoom-blur-component` | `d550d8719bbdb7038731362d207a70db60254a0f` | `experiment/claim-6-zoom-blur` | Zoom-blur component shard |
| `orx/claim-6-full-snow-component` | `ed839181f2a8aa4662d527ed1eff0bdd147f9ad1` | `experiment/claim-6-snow` | Snow component shard |
| `orx/claim-6-full-frost-component` | `0906f12fb0613c8b4faeb35eef5877027e63cf3d` | `experiment/claim-6-frost` | Frost component shard |
| `orx/claim-6-full-fog-component` | `1ee32607fa859e1035c9fc84c2afb6fdcaad266c` | `experiment/claim-6-fog` | Fog component shard |
| `orx/claim-6-full-brightness-component` | `6170e95b8378638669fe2610dfac8213eba3bdb5` | `experiment/claim-6-brightness` | Brightness component shard |
| `orx/claim-6-full-contrast-component` | `96460286c2505d28a37b407e6e1ae37b4d69fb8e` | `experiment/claim-6-contrast` | Contrast component shard |
| `orx/claim-6-full-elastic-transform-component` | `a0132c379c6f888ecb053ae53fcb6822e61e80f6` | `experiment/claim-6-elastic-transform` | Elastic-transform component shard |
| `orx/claim-6-full-pixelate-component` | `6457d85f2e213517e6ba3d062840718c59775666` | `experiment/claim-6-pixelate` | Pixelate component shard |
| `orx/claim-6-full-jpeg-compression-component` | `1e8d603e1a00f4f788329122a522d576611277c4` | `experiment/claim-6-jpeg-compression` | JPEG-compression component shard |

## Branch invariants

- `main` is the default branch and contains the complete reader-facing audit.
- Evidence branches retain their original tips and are not presented as fresh
  full-paper reproductions.
- The ImageNet-C component branches are historical attempts and do not change
  C6 from `BLOCKED` without full-scope data and independent re-aggregation.
- Historical run logs may mention the old `orx/*` names because those names are
  part of the provenance record. They are not live branch names after cleanup.
