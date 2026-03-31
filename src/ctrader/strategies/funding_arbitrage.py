from __future__ import annotations

import pandas as pd


def make_signal(funding_df: pd.DataFrame, open_th: float = 1e-4, close_th: float = 5e-5):
    f = funding_df.copy()
    tcol = "fundingTime" if "fundingTime" in f.columns else f.columns[0]
    f[tcol] = pd.to_datetime(f[tcol], unit="ms", utc=True)
    f = f.set_index(tcol).sort_index()

    def _signal(df: pd.DataFrame) -> pd.Series:
        aligned = f["fundingRate"].reindex(df.index, method="ffill").fillna(0.0)
        s = pd.Series(0, index=df.index, dtype=float)
        s[aligned >= open_th] = 1
        s[aligned <= -open_th] = -1
        s[aligned.abs() <= close_th] = 0
        return s.ffill().fillna(0)

    return _signal
