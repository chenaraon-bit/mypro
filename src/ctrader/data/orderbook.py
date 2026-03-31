from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class OrderBookL2:
    bids: Dict[float, float] = field(default_factory=dict)
    asks: Dict[float, float] = field(default_factory=dict)
    last_update_id: Optional[int] = None

    def apply_snapshot(self, bids: List[Tuple[float, float]], asks: List[Tuple[float, float]], update_id: Optional[int] = None) -> None:
        self.bids = {float(p): float(s) for p, s in bids if float(s) > 0}
        self.asks = {float(p): float(s) for p, s in asks if float(s) > 0}
        self.last_update_id = update_id

    def apply_delta(self, bids: List[Tuple[float, float]], asks: List[Tuple[float, float]], update_id: Optional[int] = None) -> None:
        for p, s in bids:
            p, s = float(p), float(s)
            if s <= 0:
                self.bids.pop(p, None)
            else:
                self.bids[p] = s
        for p, s in asks:
            p, s = float(p), float(s)
            if s <= 0:
                self.asks.pop(p, None)
            else:
                self.asks[p] = s
        if update_id is not None:
            self.last_update_id = update_id

    def best_bid(self):
        return None if not self.bids else (max(self.bids), self.bids[max(self.bids)])

    def best_ask(self):
        return None if not self.asks else (min(self.asks), self.asks[min(self.asks)])
