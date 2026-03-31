from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class MarketEvent:
    ts_ms: int
    symbol: str
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass
class SignalEvent:
    ts_ms: int
    symbol: str
    direction: int  # -1,0,1
    strength: float = 1.0
    meta: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OrderEvent:
    ts_ms: int
    symbol: str
    side: str  # BUY/SELL
    qty: float
    order_type: str = "MARKET"
    limit_price: Optional[float] = None


@dataclass
class FillEvent:
    ts_ms: int
    symbol: str
    side: str
    qty: float
    price: float
    fee: float
    slippage: float
