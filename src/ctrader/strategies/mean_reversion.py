from __future__ import annotations

import numpy as np
import pandas as pd


def make_signal(window: int = 50, entry_z: float = 2.0, exit_z: float = 0.5):
    def _signal(df: pd.DataFrame) -> pd.Series:
        close = df["close"]
        ma = close.rolling(window).mean()
        sd = close.rolling(window).std().replace(0, np.nan)
        z = (close - ma) / sd
        s = pd.Series(0, index=df.index, dtype=float)
        s[z <= -entry_z] = 1
        s[z >= entry_z] = -1
        s[np.abs(z) <= exit_z] = 0
        return s.ffill().fillna(0)
    return _signal
