"""Stage 1 — cheap statistical drift screening.

Paper 1 finding this stage is built on: per-feature KS matched or beat
SHAP-based localization against model-free ground truth. So Stage 1 is
statistical only; no model explanations enter the trigger path.

All detectors compare a reference window (from the calibration stream)
against the current monitoring window. O(d) per window.
"""
from __future__ import annotations
import numpy as np
from scipy import stats


def ks_per_feature(ref: np.ndarray, cur: np.ndarray) -> np.ndarray:
    """Two-sample KS statistic per feature. Returns shape (d,)."""
    return np.array([stats.ks_2samp(ref[:, j], cur[:, j]).statistic
                     for j in range(ref.shape[1])])


def wasserstein1_per_feature(ref: np.ndarray, cur: np.ndarray,
                             standardize: bool = True) -> np.ndarray:
    """W1 distance per feature, optionally in reference-standardized units
    so distances are comparable across features."""
    out = np.empty(ref.shape[1])
    for j in range(ref.shape[1]):
        r, c = ref[:, j], cur[:, j]
        if standardize:
            mu, sd = r.mean(), r.std() + 1e-12
            r, c = (r - mu) / sd, (c - mu) / sd
        out[j] = stats.wasserstein_distance(r, c)
    return out


def psi_per_feature(ref: np.ndarray, cur: np.ndarray,
                    n_bins: int = 10) -> np.ndarray:
    """Population Stability Index per feature with quantile bins fixed on ref.
    Convention: PSI < 0.1 stable, 0.1-0.25 moderate, > 0.25 major shift."""
    d = ref.shape[1]
    out = np.empty(d)
    for j in range(d):
        edges = np.unique(np.quantile(ref[:, j], np.linspace(0, 1, n_bins + 1)))
        if len(edges) < 3:            # near-constant feature
            out[j] = 0.0
            continue
        r_frac = np.histogram(ref[:, j], bins=edges)[0] / len(ref)
        c_frac = np.histogram(cur[:, j], bins=edges)[0] / len(cur)
        r_frac = np.clip(r_frac, 1e-6, None)
        c_frac = np.clip(c_frac, 1e-6, None)
        out[j] = np.sum((c_frac - r_frac) * np.log(c_frac / r_frac))
    return out


def mmd_rbf(ref: np.ndarray, cur: np.ndarray, subsample: int = 2_000,
            seed: int = 0) -> float:
    """Unbiased-ish window-level MMD^2 with RBF kernel, median heuristic
    bandwidth. Subsamples for O(n^2) tractability on Colab."""
    rng = np.random.default_rng(seed)
    r = ref[rng.choice(len(ref), min(subsample, len(ref)), replace=False)]
    c = cur[rng.choice(len(cur), min(subsample, len(cur)), replace=False)]
    z = np.vstack([r, c])
    d2 = np.sum((z[:, None, :] - z[None, :, :]) ** 2, axis=-1)
    gamma = 1.0 / (np.median(d2[d2 > 0]) + 1e-12)
    k = np.exp(-gamma * d2)
    n, m = len(r), len(c)
    kxx = (k[:n, :n].sum() - np.trace(k[:n, :n])) / (n * (n - 1))
    kyy = (k[n:, n:].sum() - np.trace(k[n:, n:])) / (m * (m - 1))
    kxy = k[:n, n:].mean()
    return float(kxx + kyy - 2 * kxy)


def screen_window(ref: np.ndarray, cur: np.ndarray, seed: int = 0) -> dict:
    """Run the full Stage-1 battery on one window. Aggregate per-feature
    statistics to window level via max and mean (both recorded; the trigger
    uses whichever the pre-registration froze)."""
    ks = ks_per_feature(ref, cur)
    w1 = wasserstein1_per_feature(ref, cur)
    psi = psi_per_feature(ref, cur)
    return {
        "ks_max": float(ks.max()), "ks_mean": float(ks.mean()),
        "w1_max": float(w1.max()), "w1_mean": float(w1.mean()),
        "psi_max": float(psi.max()), "psi_mean": float(psi.mean()),
        "mmd2": mmd_rbf(ref, cur, seed=seed),
    }


def calibrate_threshold(stat_history: np.ndarray, fp_budget: float = 0.01) -> float:
    """Fix the alarm threshold as the (1 - fp_budget) quantile of the statistic
    on the calibration stream — i.e., alarm rate <= fp_budget under no drift.
    MUST be run on calibration data only, before any test stream is touched."""
    return float(np.quantile(stat_history, 1 - fp_budget))
