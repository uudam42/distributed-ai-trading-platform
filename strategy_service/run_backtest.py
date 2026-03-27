#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json

from strategy_service.app.runner import run_backtest


def main():
    parser = argparse.ArgumentParser(description='Run hftbacktest-backed strategy research backtest')
    parser.add_argument('--dataset', required=True, help='Path to CSV dataset with bid/ask prices and sizes')
    parser.add_argument('--strategy', default='imbalance', choices=['imbalance', 'mean_reversion'], help='Strategy name')
    parser.add_argument('--csv', action='store_true', help='Also export CSV report')
    args = parser.parse_args()

    result = run_backtest(args.dataset, args.strategy, csv_export=args.csv)
    print(json.dumps(result.model_dump(mode='json'), indent=2))


if __name__ == '__main__':
    main()
