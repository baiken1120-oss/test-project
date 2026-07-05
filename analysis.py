# ============================================
# analysis.py
# Ver1.1.1: 王将フィルター分析ツール
# ============================================

import os
import pandas as pd

from config import (
    DATA_PATH,
    RESULT_PATH,
    FILE_1329,
    FILE_JT,
    FILE_QUANTITY,
    MINI_STOCK_COST,
    THRESHOLD_CANDIDATES,
    JT_ROUND_LOT,
)
from quantity import QuantityTable
from strategy import Strategy
from data_loader import load_merged_price_data


class OshoAnalyzer:

    def __init__(self):
        self.quantity = QuantityTable(os.path.join(DATA_PATH, FILE_QUANTITY))
        self.strategy = Strategy(self.quantity)

    def load_data(self):
        df = load_merged_price_data()

        df["Pct_1329"] = df.apply(
            lambda r: self.strategy.calc_percent(r["Close_1329"], r["Diff_1329"]),
            axis=1,
        )
        df["Pct_JT"] = df.apply(
            lambda r: self.strategy.calc_percent(r["Close_JT"], r["Diff_JT"]),
            axis=1,
        )
        df["Gap"] = (df["Pct_1329"] - df["Pct_JT"]).abs()

        # 戦略上の基準変動率。売買数量表に渡す値。
        def calc_base(row):
            pct1329 = row["Pct_1329"]
            pctJT = row["Pct_JT"]
            if (pct1329 >= 0 and pctJT >= 0) or (pct1329 <= 0 and pctJT <= 0):
                return pct1329 if abs(pct1329) >= abs(pctJT) else pctJT
            return pct1329

        df["BasePercent"] = df.apply(calc_base, axis=1)
        df["Planned1329Qty"] = df["BasePercent"].abs().apply(self.quantity.get_quantity)
        df["Planned1329Amount"] = df["Planned1329Qty"] * df["Close_1329"]
        df["PlannedJTQty"] = (df["Planned1329Amount"] / df["Close_JT"]).round().astype(int)
        df["JT_MiniQty"] = df["PlannedJTQty"] % JT_ROUND_LOT
        df["JT_MiniAmount"] = df["JT_MiniQty"] * df["Close_JT"]
        df["EstimatedMiniCost"] = df["JT_MiniAmount"] * MINI_STOCK_COST
        df["EstimatedFullCost_Old"] = df["PlannedJTQty"] * df["Close_JT"] * MINI_STOCK_COST
        df["CostSavedByLot"] = df["EstimatedFullCost_Old"] - df["EstimatedMiniCost"]

        return df

    def create_gap_distribution(self, df):
        gap = df["Gap"]
        rows = []
        rows.append({"項目": "件数", "値": len(gap)})
        rows.append({"項目": "平均", "値": gap.mean()})
        rows.append({"項目": "中央値", "値": gap.median()})
        rows.append({"項目": "標準偏差", "値": gap.std()})
        rows.append({"項目": "最小", "値": gap.min()})
        rows.append({"項目": "最大", "値": gap.max()})
        for q in [0.10, 0.25, 0.50, 0.75, 0.90, 0.95]:
            rows.append({"項目": f"{int(q * 100)}%点", "値": gap.quantile(q)})
        return pd.DataFrame(rows)

    def create_gap_bins(self, df):
        bins = [0, 0.10, 0.20, 0.30, 0.40, 0.50, 0.75, 1.00, 999]
        labels = [
            "0.00-0.10%",
            "0.10-0.20%",
            "0.20-0.30%",
            "0.30-0.40%",
            "0.40-0.50%",
            "0.50-0.75%",
            "0.75-1.00%",
            "1.00%以上",
        ]
        s = pd.cut(df["Gap"], bins=bins, labels=labels, right=False)
        out = s.value_counts().sort_index().reset_index()
        out.columns = ["乖離率帯", "日数"]
        out["比率"] = out["日数"] / len(df)
        return out

    def create_threshold_analysis(self, df):
        rows = []
        for threshold in THRESHOLD_CANDIDATES:
            target = df[df["Gap"] >= threshold]
            rows.append({
                "閾値%": threshold,
                "候補日数": len(target),
                "候補率": len(target) / len(df) if len(df) else 0,
                "平均乖離率%": target["Gap"].mean() if len(target) else 0,
                "中央値乖離率%": target["Gap"].median() if len(target) else 0,
                "平均1329予定口数": target["Planned1329Qty"].mean() if len(target) else 0,
                "平均JT予定株数": target["PlannedJTQty"].mean() if len(target) else 0,
                "平均JT端数株": target["JT_MiniQty"].mean() if len(target) else 0,
                "100株未満のみの日数": int((target["PlannedJTQty"] < JT_ROUND_LOT).sum()) if len(target) else 0,
                "端数なし日数": int((target["JT_MiniQty"] == 0).sum()) if len(target) else 0,
                "推定ミニ株コスト合計": target["EstimatedMiniCost"].sum() if len(target) else 0,
                "旧方式コスト合計_全株0.22%": target["EstimatedFullCost_Old"].sum() if len(target) else 0,
                "単元活用による節約額": target["CostSavedByLot"].sum() if len(target) else 0,
            })
        return pd.DataFrame(rows)

    def run(self):
        os.makedirs(RESULT_PATH, exist_ok=True)
        df = self.load_data()

        daily = df[[
            "Date",
            "Close_1329",
            "Diff_1329",
            "Pct_1329",
            "Close_JT",
            "Diff_JT",
            "Pct_JT",
            "Gap",
            "BasePercent",
            "Planned1329Qty",
            "Planned1329Amount",
            "PlannedJTQty",
            "JT_MiniQty",
            "JT_MiniAmount",
            "EstimatedMiniCost",
            "EstimatedFullCost_Old",
            "CostSavedByLot",
        ]]

        distribution = self.create_gap_distribution(df)
        bins = self.create_gap_bins(df)
        thresholds = self.create_threshold_analysis(df)

        daily.to_csv(os.path.join(RESULT_PATH, "daily_gap_analysis.csv"), index=False, encoding="utf-8-sig")
        distribution.to_csv(os.path.join(RESULT_PATH, "gap_distribution.csv"), index=False, encoding="utf-8-sig")
        bins.to_csv(os.path.join(RESULT_PATH, "gap_bins.csv"), index=False, encoding="utf-8-sig")
        thresholds.to_csv(os.path.join(RESULT_PATH, "threshold_analysis.csv"), index=False, encoding="utf-8-sig")

        print("========== 王将フィルター分析 ==========")
        print("乖離率分布")
        print(distribution)
        print("\n閾値別候補日数・コスト")
        print(thresholds[[
            "閾値%",
            "候補日数",
            "候補率",
            "平均乖離率%",
            "平均JT予定株数",
            "平均JT端数株",
            "推定ミニ株コスト合計",
        ]])
        print("=====================================")

        return {
            "daily": daily,
            "distribution": distribution,
            "bins": bins,
            "thresholds": thresholds,
        }
