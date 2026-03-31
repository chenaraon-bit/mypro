from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

import httpx
import pandas as pd


@dataclass
class BinanceDataSource:
    spot_base_url: str = "https://api.binance.com"
    futures_base_url: str = "https://fapi.binance.com"

    def fetch_klines(self, symbol: str, interval: str, start_ms: int, end_ms: int, limit: int = 1000) -> pd.DataFrame:
        url = f"{self.spot_base_url}/api/v3/klines"
        rows: List[List[Any]] = []
        cur = start_ms
        with httpx.Client(timeout=20) as client:
            while cur < end_ms:
                r = client.get(url, params={"symbol": symbol, "interval": interval, "startTime": cur, "endTime": end_ms, "limit": limit})
                r.raise_for_status()
                data = r.json()
                if not data:
                    break
                rows.extend(data)
                nxt = int(data[-1][0]) + 1
                if nxt <= cur:
                    break
                cur = nxt
        df = pd.DataFrame(rows, columns=["open_time","open","high","low","close","volume","close_time","qv","n","tb","tq","ignore"])
        for c in ["open","high","low","close","volume"]:
            df[c] = pd.to_numeric(df[c], errors="coerce")
        df["open_time"] = pd.to_datetime(df["open_time"], unit="ms", utc=True)
        return df

    def fetch_funding_rates(self, symbol: str, start_ms: int, end_ms: int, limit: int = 1000) -> pd.DataFrame:
        url = f"{self.futures_base_url}/fapi/v1/fundingRate"
        rows: List[Dict[str, Any]] = []
        cur = start_ms
        with httpx.Client(timeout=20) as client:
            while cur < end_ms:
                r = client.get(url, params={"symbol": symbol, "startTime": cur, "endTime": end_ms, "limit": limit})
                r.raise_for_status()
                data = r.json()
                if not data:
                    break
                rows.extend(data)
                nxt = int(data[-1]["fundingTime"]) + 1
                if nxt <= cur:
                    break
                cur = nxt
        df = pd.DataFrame(rows)
        if not df.empty:
            df["fundingRate"] = pd.to_numeric(df["fundingRate"], errors="coerce")
            df["fundingTime"] = pd.to_numeric(df["fundingTime"], errors="coerce")
        return df
