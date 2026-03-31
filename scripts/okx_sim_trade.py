"""Place a demo order on OKX simulated trading.

Environment variables:
- OKX_API_KEY
- OKX_SECRET_KEY
- OKX_PASSPHRASE

Example:
  export PYTHONPATH=src
  export OKX_API_KEY=***
  export OKX_SECRET_KEY=***
  export OKX_PASSPHRASE=***
  python scripts/okx_sim_trade.py --inst-id BTC-USDT --side buy --ord-type market --sz 0.001
"""

import argparse
import os

from ctrader.execution.okx_sim import OKXSimClient, OKXSimConfig


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--inst-id", required=True)
    ap.add_argument("--side", choices=["buy", "sell"], required=True)
    ap.add_argument("--ord-type", choices=["market", "limit"], default="market")
    ap.add_argument("--sz", required=True)
    ap.add_argument("--td-mode", default="cash")
    ap.add_argument("--px", default=None)
    ap.add_argument("--cl-ord-id", default="newCode")
    ap.add_argument("--ccy", default="USDT")
    args = ap.parse_args()

    api_key = os.getenv("OKX_API_KEY")
    secret_key = os.getenv("OKX_SECRET_KEY")
    passphrase = os.getenv("OKX_PASSPHRASE")
    if not all([api_key, secret_key, passphrase]):
        raise SystemExit("Missing env vars: OKX_API_KEY / OKX_SECRET_KEY / OKX_PASSPHRASE")

    client = OKXSimClient(
        OKXSimConfig(api_key=api_key, secret_key=secret_key, passphrase=passphrase, simulated=True)
    )

    bal = client.get_balance(args.ccy)
    print({"balance": bal})

    order = client.place_order(
        inst_id=args.inst_id,
        side=args.side,
        ord_type=args.ord_type,
        sz=args.sz,
        td_mode=args.td_mode,
        cl_ord_id=args.cl_ord_id,
        px=args.px,
    )
    print({"order": order})


if __name__ == "__main__":
    main()
