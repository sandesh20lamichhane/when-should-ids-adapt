# When Should an IDS Adapt?
### Cost-Sensitive Selective Retraining for Intrusion Detection Under Concept Drift and Emerging Attacks

Paper 2 in the research line started by
[`ids-drift-localization`](https://github.com/sandesh20lamichhane/ids-drift-localization)
(Paper 1: *When Does SHAP-Based Drift Localization Beat a Simple Statistical Test?*).

**Central question:** not *whether* drift can be detected, but *when the estimated
security benefit of adaptation exceeds its operational cost.*

## Repository structure

```
when-should-ids-adapt/
├── preregistration/          # Hypothesis gates — COMMIT & TAG BEFORE any experiment
│   └── PREREGISTRATION_v1.md
├── notebooks/                # Colab notebooks, numbered = execution order
│   ├── 00_environment_setup.ipynb
│   ├── 01_data_download_and_prep.ipynb
│   ├── 02_temporal_splits_and_calibration.ipynb
│   ├── 03_baseline_ids_training.ipynb
│   ├── 04_stage1_drift_screening.ipynb
│   ├── 05_stage2_novelty_committee.ipynb
│   ├── 06_stage3_cost_trigger.ipynb
│   ├── 07_strategies_s0_s5_experiments.ipynb
│   ├── 08_frontier_analysis_hypothesis_gates.ipynb
│   └── 09_figures_for_paper.ipynb
├── src/                      # Shared library imported by every notebook
│   ├── config.py             # seeds, budgets, paths, dataset registry
│   ├── drift.py              # Stage 1: KS, Wasserstein-1, PSI, MMD
│   ├── novelty.py            # Stage 2: IF, autoencoder, kNN committee
│   ├── trigger.py            # Stage 3: risk–cost decision + selective labelling
│   ├── streams.py            # temporal streaming + leave-one-family-out injection
│   └── metrics.py            # detection delay, frontier area, gate evaluation
├── results/                  # per-experiment CSV/parquet (small files tracked)
├── figures/                  # paper-ready figures
└── data/                     # NOT tracked — lives on Google Drive (see data/README.md)
```

## Colab Pro+ workflow

Every notebook starts with the same bootstrap cell:

```python
from google.colab import drive
drive.mount('/content/drive')

!git clone https://github.com/sandesh20lamichhane/when-should-ids-adapt.git /content/repo 2>/dev/null || (cd /content/repo && git pull)
import sys; sys.path.insert(0, '/content/repo')

from src.config import CFG   # all paths point into Drive
```

Rules that keep the project reproducible on Colab:

1. **All logic lives in `src/`, notebooks only orchestrate.** If a function is
   needed in two notebooks, it moves to `src/` — never copy-pasted.
2. **Data and model checkpoints live on Drive** (`CFG.DATA_ROOT`), never in the
   repo and never only on the Colab VM (VMs are ephemeral).
3. **Every experiment writes a CSV to `results/` with the git commit hash and
   seed in the filename.** Notebook 08 only reads `results/` — it never re-runs
   experiments.
4. **Seeds are fixed in `src/config.py`** and iterated explicitly; no hidden
   randomness.
5. **The pre-registration is tagged (`prereg-v1`) before notebook 03 is ever
   run on test streams.** The tag's commit hash goes into the paper.

## Order of work

| Phase | Notebooks | Gate |
|---|---|---|
| Protocol | `preregistration/` | tag `prereg-v1` pushed |
| Data | 00–02 | calibration streams frozen |
| Framework | 03–06 | stages unit-checked on calibration data only |
| Experiments | 07 | S0–S5 across corpora × families × seeds |
| Analysis | 08–09 | H1–H4 gates evaluated exactly as pre-registered |
