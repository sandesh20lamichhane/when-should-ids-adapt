"""Stage 3 — cost-aware adaptation decision + budget-constrained labelling.

Decision rule:  adapt iff  R > C
  R = p_novel * severity * expected_miss     (expected security loss)
  C = c_analyst + c_label*batch + c_compute + c_validation

The cost/severity parameters are NOT tuned to make S5 win: every experiment
sweeps them over the pre-registered grid and reports the full frontier
(see PREREGISTRATION_v1.md and paper §O1).
"""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np


@dataclass
class CostParams:
    c_analyst: float = 1.0        # fixed cost of opening an investigation
    c_label: float = 0.02         # per-label analyst cost
    c_compute: float = 0.5        # one retraining run
    c_validation: float = 0.5     # pre-deployment validation
    severity: float = 10.0        # loss per expected missed attack unit

    def adaptation_cost(self, batch_size: int) -> float:
        return (self.c_analyst + self.c_label * batch_size
                + self.c_compute + self.c_validation)


# Pre-registered sweep grid — frontier is reported across ALL of these.
COST_GRID = [
    CostParams(severity=s, c_label=cl)
    for s in (1.0, 3.0, 10.0, 30.0)
    for cl in (0.005, 0.02, 0.08)
]


def expected_risk(p_novel: float, drift_magnitude: float,
                  params: CostParams) -> float:
    """R = P(novel) x severity x expected miss rate.
    Expected miss rate is proxied by drift magnitude (calibrated KS excess),
    the only decision-time observable — this proxy choice is itself part of
    what the experiments evaluate."""
    return p_novel * params.severity * drift_magnitude


def decide(p_novel: float, drift_magnitude: float, batch_size: int,
           params: CostParams) -> str:
    """Returns 'monitor' or 'investigate'."""
    r = expected_risk(p_novel, drift_magnitude, params)
    c = params.adaptation_cost(batch_size)
    return "investigate" if r > c else "monitor"


# ---------------- selective labelling ----------------

def hybrid_acquisition(X_pool: np.ndarray, uncertainty: np.ndarray,
                       novelty: np.ndarray, batch: int,
                       alpha: float = 0.5, seed: int = 0) -> np.ndarray:
    """Pick `batch` indices mixing informativeness and coverage.

    score = alpha * uncertainty + (1-alpha) * novelty, then greedy core-set
    selection on the top-2*batch candidates so the batch covers the novel
    region instead of re-sampling the densest cluster.
    """
    rng = np.random.default_rng(seed)
    score = alpha * _rank01(uncertainty) + (1 - alpha) * _rank01(novelty)
    cand = np.argsort(score)[-min(2 * batch, len(score)):]
    if len(cand) <= batch:
        return cand
    # greedy k-center over candidates
    chosen = [cand[rng.integers(len(cand))]]
    Xc = X_pool[cand]
    dist = np.linalg.norm(Xc - X_pool[chosen[0]], axis=1)
    for _ in range(batch - 1):
        nxt = cand[int(np.argmax(dist))]
        chosen.append(nxt)
        dist = np.minimum(dist, np.linalg.norm(Xc - X_pool[nxt], axis=1))
    return np.array(chosen)


def _rank01(x: np.ndarray) -> np.ndarray:
    r = np.argsort(np.argsort(x))
    return r / max(1, len(x) - 1)
