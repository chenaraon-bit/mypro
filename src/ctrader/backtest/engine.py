from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import pandas as pd

from .broker import SimBroker
from .events import MarketEvent, OrderEvent
from .metrics import summarize, drawdown
from ..config import BacktestConfig


@dataclass
class BacktestResult:
    trades: pd.DataFrame
    returns: pd.Series
    metrics: dict


class BacktestEngine:
    def __init__(self, cfg: BacktestConfig):
        self.cfg = cfg
        self.broker = SimBroker(cfg)

    def run(self, bars: pd.DataFrame, signal_fn: Callable[[pd.DataFrame], pd.Series], qty: float = 1.0) -> BacktestResult:
        sig = signal_fn(bars).reindex(bars.index).fillna(0)
        pos = sig.shift(1).fillna(0)
        rets = bars["close"].pct_change().fillna(0)

        trade_rows = []
        pnl = pd.Series(0.0, index=bars.index)

        prev_pos = 0
        for ts, row in bars.iterrows():
            cur = int(pos.loc[ts])
            if cur != prev_pos:
                side = "BUY" if cur > prev_pos else "SELL"
                bar = MarketEvent(int(ts.value / 1e6), "SYM", row.open, row.high, row.low, row.close, row.volume)
                fill = self.broker.execute(OrderEvent(bar.ts_ms, "SYM", side=side, qty=qty), bar)
                if fill:
                    trade_rows.append({"ts": ts, "side": side, "qty": qty, "price": fill.price, "fee": fill.fee, "slippage": fill.slippage, "realized_pnl": -fill.fee - fill.slippage})
                prev_pos = cur
            pnl.loc[ts] = pos.loc[ts] * rets.loc[ts]

        if trade_rows:
            trade_df = pd.DataFrame(trade_rows)
            fee_ret = trade_df.groupby("ts")["realized_pnl"].sum().reindex(bars.index).fillna(0.0)
        else:
            trade_df = pd.DataFrame(columns=["ts", "side", "qty", "price", "fee", "slippage", "realized_pnl"])
            fee_ret = pd.Series(0.0, index=bars.index)

        net = pnl + fee_ret

        equity = (1 + net).cumprod()
        live = (drawdown(equity) > -self.cfg.risk.max_drawdown_kill).astype(float)
        net = net * live

        return BacktestResult(trades=trade_df, returns=net, metrics=summarize(net, trade_df, self.cfg.periods_per_year))
