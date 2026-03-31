from __future__ import annotations

import numpy as np
import pandas as pd


def drawdown(equity: pd.Series) -> pd.Series:
    peak = equity.cummax()
    return equity / peak - 1.0


def summarize(returns: pd.Series, trades: pd.DataFrame, periods_per_year: int) -> dict:
    equity = (1 + returns.fillna(0)).cumprod()
    total = float(equity.iloc[-1] - 1)
    ann_ret = float((equity.iloc[-1]) ** (periods_per_year / max(1, len(returns))) - 1)
    ann_vol = float(returns.std() * np.sqrt(periods_per_year))
    sharpe = ann_ret / ann_vol if ann_vol > 0 else 0.0
    dd = drawdown(equity)
    mdd = float(dd.min())
    calmar = ann_ret / abs(mdd) if mdd < 0 else 0.0
    win_rate = float((trades["realized_pnl"] > 0).mean()) if len(trades) else 0.0
    return {
        "total_return": total,
        "annualized_return": ann_ret,
        "annualized_vol": ann_vol,
        "sharpe": sharpe,
        "calmar": calmar,
        "max_drawdown": mdd,
        "win_rate": win_rate,
        "trade_count": int(len(trades)),
    }
