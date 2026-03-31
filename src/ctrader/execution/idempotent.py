from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class RetryConfig:
    max_retries: int = 3
    base_sleep_s: float = 0.4
    backoff: float = 2.0


class IdempotentOrderManager:
    """Adds clOrdId idempotency + retry wrapper around an exchange client."""

    def __init__(self, client: Any, retry_cfg: Optional[RetryConfig] = None, clord_prefix: str = "newCode"):
        self.client = client
        self.retry_cfg = retry_cfg or RetryConfig()
        self.clord_prefix = clord_prefix

    def new_clord_id(self) -> str:
        suffix = uuid.uuid4().hex[:18]
        return f"{self.clord_prefix}-{suffix}"[:32]

    def place_order_with_retry(self, **kwargs: Any) -> Dict[str, Any]:
        kwargs = dict(kwargs)
        kwargs.setdefault("cl_ord_id", self.new_clord_id())

        sleep_s = self.retry_cfg.base_sleep_s
        last_err: Optional[Exception] = None
        for _ in range(self.retry_cfg.max_retries):
            try:
                return self.client.place_order(**kwargs)
            except Exception as exc:  # noqa: BLE001
                last_err = exc
                time.sleep(sleep_s)
                sleep_s *= self.retry_cfg.backoff
        raise RuntimeError(f"place_order failed after retries: {last_err}")
