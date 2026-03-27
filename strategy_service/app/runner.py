from __future__ import annotations

import asyncio
import csv
import json
from datetime import datetime
from pathlib import Path

import pandas as pd

from .config import settings
from .kafka import publish, start_producer, stop_producer
from .logging_utils import configure_logging, log_kv
from .schemas import BacktestResult
from strategy_service.strategies.imbalance import run_strategy as run_imbalance
from strategy_service.strategies.mean_reversion import run_strategy as run_mean_reversion

TOPIC = 'strategy.backtest.completed.v1'
logger = configure_logging('strategy-runner')


STRATEGIES = {
    'imbalance': run_imbalance,
    'mean_reversion': run_mean_reversion,
}


def load_dataset(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    log_kv(logger, 'StrategyRunner', 'dataset_loaded', path=path, rows=len(df))
    return df


def save_report(result: BacktestResult, csv_export: bool = False) -> str:
    reports_dir = Path(settings.reports_dir)
    reports_dir.mkdir(parents=True, exist_ok=True)
    base = reports_dir / f"{result.strategy_name}-{int(result.timestamp.timestamp())}"
    json_path = base.with_suffix('.json')
    json_path.write_text(json.dumps(result.model_dump(mode='json'), indent=2))
    if csv_export:
        with base.with_suffix('.csv').open('w', newline='') as fh:
            writer = csv.DictWriter(fh, fieldnames=list(result.model_dump(mode='json').keys()))
            writer.writeheader()
            writer.writerow(result.model_dump(mode='json'))
    return str(json_path)


async def publish_result(result: BacktestResult) -> None:
    await start_producer()
    try:
        await publish(TOPIC, result.model_dump(mode='json'), key=str(result.event_id))
        log_kv(logger, 'StrategyRunner', 'publish_success', topic=TOPIC, event_id=result.event_id)
    except Exception as exc:
        log_kv(logger, 'StrategyRunner', 'publish_failed', topic=TOPIC, error=str(exc))
        raise
    finally:
        await stop_producer()


async def run_backtest_async(dataset_path: str, strategy_name: str = 'imbalance', csv_export: bool = False) -> BacktestResult:
    if strategy_name not in STRATEGIES:
        raise ValueError(f'Unknown strategy: {strategy_name}')
    df = load_dataset(dataset_path)
    log_kv(logger, 'StrategyRunner', 'strategy_start', strategy=strategy_name, dataset=dataset_path)
    metrics = STRATEGIES[strategy_name](df)
    result = BacktestResult(
        strategy_name=strategy_name,
        dataset=dataset_path,
        pnl=metrics['pnl'],
        number_of_trades=metrics['number_of_trades'],
        fill_ratio=metrics['fill_ratio'],
        inventory_exposure=metrics['inventory_exposure'],
        report_path='',
        timestamp=datetime.utcnow(),
    )
    report_path = save_report(result, csv_export=csv_export)
    result.report_path = report_path
    log_kv(logger, 'StrategyRunner', 'strategy_complete', strategy=strategy_name, pnl=result.pnl, trades=result.number_of_trades)
    await publish_result(result)
    return result


def run_backtest(dataset_path: str, strategy_name: str = 'imbalance', csv_export: bool = False) -> BacktestResult:
    return asyncio.run(run_backtest_async(dataset_path, strategy_name, csv_export=csv_export))
