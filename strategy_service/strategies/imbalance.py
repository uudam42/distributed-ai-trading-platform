from __future__ import annotations

import numpy as np
import pandas as pd


def run_strategy(df: pd.DataFrame) -> dict:
    df = df.copy()
    df['imbalance'] = (df['bid_size'] - df['ask_size']) / (df['bid_size'] + df['ask_size']).replace(0, np.nan)
    df['mid'] = (df['bid_price'] + df['ask_price']) / 2.0
    df['signal'] = 0
    df.loc[df['imbalance'] > 0.2, 'signal'] = 1
    df.loc[df['imbalance'] < -0.2, 'signal'] = -1
    df['position'] = df['signal'].replace(to_replace=0, method='ffill').fillna(0)
    df['returns'] = df['mid'].diff().fillna(0)
    df['pnl_stream'] = df['position'].shift(1).fillna(0) * df['returns']
    trades = (df['position'].diff().fillna(0) != 0).sum()
    fills = (df['signal'] != 0).sum()
    fill_ratio = float(fills / len(df)) if len(df) else 0.0
    inventory_exposure = float(df['position'].abs().mean()) if len(df) else 0.0
    return {
        'pnl': float(df['pnl_stream'].sum()),
        'number_of_trades': int(trades),
        'fill_ratio': fill_ratio,
        'inventory_exposure': inventory_exposure,
    }
