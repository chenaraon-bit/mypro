from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Optional

from .events import FillEvent, MarketEvent, OrderEvent
from ..config import BacktestConfig


@dataclass
class SimBroker:
    cfg: BacktestConfig

    def _delay_ms(self) -> int:
        return max(0, int(random.gauss(self.cfg.latency.mean_ms, self.cfg.latency.jitter_ms)))

    def execute(self, order: OrderEvent, bar: MarketEvent) -> Optional[FillEvent]:
        px = bar.open
        if order.order_type == "LIMIT":
            if order.limit_price is None:
                return None
            if not (bar.low <= order.limit_price <= bar.high):
                return None
            px = order.limit_price

        slip = px * (self.cfg.slippage.fixed_bps / 10000.0)
        exec_px = px + slip if order.side == "BUY" else px - slip

        fee_bps = self.cfg.fee.taker_bps if order.order_type == "MARKET" else self.cfg.fee.maker_bps
        fee = exec_px * order.qty * (fee_bps / 10000.0)
        return FillEvent(
            ts_ms=order.ts_ms + self._delay_ms(),
            symbol=order.symbol,
            side=order.side,
            qty=order.qty,
            price=exec_px,
            fee=fee,
            slippage=slip * order.qty,
        )
