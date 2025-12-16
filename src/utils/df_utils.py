# utils/df_utils.py
import pandas as pd

def normalize_df_time(df: pd.DataFrame, col="time", tz="Asia/Ho_Chi_Minh"):
    df[col] = pd.to_datetime(df[col], errors="coerce")

    if df[col].dt.tz is None:
        df[col] = df[col].dt.tz_localize(tz)
    else:
        df[col] = df[col].dt.tz_convert(tz)

    return df

def filter_by_time(df, start_dt, end_dt, col="time"):
    return df[(df[col] >= start_dt) & (df[col] <= end_dt)]
