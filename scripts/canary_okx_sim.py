"""Canary mode for OKX simulated trading using idempotent order manager."""

import argparse
import os

from ctrader.execution.idempotent import IdempotentOrderManager
from ctrader.execution.okx_sim import OKXSimClient, OKXSimConfig


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--inst-id", default="BTC-USDT")
    ap.add_argument("--side", choices=["buy", "sell"], default="buy")
    ap.add_argument("--ord-type", choices=["market", "limit"], default="market")
    ap.add_argument("--sz", default="0.0001", help="tiny canary size")
    ap.add_argument("--td-mode", default="cash")
    ap.add_argument("--px", default=None)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if args.dry_run:
        print({"dry_run": True, "inst_id": args.inst_id, "side": args.side, "sz": args.sz})
        return

    cfg = OKXSimConfig(
        api_key=os.getenv("OKX_API_KEY", ""),
        secret_key=os.getenv("OKX_SECRET_KEY", ""),
        passphrase=os.getenv("OKX_PASSPHRASE", ""),
        simulated=True,
    )
    if not all([cfg.api_key, cfg.secret_key, cfg.passphrase]):
        raise SystemExit("Missing env vars: OKX_API_KEY / OKX_SECRET_KEY / OKX_PASSPHRASE")

    client = OKXSimClient(cfg)
    om = IdempotentOrderManager(client=client, clord_prefix="newCode")

    result = om.place_order_with_retry(
        inst_id=args.inst_id,
        side=args.side,
        ord_type=args.ord_type,
        sz=args.sz,
        td_mode=args.td_mode,
        px=args.px,
    )
    print({"canary_order": result})


if __name__ == "__main__":
    main()
