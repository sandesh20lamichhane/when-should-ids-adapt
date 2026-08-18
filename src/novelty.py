"""Stage 2 — unsupervised novelty verification committee.

Members: Isolation Forest, autoencoder reconstruction error, kNN distance.
(Deep SVDD can be added later; keep the committee interface stable.)

Calibration rule (pre-registered): the committee is fit and its score
normalisation fixed on the disjoint calibration stream — never on the
held-out attack family. See PREREGISTRATION_v1.md §3.
"""
from __future__ import annotations
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPRegressor


class NoveltyCommittee:
    def __init__(self, seed: int = 0, knn_k: int = 10):
        self.seed = seed
        self.knn_k = knn_k
        self.scaler = StandardScaler()
        self.iforest = IsolationForest(n_estimators=200, random_state=seed)
        self.knn = NearestNeighbors(n_neighbors=knn_k)
        # Compact bottleneck AE via sklearn MLP (input -> d/4 -> input).
        # Swap for a torch AE later without changing the interface.
        self.ae = None
        self._cal = {}  # per-member calibration quantile functions

    # ---------------- fitting ----------------
    def fit(self, X_cal: np.ndarray):
        Xs = self.scaler.fit_transform(X_cal)
        d = Xs.shape[1]
        self.iforest.fit(Xs)
        self.knn.fit(Xs)
        self.ae = MLPRegressor(hidden_layer_sizes=(max(4, d // 4),),
                               max_iter=200, random_state=self.seed)
        self.ae.fit(Xs, Xs)
        # store calibration score distributions for percentile normalisation
        self._cal = {name: np.sort(s)
                     for name, s in self._raw_scores(Xs).items()}
        return self

    # ---------------- scoring ----------------
    def _raw_scores(self, Xs: np.ndarray) -> dict:
        rec = np.mean((self.ae.predict(Xs) - Xs) ** 2, axis=1)
        knn_d = self.knn.kneighbors(Xs)[0][:, -1]
        ifo = -self.iforest.score_samples(Xs)   # higher = more anomalous
        return {"iforest": ifo, "ae": rec, "knn": knn_d}

    def score(self, X: np.ndarray) -> np.ndarray:
        """Committee novelty score in [0, 1]: mean of per-member percentile
        ranks relative to the calibration distribution. 0.99 means 'more
        anomalous than 99% of calibration traffic for the average member'."""
        Xs = self.scaler.transform(X)
        raw = self._raw_scores(Xs)
        pct = [np.searchsorted(self._cal[m], raw[m]) / len(self._cal[m])
               for m in raw]
        return np.clip(np.mean(pct, axis=0), 0, 1)

    def window_novelty(self, X: np.ndarray, top_q: float = 0.95) -> float:
        """Window-level novelty: mean committee score of the top (1-top_q)
        most anomalous flows — robust to a novel family being a small
        fraction of the window."""
        s = self.score(X)
        k = max(1, int(len(s) * (1 - top_q)))
        return float(np.sort(s)[-k:].mean())
