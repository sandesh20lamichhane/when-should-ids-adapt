# Pre-Registration v1 — When Should an IDS Adapt?

**Status:** DRAFT — do not run any experiment on test streams until this file is
finalised, committed, and tagged `prereg-v1`. Record the tag's commit hash here
after tagging: `COMMIT_HASH: ____________`

**Date frozen:** ____________

---

## 1. Hypotheses and acceptance gates

Gates are evaluated per dataset. A hypothesis is **accepted** only if its gate
holds on ≥ 2 of the 3 primary corpora. All thresholds below are frozen at tag
time and may not be altered afterwards for any reason; deviations must be
reported as deviations.

### H1 — Selective retraining retains benefit at a fraction of cost
- Gate: macro-F1 over post-drift windows ≥ **95%** of the S2
  (retrain-on-every-drift) baseline, while consuming ≤ **30%** of S2's label
  budget and ≤ **40%** of its retraining events.
- Statistical criterion: bootstrap 95% CI (10,000 resamples, paired over
  windows) on the F1 ratio excludes 0.90.

### H2 — Joint trigger dominates single-signal triggers
- Gate: S5's budget–performance curve Pareto-dominates S3 and S4 at ≥ **4 of 5**
  budget points in {1%, 2%, 5%, 10%, 20%} of stream labels.
- Statistical criterion: Wilcoxon signed-rank across seeds × injection
  schedules, p < 0.05, Holm-corrected over budget points.

### H3 — Novelty verification shortens zero-day recovery
- Gate: median detection delay for the held-out family (stream position until
  family recall ≥ 0.7) is ≥ **25%** lower for S5 than S1 (periodic) at equal
  label budget.

### H4 — SHAP adds no material value to the trigger (equivalence)
- Gate: TOST with equivalence bounds ±0.02 macro-F1 at every budget point,
  α = 0.05, comparing S5 with and without SHAP-derived trigger features.
- This is pre-registered as an **equivalence claim**, not a nil finding.

## 2. Datasets and roles (frozen)

| Corpus | Role |
|---|---|
| CICIDS2017 (Engelen-corrected) | Primary — leave-one-family-out |
| CSE-CIC-IDS2018 (Liu-corrected) | Primary — leave-one-family-out + temporal |
| UNSW-NB15 | Primary — leave-one-family-out; cross-dataset source |
| LUFlow | Secondary — real longitudinal drift |
| TON_IoT / Edge-IIoTset | Secondary — IoT generalisation |
| CICIoT2023 | Secondary — scale robustness |

NSL-KDD is excluded. Random-shuffle evaluation is prohibited everywhere.

## 3. Zero-day protocol (frozen)

For each primary corpus and each attack family *f* with ≥ 5,000 flows:
1. Train the IDS with *f* removed entirely from all training data.
2. Build a strictly temporal stream; inject *f* at onset position 40% of the
   stream, under two ramp profiles: abrupt (step) and gradual (linear over 10%
   of stream length).
3. All detector/committee thresholds are calibrated on a disjoint calibration
   stream containing benign + known-attack traffic only — never family *f*.

## 4. Strategies compared (frozen)

S0 never-retrain · S1 periodic (every 10% of stream) · S2 retrain on every
Stage-1 alarm · S3 drift-triggered only · S4 novelty-triggered only ·
S5 cost-aware joint trigger (proposed).

Active-learning acquisition ablation within S5: random / uncertainty /
core-set diversity / hybrid.

## 5. Metrics (frozen)

Primary: macro-F1 (post-onset windows); per-family recall trajectory;
detection delay to recall 0.7; area under budget–performance frontier.
Secondary: FPR on benign, labels consumed, retraining count, wall-clock cost.

## 6. Seeds and repetitions (frozen)

Seeds: {11, 23, 37, 51, 73}. Every reported number aggregates all 5 seeds ×
both ramp profiles unless stated otherwise.

## 7. Exclusions and deviations

Any post-hoc exclusion of runs, families, or corpora must be listed here with
justification, and reported in the paper's deviations table.
