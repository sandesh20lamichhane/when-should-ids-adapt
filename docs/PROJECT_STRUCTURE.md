# Project Structure — the two-home design

This project deliberately lives in TWO places. They are NOT copies of each
other and must never be merged.

| Home | What lives there | Why |
|---|---|---|
| **GitHub repo** `when-should-ids-adapt` | code (`src/`), notebooks, docs, `preregistration/`, small `results/` CSVs, `figures/` | versioned, reviewable, cited in the paper |
| **Google Drive** `MyDrive/ids-adapt/` | `data/raw/`, `data/processed/`, `models/`, `checkpoints/` | gigabytes; survives Colab VM resets; never in git |

## GitHub repo tree (authoritative)

    when-should-ids-adapt/
    |-- README.md                  project overview
    |-- requirements.txt           pinned packages (sklearn==1.5.2)
    |-- .gitignore                 keeps data/models out of git
    |-- docs/
    |   `-- PROJECT_STRUCTURE.md   this file
    |-- preregistration/
    |   `-- PREREGISTRATION_v1.md  H1-H4 gates; tag prereg-v1 before experiments
    |-- notebooks/                 numbered = execution order; built one at a time
    |   |-- 00_environment_setup.ipynb        [BUILT]
    |   |-- 01_data_download_and_prep.ipynb   [next]
    |   |-- 02_temporal_splits_and_calibration.ipynb
    |   |-- 03_baseline_ids_training.ipynb
    |   |-- 04_stage1_drift_screening.ipynb
    |   |-- 05_stage2_novelty_committee.ipynb
    |   |-- 06_stage3_cost_trigger.ipynb
    |   |-- 07_strategies_s0_s5_experiments.ipynb
    |   |-- 08_frontier_analysis_hypothesis_gates.ipynb
    |   `-- 09_figures_for_paper.ipynb
    |-- src/                       ALL logic lives here; notebooks only orchestrate
    |   |-- config.py              [stub] CFG: seeds, budgets, paths, dataset registry
    |   |-- checkpoint.py          [REAL] CheckpointManager (ledger + artifacts)
    |   |-- drift.py               [stub] Stage 1: KS / W1 / PSI / MMD
    |   |-- novelty.py             [stub] Stage 2: IF + AE + kNN committee
    |   |-- trigger.py             [stub] Stage 3: cost model + acquisition
    |   |-- streams.py             [stub] temporal streams + family injection
    |   `-- metrics.py             [stub] gates H1-H4, delay, frontier
    |-- results/                   CSVs named <exp>__<data>__s<seed>__<githash>.csv
    `-- figures/                   paper-ready PDFs from notebook 09

## Google Drive tree (authoritative)

    MyDrive/ids-adapt/
    |-- data/
    |   |-- raw/                   one folder per corpus, exact names:
    |   |   |-- cicids2017/  cse_cic_ids2018/  unsw_nb15/  luflow/
    |   |   `-- ton_iot/  ciciot2023/  cic_bell_dns2021/  umudga/
    |   `-- processed/             harmonised parquet, written by notebook 01
    |-- models/                    <corpus>__<family>__<model>__s<seed>.joblib
    `-- checkpoints/               <run_name>/ledger.json + artifacts (resume system)

Nothing else belongs in ids-adapt/ on Drive. In particular, NO .ipynb files
on Drive - notebooks are saved to GitHub only
(Colab: File > Save a copy in GitHub > path notebooks/<name>.ipynb).

## Rules

1. Code changes -> commit + push from Colab (push cell at the end of nb 00).
2. Notebook changes -> File > Save a copy in GitHub. Never edit via GitHub web.
3. Heavy files -> Drive only; .gitignore enforces this.
4. Results CSVs carry the git hash of the code that produced them.
5. If GitHub and a local VM disagree, GitHub wins: delete /content/repo, re-clone.
