"""Prometheus metrics for MemeX."""

from prometheus_client import Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST

# Business metrics
ACTIVE_POSITIONS = Gauge("memex_active_positions", "Number of open positions")
TOTAL_PNL_24H = Gauge("memex_total_pnl_24h_usd", "Total PnL in last 24 hours (USD)")
WIN_RATE_24H = Gauge("memex_win_rate_24h", "Win rate in last 24 hours (percent)")
SIGNALS_GENERATED = Counter("memex_signals_generated_total", "Total signals generated", ["signal_type"])
TRADES_EXECUTED = Counter("memex_trades_executed_total", "Total trades executed", ["trade_type", "mode"])

# Technical metrics
API_REQUEST_DURATION = Histogram(
    "memex_api_request_duration_seconds",
    "API request duration",
    ["method", "endpoint"],
)
WORKER_JOB_DURATION = Histogram(
    "memex_worker_job_duration_seconds",
    "Worker job duration",
    ["worker_name"],
)
DEX_API_DURATION = Histogram("memex_dex_api_duration_seconds", "DEX Screener API call duration")
PREDICTION_DURATION = Histogram("memex_prediction_duration_seconds", "ML prediction inference time")


def metrics_response():
    return generate_latest(), CONTENT_TYPE_LATEST
