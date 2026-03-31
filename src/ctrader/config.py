from dataclasses import dataclass, field


@dataclass
class FeeConfig:
    maker_bps: float = 1.0
    taker_bps: float = 5.0


@dataclass
class SlippageConfig:
    fixed_bps: float = 2.0


@dataclass
class LatencyConfig:
    mean_ms: int = 150
    jitter_ms: int = 50


@dataclass
class RiskConfig:
    max_drawdown_kill: float = 0.25
    leverage: float = 1.0
    maintenance_margin_rate: float = 0.005


@dataclass
class BacktestConfig:
    periods_per_year: int = 365
    initial_capital: float = 10000.0
    fee: FeeConfig = field(default_factory=FeeConfig)
    slippage: SlippageConfig = field(default_factory=SlippageConfig)
    latency: LatencyConfig = field(default_factory=LatencyConfig)
    risk: RiskConfig = field(default_factory=RiskConfig)
