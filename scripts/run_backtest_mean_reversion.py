import argparse
import pandas as pd

from ctrader.backtest.engine import BacktestEngine
from ctrader.config import BacktestConfig
from ctrader.strategies.mean_reversion import make_signal


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)
    ap.add_argument("--window", type=int, default=50)
    args = ap.parse_args()

    df = pd.read_csv(args.csv)
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    df = df.set_index("timestamp").sort_index()

    eng = BacktestEngine(BacktestConfig())
    res = eng.run(df, make_signal(window=args.window))
    print(res.metrics)


if __name__ == "__main__":
    main()
