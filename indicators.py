import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings('ignore')


def exponential_moving_average(df, base='close_total', target='ema', period=21, alpha=False):
    con = pd.concat([df[:period][base].rolling(window=period).mean(), df[period:][base]])
    if alpha:
        df[target] = con.ewm(alpha=1 / period, adjust=False).mean()
    else:
        df[target] = con.ewm(span=period, adjust=False).mean()
    df[target].fillna(0, inplace=True)
    return df


def average_true_range(df, period):
    ohlc = ['open_total', 'high_total', 'low_total', 'close_total']
    atr = 'atr_' + str(period)
    if 'TR' not in df.columns:
        df['h-l'] = df[ohlc[1]] - df[ohlc[2]]
        df['h-yc'] = abs(df[ohlc[1]] - df[ohlc[3]].shift())
        df['l-yc'] = abs(df[ohlc[2]] - df[ohlc[3]].shift())

        df['TR'] = df[['h-l', 'h-yc', 'l-yc']].max(axis=1)

        df.drop(['h-l', 'h-yc', 'l-yc'], inplace=True, axis=1)

    # Compute EMA of true range using ATR formula after ignoring first row
    exponential_moving_average(df, 'TR', atr, period, alpha=True)


def super_trend(df, period=10, atr_multiplier=3, sp_val='sp_val', sp_dir='sp_dir'):
    ohlc = ['open_total', 'high_total', 'low_total', 'close_total']
    average_true_range(df, period)
    atr = 'atr_' + str(period)

    # Compute basic upper and low_totaler bands
    df['basic_ub'] = (df[ohlc[1]] + df[ohlc[2]]) / 2 + atr_multiplier * df[atr]
    df['basic_lb'] = (df[ohlc[1]] + df[ohlc[2]]) / 2 - atr_multiplier * df[atr]

    # Compute final upper and low_totaler bands
    df['final_ub'] = 0.00
    df['final_lb'] = 0.00
    for i in range(period, len(df)):
        df['final_ub'].iat[i] = df['basic_ub'].iat[i] if df['basic_ub'].iat[i] < df['final_ub'].iat[i - 1] or \
                                                         df[ohlc[3]].iat[i - 1] > df['final_ub'].iat[i - 1] else \
            df['final_ub'].iat[i - 1]
        df['final_lb'].iat[i] = df['basic_lb'].iat[i] if df['basic_lb'].iat[i] > df['final_lb'].iat[i - 1] or \
                                                         df[ohlc[3]].iat[i - 1] < df['final_lb'].iat[i - 1] else \
            df['final_lb'].iat[i - 1]

    # Set the Supertrend value
    df[sp_val] = 0.00
    for i in range(period, len(df)):
        df[sp_val].iat[i] = df['final_ub'].iat[i] if df[sp_val].iat[i - 1] == df['final_ub'].iat[i - 1] and \
                                                     df[ohlc[3]].iat[
                                                         i] <= df['final_ub'].iat[i] else \
            df['final_lb'].iat[i] if df[sp_val].iat[i - 1] == df['final_ub'].iat[i - 1] and df[ohlc[3]].iat[i] > \
                                     df['final_ub'].iat[i] else \
                df['final_lb'].iat[i] if df[sp_val].iat[i - 1] == df['final_lb'].iat[i - 1] and df[ohlc[3]].iat[i] >= \
                                         df['final_lb'].iat[i] else \
                    df['final_ub'].iat[i] if df[sp_val].iat[i - 1] == df['final_lb'].iat[i - 1] and df[ohlc[3]].iat[i] < \
                                             df['final_lb'].iat[i] else 0.00

        # Mark the trend direction up/down
    df[sp_dir] = np.where((df[sp_val] > 0.00), np.where((df[ohlc[3]] < df[sp_val]), 'down', 'up'), np.NaN)

    # Remove basic and final bands from the columns
    df.drop(['basic_ub', 'basic_lb', 'final_ub', 'final_lb', f"{atr}", "TR"], inplace=True, axis=1)

    df.fillna(0, inplace=True)

    return df
