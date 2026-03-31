"""Read OKX private order stream (simulated/private WS)."""

import argparse
import asyncio
import os

from ctrader.execution.okx_ws_orders import OKXOrderStream, OKXWSConfig


async def _run(limit: int) -> None:
    cfg = OKXWSConfig(
        api_key=os.getenv("OKX_API_KEY", ""),
        secret_key=os.getenv("OKX_SECRET_KEY", ""),
        passphrase=os.getenv("OKX_PASSPHRASE", ""),
        simulated=True,
    )
    if not all([cfg.api_key, cfg.secret_key, cfg.passphrase]):
        raise SystemExit("Missing env vars: OKX_API_KEY / OKX_SECRET_KEY / OKX_PASSPHRASE")

    stream = OKXOrderStream(cfg)
    n = 0
    async for msg in stream.stream_orders():
        print(msg)
        n += 1
        if n >= limit:
            break


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=20)
    args = ap.parse_args()
    asyncio.run(_run(args.limit))


if __name__ == "__main__":
    main()
