from __future__ import annotations

import base64
import hashlib
import hmac
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional



@dataclass
class OKXSimConfig:
    api_key: str
    secret_key: str
    passphrase: str
    base_url: str = "https://www.okx.com"
    timeout_s: float = 15.0
    simulated: bool = True


class OKXSimClient:
    """OKX V5 simulated trading client.

    Uses header `x-simulated-trading: 1` for demo/simulated mode.
    """

    def __init__(self, cfg: OKXSimConfig):
        self.cfg = cfg
        import httpx
        self.client = httpx.Client(base_url=cfg.base_url, timeout=cfg.timeout_s)

    @staticmethod
    def iso_ts() -> str:
        return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")

    @staticmethod
    def sign(secret_key: str, timestamp: str, method: str, request_path: str, body: str) -> str:
        msg = f"{timestamp}{method.upper()}{request_path}{body}".encode("utf-8")
        digest = hmac.new(secret_key.encode("utf-8"), msg, hashlib.sha256).digest()
        return base64.b64encode(digest).decode("utf-8")

    def _headers(self, ts: str, sign: str) -> Dict[str, str]:
        headers = {
            "OK-ACCESS-KEY": self.cfg.api_key,
            "OK-ACCESS-SIGN": sign,
            "OK-ACCESS-TIMESTAMP": ts,
            "OK-ACCESS-PASSPHRASE": self.cfg.passphrase,
            "Content-Type": "application/json",
        }
        if self.cfg.simulated:
            headers["x-simulated-trading"] = "1"
        return headers

    def _request(self, method: str, path: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        body = json.dumps(payload) if payload else ""
        ts = self.iso_ts()
        sig = self.sign(self.cfg.secret_key, ts, method, path, body)
        headers = self._headers(ts, sig)

        if method.upper() == "GET":
            r = self.client.get(path, headers=headers, params=payload)
        else:
            r = self.client.post(path, headers=headers, content=body)
        r.raise_for_status()
        return r.json()

    def get_balance(self, ccy: str = "USDT") -> Dict[str, Any]:
        return self._request("GET", "/api/v5/account/balance", {"ccy": ccy})

    def place_order(
        self,
        inst_id: str,
        side: str,
        ord_type: str,
        sz: str,
        td_mode: str = "cash",
        cl_ord_id: Optional[str] = None,
        px: Optional[str] = None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "instId": inst_id,
            "tdMode": td_mode,
            "side": side,
            "ordType": ord_type,
            "sz": sz,
        }
        if cl_ord_id:
            payload["clOrdId"] = cl_ord_id
        if px is not None:
            payload["px"] = px
        return self._request("POST", "/api/v5/trade/order", payload)
