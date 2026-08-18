"""Metrics + pre-registered hypothesis gate evaluation.

Notebook 08 calls ONLY functions in this module to decide H1-H4, so the gate
logic is reviewable in one place and matches PREREGISTRATION_v1.md verbatim.
"""
from __future__ import annotations
import numpy as np
from .config import CFG


# ---------------- core metrics ----------------

def detection_delay(recall_trajectory: np.ndarray, onset_window: int) -> float:
    """Windows from onset until family recall >= CFG.RECOVERY_RECALL.
    Returns np.inf if never recovered."""
    post = recall_trajectory[onset_window:]
    hits = np.where(post >= CFG.RECOVERY_RECALL)[0]
    return float(hits[0]) if len(hits) else float("inf")


def frontier_area(budgets: np.ndarray, f1s: np.ndarray) -> float:
    """Area under the budget-performance curve (trapezoid), normalised by
    budget range — higher is better."""
    order = np.argsort(budgets)
    b, f = np.asarray(budgets)[order], np.asarray(f1s)[order]
    return float(np.trapz(f, b) / (b[-1] - b[0]))


def pareto_dominates(f1_a: np.ndarray, f1_b: np.ndarray) -> np.ndarray:
    """Pointwise: does A dominate B at each shared budget point?"""
    return np.asarray(f1_a) >= np.asarray(f1_b)


# ---------------- bootstrap ----------------

def bootstrap_ratio_ci(x: np.ndarray, y: np.ndarray, n_boot: int = 10_000,
                       seed: int = 0, alpha: float = 0.05):
    """Paired bootstrap CI for mean(x)/mean(y). Used by the H1 gate."""
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(x), size=(n_boot, len(x)))
    ratios = x[idx].mean(axis=1) / np.clip(y[idx].mean(axis=1), 1e-12, None)
    lo, hi = np.quantile(ratios, [alpha / 2, 1 - alpha / 2])
    return float(np.mean(x) / np.mean(y)), float(lo), float(hi)


# ---------------- gates (verbatim from PREREGISTRATION_v1.md) ----------------

def gate_h1(f1_s5: np.ndarray, f1_s2: np.ndarray,
            labels_s5: float, labels_s2: float,
            retrains_s5: int, retrains_s2: int, seed: int = 0) -> dict:
    ratio, lo, hi = bootstrap_ratio_ci(f1_s5, f1_s2, seed=seed)
    return {
        "ratio": ratio, "ci_low": lo, "ci_high": hi,
        "label_frac": labels_s5 / max(labels_s2, 1e-12),
        "retrain_frac": retrains_s5 / max(retrains_s2, 1),
        "pass": (ratio >= 0.95 and lo > 0.90
                 and labels_s5 <= 0.30 * labels_s2
                 and retrains_s5 <= 0.40 * retrains_s2),
    }


def gate_h3(delays_s5: np.ndarray, delays_s1: np.ndarray) -> dict:
    m5, m1 = np.median(delays_s5), np.median(delays_s1)
    return {"median_s5": float(m5), "median_s1": float(m1),
            "reduction": float(1 - m5 / max(m1, 1e-12)),
            "pass": m5 <= 0.75 * m1}


def gate_h4_tost(diff_per_budget: np.ndarray, bound: float = 0.02,
                 alpha: float = 0.05) -> dict:
    """TOST equivalence on frontier differences (with-SHAP minus without).
    Uses t-tests per pre-registration; requires >= 5 paired observations
    per budget point (seeds x schedules)."""
    from scipy import stats
    d = np.asarray(diff_per_budget, dtype=float)
    t_lo = stats.ttest_1samp(d, -bound, alternative="greater")
    t_hi = stats.ttest_1samp(d, bound, alternative="less")
    p = max(t_lo.pvalue, t_hi.pvalue)
    return {"mean_diff": float(d.mean()), "tost_p": float(p),
            "pass_equivalence": p < alpha}
