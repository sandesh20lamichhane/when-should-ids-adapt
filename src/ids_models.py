
"""Baseline IDS training - leave-one-family-out (prereg-v1 @ 54e54c8).

Frozen hyperparameters (notebook 03, documented decisions 2-3):
  RandomForest: n_estimators=300, class_weight='balanced', min_samples_leaf=10
  XGBoost:      tree_method='hist', n_estimators=300, max_depth=8,
                learning_rate=0.1, objective='multi:softprob'
Task: multi-class over {benign + families present in the unit's training data}.
"""
import time
import numpy as np
import pandas as pd
import joblib
from pathlib import Path

META = ('label','family','timestamp','attempted')


def load_unit_training(splits_dir: Path, corpus: str, heldout: str):
    """Full train segment minus held-out family minus attempted flows.
    Returns X (float32 ndarray), y (family strings), feature list."""
    df = pd.read_parquet(splits_dir / f'{corpus}__train.parquet')
    df['family'] = df['family'].replace({'backdoors': 'backdoor'})
    df = df[(~df['attempted']) & (df['family'] != heldout)]
    feat = [c for c in df.columns if c not in META]
    X = df[feat].to_numpy(np.float32)
    y = df['family'].to_numpy()
    n_rows = len(df); del df
    return X, y, feat, n_rows


def train_rf(X, y, seed: int):
    from sklearn.ensemble import RandomForestClassifier
    m = RandomForestClassifier(n_estimators=300, class_weight='balanced',
                               min_samples_leaf=10, n_jobs=-1,
                               random_state=seed)
    t0 = time.time(); m.fit(X, y)
    return m, time.time() - t0


def train_xgb(X, y, seed: int):
    from xgboost import XGBClassifier
    from sklearn.utils.class_weight import compute_sample_weight
    from sklearn.preprocessing import LabelEncoder
    le = LabelEncoder(); yi = le.fit_transform(y)
    w = compute_sample_weight('balanced', yi)
    m = XGBClassifier(tree_method='hist', n_estimators=300, max_depth=8,
                      learning_rate=0.1, objective='multi:softprob',
                      num_class=len(le.classes_), random_state=seed,
                      n_jobs=-1, verbosity=0)
    t0 = time.time(); m.fit(X, yi, sample_weight=w)
    m._label_encoder_classes = le.classes_          # for decoding predictions
    return m, time.time() - t0


def model_path(models_dir: Path, corpus, family, model, seed) -> Path:
    return models_dir / f'{corpus}__{family}__{model}__s{seed}.joblib'


def save_model(m, path: Path):
    joblib.dump(m, path, compress=3)
    return path.stat().st_size / 1e9


def cal_sanity(m, splits_dir: Path, corpus, heldout, known, feat,
               batch=1_000_000):
    """Sanity accuracy on the calibration stream restricted per the
    known-family rule (prereg section 6). Never touches eval."""
    import pyarrow.parquet as pq
    src = pq.ParquetFile(splits_dir / f'{corpus}__cal.parquet')
    correct = total = 0
    classes = getattr(m, '_label_encoder_classes', None)
    for b in src.iter_batches(batch_size=batch):
        d = b.to_pandas()
        d['family'] = d['family'].replace({'backdoors': 'backdoor'})
        d = d[(~d['attempted']) & (d['family'] != heldout)
              & (d['family'].isin(list(known) + ['benign']))]
        if not len(d): continue
        yp = m.predict(d[feat].to_numpy(np.float32))
        if classes is not None: yp = classes[yp]
        correct += int((yp == d['family'].to_numpy()).sum()); total += len(d)
        del d
    return correct / max(total, 1), total
