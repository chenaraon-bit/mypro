"""Crypto trading research framework (v2).

Upgrades over MVP:
- Cost model includes fee tier + slippage impact term + latency penalty.
- Risk layer includes volatility targeting, leverage cap, position cap, stop-loss,
  and portfolio-level drawdown kill switch.
- Walk-forward supports train-time parameter selection (simple grid search) and
  test-time out-of-sample evaluation.
- Report export (metrics json + trades/equity csv).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple
import json

import numpy as np
import pandas as pd


@dataclass
class MarketConfig:
    maker_fee_bps: float = 2.0
    taker_fee_bps: float = 6.0
    slippage_bps: float = 3.0
    impact_coeff: float = 0.15  # extra bps per 1.0 turnover * realized vol
    latency_bps: float = 0.5
    use_taker: bool = True


@dataclass
class RiskConfig:
    target_vol: float = 0.25
    max_leverage: float = 2.0
    max_abs_position: float = 2.0
    stop_loss: float = 0.03
    max_drawdown_kill: float = 0.25


@dataclass
class BacktestConfig:
    annualization: int = 365
    initial_capital: float = 1.0
    market: MarketConfig = field(default_factory=MarketConfig)
    risk: RiskConfig = field(default_factory=RiskConfig)


@dataclass
class BacktestResult:
    equity_curve: pd.Series
    trades: pd.DataFrame
    metrics: dict
    params: dict


def load_ohlcv_csv(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    required = {"timestamp", "open", "high", "low", "close", "volume"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    return (
        df.sort_values("timestamp")
        .drop_duplicates("timestamp")
        .set_index("timestamp")
        [["open", "high", "low", "close", "volume"]]
    )


def generate_signals(df: pd.DataFrame, fast: int = 20, slow: int = 100, mode: str = "trend") -> pd.Series:
    close = df["close"]
    if mode == "trend":
        fast_ma = close.rolling(fast).mean()
        slow_ma = close.rolling(slow).mean()
        raw = np.where(fast_ma > slow_ma, 1.0, -1.0)
    elif mode == "mean_reversion":
        ma = close.rolling(slow).mean()
        z = (close - ma) / close.rolling(slow).std().replace(0, np.nan)
        raw = np.where(z > 1.0, -1.0, np.where(z < -1.0, 1.0, 0.0))
    else:
        raise ValueError("mode must be one of: trend, mean_reversion")

    signal = pd.Series(raw, index=df.index).replace([np.inf, -np.inf], np.nan).fillna(0.0)
    return signal


def volatility_targeted_position(returns: pd.Series, signal: pd.Series, cfg: BacktestConfig, lookback: int = 48) -> pd.Series:
    realized_vol = returns.rolling(lookback).std() * np.sqrt(cfg.annualization)
    scaled = cfg.risk.target_vol / realized_vol.replace(0.0, np.nan)
    scaled = scaled.replace([np.inf, -np.inf], np.nan).fillna(0.0)
    pos = (signal * scaled).clip(-cfg.risk.max_leverage, cfg.risk.max_leverage)
    return pos.clip(-cfg.risk.max_abs_position, cfg.risk.max_abs_position)


def compute_drawdown(equity: pd.Series) -> pd.Series:
    peak = equity.cummax()
    return (equity / peak) - 1.0


def execution_cost(turnover: pd.Series, realized_vol: pd.Series, cfg: BacktestConfig) -> pd.Series:
    fee_bps = cfg.market.taker_fee_bps if cfg.market.use_taker else cfg.market.maker_fee_bps
    fee = turnover * (fee_bps / 10_000.0)

    base_slippage = turnover * (cfg.market.slippage_bps / 10_000.0)
    impact_slippage = turnover * realized_vol.fillna(0.0) * (cfg.market.impact_coeff / 10_000.0)
    latency_penalty = turnover * (cfg.market.latency_bps / 10_000.0)
    return fee + base_slippage + impact_slippage + latency_penalty


def apply_risk_controls(net: pd.Series, cfg: BacktestConfig) -> pd.Series:
    net = net.clip(lower=-cfg.risk.stop_loss)
    equity = (1.0 + net).cumprod()
    dd = compute_drawdown(equity)
    # kill-switch: flatten risk after severe drawdown
    live_mask = (dd > -cfg.risk.max_drawdown_kill).astype(float)
    return net * live_mask


def performance_metrics(equity: pd.Series, returns: pd.Series, trades: pd.DataFrame, annualization: int) -> dict:
    total_return = float(equity.iloc[-1] / equity.iloc[0] - 1.0)
    ann_return = float((equity.iloc[-1] / equity.iloc[0]) ** (annualization / max(1, len(returns))) - 1.0)
    ann_vol = float(returns.std() * np.sqrt(annualization))
    sharpe = ann_return / ann_vol if ann_vol > 0 else 0.0

    dd = compute_drawdown(equity)
    mdd = float(dd.min())
    calmar = ann_return / abs(mdd) if mdd < 0 else 0.0

    downside = returns[returns < 0].std() * np.sqrt(annualization)
    sortino = float(ann_return / downside) if downside and downside > 0 else 0.0

    win_rate = float((trades["pnl"] > 0).mean()) if len(trades) else 0.0
    avg_win = float(trades.loc[trades["pnl"] > 0, "pnl"].mean()) if (trades["pnl"] > 0).any() else 0.0
    avg_loss = float(-trades.loc[trades["pnl"] < 0, "pnl"].mean()) if (trades["pnl"] < 0).any() else 0.0
    expectancy = win_rate * avg_win - (1 - win_rate) * avg_loss

    return {
        "total_return": total_return,
        "annualized_return": ann_return,
        "annualized_volatility": ann_vol,
        "sharpe": sharpe,
        "sortino": sortino,
        "calmar": calmar,
        "max_drawdown": mdd,
        "win_rate": win_rate,
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "expectancy": expectancy,
        "num_trades": int(len(trades)),
    }


def backtest(df: pd.DataFrame, cfg: BacktestConfig, fast: int = 20, slow: int = 100, mode: str = "trend") -> BacktestResult:
    rets = df["close"].pct_change().fillna(0.0)
    signal = generate_signals(df, fast=fast, slow=slow, mode=mode)
    pos = volatility_targeted_position(rets, signal, cfg).shift(1).fillna(0.0)
    turnover = pos.diff().abs().fillna(0.0)
    realized_vol = rets.rolling(48).std() * np.sqrt(cfg.annualization)

    gross = pos * rets
    costs = execution_cost(turnover, realized_vol, cfg)
    net = apply_risk_controls(gross - costs, cfg)

    equity = cfg.initial_capital * (1.0 + net).cumprod()

    trades = pd.DataFrame(
        {
            "timestamp": df.index,
            "position": pos.values,
            "turnover": turnover.values,
            "gross": gross.values,
            "cost": costs.values,
            "pnl": net.values,
            "equity": equity.values,
        }
    )
    executed = trades[trades["turnover"] > 0].copy()

    metrics = performance_metrics(equity, net, executed, cfg.annualization)
    params = {"fast": fast, "slow": slow, "mode": mode}
    return BacktestResult(equity_curve=equity, trades=executed, metrics=metrics, params=params)


def walk_forward_splits(n: int, train_size: int, test_size: int, step: int) -> Iterable[Tuple[slice, slice]]:
    start = 0
    while start + train_size + test_size <= n:
        yield slice(start, start + train_size), slice(start + train_size, start + train_size + test_size)
        start += step


def _select_params(train_df: pd.DataFrame, cfg: BacktestConfig, grid: Sequence[Tuple[int, int]], mode: str) -> Tuple[int, int]:
    best_pair = grid[0]
    best_score = -np.inf
    for fast, slow in grid:
        if fast >= slow:
            continue
        res = backtest(train_df, cfg, fast=fast, slow=slow, mode=mode)
        score = res.metrics["sharpe"]
        if np.isfinite(score) and score > best_score:
            best_score = score
            best_pair = (fast, slow)
    return best_pair


def walk_forward_evaluate(
    df: pd.DataFrame,
    cfg: BacktestConfig,
    mode: str = "trend",
    train_size: int = 500,
    test_size: int = 200,
    step: int = 200,
    param_grid: Sequence[Tuple[int, int]] | None = None,
) -> pd.DataFrame:
    if param_grid is None:
        param_grid = [(10, 50), (20, 100), (30, 150)]

    rows: List[dict] = []
    for i, (tr, te) in enumerate(walk_forward_splits(len(df), train_size, test_size, step), start=1):
        train_df = df.iloc[tr]
        test_df = df.iloc[te]
        if len(test_df) < 50:
            continue

        fast, slow = _select_params(train_df, cfg, param_grid, mode)
        oos = backtest(test_df, cfg, fast=fast, slow=slow, mode=mode)

        row = {"fold": i, "selected_fast": fast, "selected_slow": slow}
        row.update(oos.metrics)
        rows.append(row)
    return pd.DataFrame(rows)


def export_report(output_dir: str, run_name: str, result: BacktestResult, wf: pd.DataFrame | None, cfg: BacktestConfig) -> None:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    equity_path = out / f"{run_name}_equity.csv"
    trades_path = out / f"{run_name}_trades.csv"
    metrics_path = out / f"{run_name}_metrics.json"
    wf_path = out / f"{run_name}_walk_forward.csv"

    result.equity_curve.rename("equity").to_csv(equity_path)
    result.trades.to_csv(trades_path, index=False)

    payload = {
        "metrics": result.metrics,
        "params": result.params,
        "config": {
            "annualization": cfg.annualization,
            "initial_capital": cfg.initial_capital,
            "market": asdict(cfg.market),
            "risk": asdict(cfg.risk),
        },
    }
    metrics_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    if wf is not None and not wf.empty:
        wf.to_csv(wf_path, index=False)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Crypto strategy backtester (cost/risk/walk-forward)")
    parser.add_argument("--csv", required=True, help="Path to OHLCV csv")
    parser.add_argument("--mode", default="trend", choices=["trend", "mean_reversion"])
    parser.add_argument("--fast", type=int, default=20)
    parser.add_argument("--slow", type=int, default=100)
    parser.add_argument("--taker-fee-bps", type=float, default=6.0)
    parser.add_argument("--maker-fee-bps", type=float, default=2.0)
    parser.add_argument("--slippage-bps", type=float, default=3.0)
    parser.add_argument("--impact-coeff", type=float, default=0.15)
    parser.add_argument("--latency-bps", type=float, default=0.5)
    parser.add_argument("--target-vol", type=float, default=0.25)
    parser.add_argument("--max-leverage", type=float, default=2.0)
    parser.add_argument("--max-position", type=float, default=2.0)
    parser.add_argument("--stop-loss", type=float, default=0.03)
    parser.add_argument("--kill-dd", type=float, default=0.25)
    parser.add_argument("--output-dir", default="outputs")
    parser.add_argument("--run-name", default="baseline")
    args = parser.parse_args()

    cfg = BacktestConfig(
        market=MarketConfig(
            maker_fee_bps=args.maker_fee_bps,
            taker_fee_bps=args.taker_fee_bps,
            slippage_bps=args.slippage_bps,
            impact_coeff=args.impact_coeff,
            latency_bps=args.latency_bps,
        ),
        risk=RiskConfig(
            target_vol=args.target_vol,
            max_leverage=args.max_leverage,
            max_abs_position=args.max_position,
            stop_loss=args.stop_loss,
            max_drawdown_kill=args.kill_dd,
        ),
    )

    data = load_ohlcv_csv(args.csv)
    result = backtest(data, cfg, fast=args.fast, slow=args.slow, mode=args.mode)
    wf = walk_forward_evaluate(data, cfg, mode=args.mode)

    print("=== Backtest Metrics ===")
    for k, v in result.metrics.items():
        print(f"{k}: {v:.6f}" if isinstance(v, float) else f"{k}: {v}")

    if not wf.empty:
        print("\n=== Walk-Forward Mean Metrics ===")
        print(wf.mean(numeric_only=True).to_string())

    export_report(args.output_dir, args.run_name, result, wf, cfg)
    print(f"\nSaved report to: {args.output_dir}")
