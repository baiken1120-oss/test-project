# ============================================
# data_loader.py
# Ver2.0.0: 10年CSV対応用の共通データ読み込み
# ============================================

import os
import pandas as pd

from config import DATA_PATH, FILE_1329, FILE_JT


def _to_number(series):
    """CSV内のカンマ、空白、'-' を吸収して数値化する。"""
    return pd.to_numeric(
        series.astype(str)
        .str.replace(",", "", regex=False)
        .str.replace("−", "-", regex=False)
        .str.strip()
        .replace({"-": "0", "": "0", "nan": "0"}),
        errors="coerce",
    )


def _load_price_csv(filename):
    df = pd.read_csv(os.path.join(DATA_PATH, filename), encoding="utf-8-sig")

    df = df.rename(columns={
        "日付": "Date",
        "終値": "Close",
        "前日比": "Diff",
    })

    required = ["Date", "Close", "Diff"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"{filename} に必要列がありません: {missing}")

    df = df[required].copy()
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df["Close"] = _to_number(df["Close"])
    df["Diff"] = _to_number(df["Diff"])

    df = df.dropna(subset=["Date", "Close", "Diff"])
    df = df[df["Close"] > 0]
    df = df.sort_values("Date")
    df = df.drop_duplicates(subset=["Date"], keep="last")

    return df


def load_merged_price_data():
    df1329 = _load_price_csv(FILE_1329)
    dfJT = _load_price_csv(FILE_JT)

    df = pd.merge(
        df1329,
        dfJT,
        on="Date",
        suffixes=("_1329", "_JT"),
    )

    df = df.sort_values("Date").reset_index(drop=True)
    df["Year"] = df["Date"].dt.year
    df["Date"] = df["Date"].dt.strftime("%Y/%m/%d")

    return df
