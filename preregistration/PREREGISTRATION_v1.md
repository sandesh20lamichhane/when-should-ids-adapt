# Pre-Registration v1 — When Should an IDS Adapt?
## Cost-Sensitive Selective Retraining for Intrusion Detection Under Concept Drift and Emerging Attacks

**Status:** FINAL — commit this file, then tag `prereg-v1` and push the tag
**before any experiment touches an evaluation stream.**

Tag commit hash (fill after tagging): `COMMIT_HASH: fbe8189`
Date frozen: 2026-08-19

Evidence base for the decisions herein: notebook 01 family distributions and
notebook 02 family × split matrices (reproduced in §5), both committed to this
repository before this freeze.

---

## 1. Hypotheses and acceptance gates

Gates are evaluated per primary corpus. A hypothesis is **accepted** only if
its gate holds on ≥ 2 of the 3 primary corpora. Thresholds are frozen at tag
time; any deviation must be reported in §9.

### H1 — Selective retraining retains benefit at a fraction of cost
- Gate: macro-F1 over post-onset windows ≥ **95%** of the S2
  (retrain-on-every-drift) baseline, while consuming ≤ **30%** of S2's label
  budget and ≤ **40%** of its retraining events.
- Statistical criterion: paired bootstrap 95% CI (10,000 resamples over
  windows) on the F1 ratio excludes 0.90.

### H2 — Joint trigger dominates single-signal triggers
- Gate: S5's budget–performance curve Pareto-dominates S3 (drift-only) and S4
  (novelty-only) at ≥ **4 of 5** budget points in {1%, 2%, 5%, 10%, 20%} of
  stream labels.
- Statistical criterion: Wilcoxon signed-rank across seeds × ramp profiles,
  p < 0.05, Holm-corrected over budget points.

### H3 — Novelty verification shortens zero-day recovery
- Gate: median detection delay for the held-out family (windows from onset
  until family recall ≥ 0.7) is ≥ **25%** lower for S5 than S1 (periodic) at
  equal label budget.

### H4 — SHAP adds no material value to the trigger (equivalence)
- Gate: TOST with equivalence bounds ±0.02 macro-F1 at every budget point,
  α = 0.05, comparing S5 with vs. without SHAP-derived trigger features.
- Pre-registered as an **equivalence claim**, not a nil finding.

## 2. Datasets (frozen)

Primary (gate-bearing): CICIDS2017 (Engelen-corrected improved release),
CSE-CIC-IDS2018 (DistriNet improved release), UNSW-NB15 (full 4-part CSVs).
Secondary (robustness, no gates): LUFlow (clone db78471), TON_IoT,
Edge-IIoTset, CICIoT2023. DNS extension (Phase 5 / Paper 3): CIC-Bell-DNS
2021, UMUDGA. NSL-KDD and KDD'99 are excluded as methodologically obsolete.
Full catalog: `docs/DATASETS.md`.

Processed sizes: cicids2017 = 2,099,971 rows; cse_cic_ids2018 = 63,195,088
rows; unsw_nb15 = 2,540,047 rows. Common schema: 84 (CIC) / ~40 (UNSW)
float32 features + label + family + timestamp + attempted.

## 3. Label and family policies (frozen)

- Family map: `src`-committed normalisation-robust map (notebook 01 cell 5).
  The `backdoors`/`backdoor` UNSW variant is normalised to `backdoor` at load
  time.
- **Attempted policy:** flows labelled "` - Attempted`" (improved releases)
  are flagged and **excluded** from IDS training, calibration, and hold-out
  injection. Sensitivity analysis including them may be reported as
  supplementary, clearly labelled.
- **Hold-out eligibility:** ≥ 5,000 completed flows in the corpus (all
  segments pooled).

**Hold-out grid (15 units):**

| Corpus | Hold-out families (completed flows) | Excluded |
|---|---|---|
| cicids2017 | dos 171,634 · portscan 159,066 · ddos 95,144 · infiltration 71,803 · bruteforce 6,933 | botnet 736 · web 104 · heartbleed 11 |
| cse_cic_ids2018 | dos 1,834,210 · ddos 1,374,148 · botnet 142,921 · bruteforce 94,197 · infiltration 89,663 | web 283 |
| unsw_nb15 | generic 215,481 · exploits 44,525 · fuzzers 24,246 · dos 16,353 · reconnaissance 13,987 | analysis · backdoor · shellcode · worms |

## 4. Temporal splits (frozen; built by notebook 02, all integrity checks PASS)

Fractions (0.50, 0.20, 0.30) of the corpus timeline; boundaries at the 50%
and 70% timestamp quantiles; segments internally sorted, non-overlapping,
row-conserving. NaT-timestamp rows dropped with counts recorded in
`splits_meta.json`.

| Corpus | train/cal boundary | cal/eval boundary |
|---|---|---|
| cicids2017 | 2017-07-05 16:45:41 | 2017-07-06 18:32:15 |
| cse_cic_ids2018 | 2018-02-21 21:18:21 | 2018-02-28 12:51:42 |
| unsw_nb15 | 2015-02-18 02:36:17 | 2015-02-18 06:25:00 |

## 5. Family × segment evidence (notebook 02 cell 6, completed flows)

cicids2017: train {benign 865,503; dos 171,634; bruteforce 6,933} ·
cal {benign 369,538; infiltration 48,346; web 104; heartbleed 11} ·
eval {benign 347,520; portscan 159,066; ddos 95,144; infiltration 23,457;
botnet 736}.

cse_cic_ids2018: train {benign 27,989,197; dos 1,834,210; ddos 1,374,148;
bruteforce 94,197} · cal {benign 12,638,579; web 283} · eval {benign
18,725,653; botnet 142,921; infiltration 89,663}.

unsw_nb15: all major families span all three segments — generic
25,192/88,399/101,890; exploits 11,024/14,107/19,394; fuzzers
7,568/6,550/10,128; dos 3,829/4,563/7,961; reconnaissance 3,569/4,045/6,373
(train/cal/eval).

Implication (drives §6): the CIC corpora are day-structured — attack families
are temporally disjoint across segments; UNSW-NB15 is temporally mixed.

## 6. Zero-day evaluation protocol (frozen)

**Mode B — controlled injection (PRIMARY; all gates evaluated here).**
For each hold-out unit (corpus, family f):
1. Training data = train segment, minus all flows of f, minus attempted flows.
2. Calibration stream = cal segment, minus f, minus attempted flows, and
   restricted to benign + **known families** (see rule below). All Stage-1
   thresholds (FP budget 1%) and the novelty committee are fixed here and
   never re-fit.
3. Evaluation background = eval segment minus f (and minus attempted flows).
4. Injection: all completed flows of f (pooled from every segment, preserving
   their internal temporal order) are injected at onset = **40%** of the eval
   stream, under two ramp profiles: **abrupt** (step) and **gradual** (linear
   ramp over 10% of stream length).
5. Windows of 5,000 flows; replay in strict temporal order.

**Known-family rule:** a family is "known" for an experiment iff it has
≥ 1,000 completed flows in the train segment (after removing f). Attack flows
of non-known families are removed from the calibration stream to prevent
unknown attacks from contaminating detector calibration. (Known sets —
cicids2017: dos, bruteforce; cse_cic_ids2018: dos, ddos, bruteforce;
unsw_nb15: generic, exploits, fuzzers, dos, reconnaissance.)

**Mode A — natural emergence (companion analysis; no gates).**
The eval segment replayed unmodified (attempted flows removed). Emerging
families = those absent from the train segment: cicids2017 {portscan, ddos};
cse_cic_ids2018 {botnet, infiltration}. cicids2017 infiltration is excluded
from Mode A (first appearance precedes the eval segment). Reported as
ecological validation alongside Mode B.

Random-shuffle evaluation is prohibited everywhere.

## 7. Strategies, budgets, seeds, metrics (frozen)

Strategies: S0 never-retrain · S1 periodic (every 10% of stream) · S2 retrain
on every Stage-1 alarm · S3 drift-triggered only · S4 novelty-triggered only ·
S5 cost-aware joint trigger (proposed). Acquisition ablation within S5:
random / uncertainty / core-set diversity / hybrid.

Label budgets: {1%, 2%, 5%, 10%, 20%} of eval-stream flows.
Cost-parameter grid: severity ∈ {1, 3, 10, 30} × c_label ∈ {0.005, 0.02,
0.08} — all results reported as frontiers over the full grid.
Seeds: {11, 23, 37, 51, 73}. Every reported number aggregates 5 seeds × 2
ramp profiles unless stated otherwise.

Primary metrics: macro-F1 over post-onset windows; per-family recall
trajectory; detection delay to recall 0.7; area under budget–performance
frontier. Secondary: false-alarm rate on benign, labels consumed, retraining
count, wall-clock adaptation cost. Inference: paired bootstrap CIs; Wilcoxon
signed-rank with Holm correction; TOST for H4. Every reported CI/p-value pair
is checked for mutual consistency before submission.

## 8. Models (frozen)

Frozen IDS: RandomForest (n_estimators = 300, class_weight = 'balanced') and
XGBoost as primary classifiers; identical features across strategies.
Stage 1: per-feature KS, Wasserstein-1, PSI; window MMD (RBF, median
heuristic). Stage 2 committee: IsolationForest (200 trees), autoencoder
reconstruction error, kNN distance (k = 10); percentile normalisation fixed
on the calibration stream. Stage 3: risk–cost trigger with hybrid
uncertainty × diversity acquisition.

## 9. Exclusions and deviations

Any post-hoc exclusion of runs, families, or corpora, and any deviation from
this document, must be listed here with justification and reported in the
paper's deviations table.

| Date | Deviation | Justification |
|---|---|---|
| — | — | — |
