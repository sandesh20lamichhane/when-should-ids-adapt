"""Temporal streaming + leave-one-attack-family-out zero-day injection.

Hard rules (pre-registered):
  * strictly temporal order — random shuffling is prohibited everywhere
  * the held-out family never appears in training or calibration data
  * injection onset and ramp profile are fixed constants from CFG
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from .config import CFG


def temporal_sort(df: pd.DataFrame, time_col: str) -> pd.DataFrame:
    return df.sort_values(time_col, kind="mergesort").reset_index(drop=True)


def leave_one_family_out(df: pd.DataFrame, family_col: str, family: str):
    """Split into (train_pool, heldout_family). Train pool keeps benign and
    all OTHER attack families; the held-out family is returned separately for
    later injection."""
    held = df[df[family_col] == family].copy()
    rest = df[df[family_col] != family].copy()
    if len(held) < CFG.MIN_FAMILY_FLOWS:
        raise ValueError(
            f"family '{family}' has {len(held)} flows < "
            f"MIN_FAMILY_FLOWS={CFG.MIN_FAMILY_FLOWS}; skip per prereg §3")
    return rest, held


def build_stream(background: pd.DataFrame, held: pd.DataFrame,
                 time_col: str, ramp: str = "abrupt",
                 seed: int = 0) -> pd.DataFrame:
    """Create the evaluation stream: temporally ordered background traffic
    with the held-out family injected at CFG.ZERO_DAY_ONSET.

    ramp='abrupt': all held flows appear from onset in their own temporal order.
    ramp='gradual': injection probability rises linearly over
                    CFG.GRADUAL_RAMP_LEN of the stream, then 1.0.
    """
    rng = np.random.default_rng(seed)
    bg = temporal_sort(background, time_col)
    hd = temporal_sort(held, time_col)
    n = len(bg)
    onset = int(n * CFG.ZERO_DAY_ONSET)
    ramp_end = onset + int(n * CFG.GRADUAL_RAMP_LEN)

    # positions where held flows are interleaved into the background
    if ramp == "abrupt":
        pos = np.sort(rng.integers(onset, n, size=len(hd)))
    elif ramp == "gradual":
        # rejection-sample positions with linearly increasing acceptance
        pos = []
        while len(pos) < len(hd):
            p = rng.integers(onset, n)
            accept = 1.0 if p >= ramp_end else (p - onset) / max(1, ramp_end - onset)
            if rng.random() < accept:
                pos.append(p)
        pos = np.sort(np.array(pos))
    else:
        raise ValueError(ramp)

    bg = bg.assign(_inj=False)
    hd = hd.assign(_inj=True)
    hd = hd.assign(_pos=pos)
    bg = bg.assign(_pos=np.arange(n))
    stream = pd.concat([bg, hd]).sort_values(["_pos", "_inj"]).reset_index(drop=True)
    return stream.drop(columns="_pos")


def iter_windows(stream: pd.DataFrame, feature_cols: list,
                 window: int | None = None):
    """Yield (window_index, X_window, meta_window) in temporal order."""
    w = window or CFG.WINDOW_SIZE
    for i in range(0, len(stream) - w + 1, w):
        chunk = stream.iloc[i:i + w]
        yield i // w, chunk[feature_cols].to_numpy(dtype=float), chunk
