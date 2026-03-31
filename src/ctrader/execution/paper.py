from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class PaperFill:
    ts: str
    symbol: str
    side: str
    qty: float
    price: float
    fee: float


@dataclass
class PaperBroker:
    """Simple paper trading broker for simulation account execution.

    - No real exchange orders are sent.
    - Maintains cash, position and realized PnL locally.
    """

    starting_cash: float = 10000.0
    fee_bps: float = 5.0
    cash: float = field(init=False)
    positions: Dict[str, float] = field(default_factory=dict)
    avg_price: Dict[str, float] = field(default_factory=dict)
    realized_pnl: float = 0.0
    fills: List[PaperFill] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.cash = self.starting_cash

    def place_market_order(self, ts: str, symbol: str, side: str, qty: float, price: float) -> PaperFill:
        notional = qty * price
        fee = notional * (self.fee_bps / 10000.0)

        pos = self.positions.get(symbol, 0.0)
        avg = self.avg_price.get(symbol, 0.0)

        if side.upper() == "BUY":
            self.cash -= notional + fee
            new_pos = pos + qty
            self.avg_price[symbol] = ((pos * avg) + (qty * price)) / new_pos if new_pos != 0 else 0.0
            self.positions[symbol] = new_pos
        else:
            self.cash += notional - fee
            close_qty = min(abs(pos), qty)
            if pos > 0:
                self.realized_pnl += close_qty * (price - avg)
            elif pos < 0:
                self.realized_pnl += close_qty * (avg - price)
            self.positions[symbol] = pos - qty

        fill = PaperFill(ts=ts, symbol=symbol, side=side.upper(), qty=qty, price=price, fee=fee)
        self.fills.append(fill)
        return fill

    def equity(self, mark_prices: Dict[str, float]) -> float:
        pnl_unreal = 0.0
        for sym, pos in self.positions.items():
            m = mark_prices.get(sym)
            if m is None:
                continue
            pnl_unreal += pos * (m - self.avg_price.get(sym, m))
        return self.cash + pnl_unreal
