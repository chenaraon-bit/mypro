from __future__ import annotations

import numpy as np


def deflated_sharpe_ratio(observed_sharpe: float, n_trials: int, skew: float = 0.0, kurt: float = 3.0) -> float:
    """Lightweight DSR approximation for ranking, not a full paper implementation."""
    if n_trials <= 1:
        return observed_sharpe
    penalty = np.sqrt(2 * np.log(n_trials))
    adjust = 1 + (skew * observed_sharpe) / 6 - ((kurt - 3) * observed_sharpe**2) / 24
    return float((observed_sharpe - penalty) * adjust)


def pbo_from_rank_logits(logits: np.ndarray) -> float:
    """Estimate PBO from CSCV-like logits; >0 means overfit tendency."""
    logits = np.asarray(logits)
    return float((logits < 0).mean())
