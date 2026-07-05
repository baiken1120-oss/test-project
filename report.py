# ============================================
# report.py
# ============================================

import os
import pandas as pd

from config import INITIAL_CAPITAL


class Report:

    def __init__(self, result_path):

        self.result_path = result_path

    ##########################################################

    def create_summary(self, trade_log):

        summary = {}

        initial_asset = float(trade_log.iloc[0]["Asset"])
        final_asset = float(trade_log.iloc[-1]["Asset"])
        extra_funding = float(trade_log.iloc[-1].get("Extra_Funding", 0.0))

        summary["初期投入額"] = INITIAL_CAPITAL
        summary["初期建付後資産"] = initial_asset
        summary["終了資産"] = final_asset

        # 実際に外から入れた資金を基準にした損益。
        # Ver1.0では追加資金を使わない方針だが、検証用に控除する。
        summary["投入額基準総損益"] = final_asset - INITIAL_CAPITAL - extra_funding

        # バックテストログ上の開始時点からの差分。
        # 初期建付け後資産にはミニ株コスト等が反映される。
        summary["ログ期間損益"] = final_asset - initial_asset

        summary["実現利益"] = float(trade_log.iloc[-1]["Realized"])

        summary["評価利益"] = (
            float(trade_log.iloc[-1]["1329_Eval"])
            +
            float(trade_log.iloc[-1]["JT_Eval"])
        )

        summary["追加資金"] = extra_funding

        trade_rows = trade_log[trade_log["Reason"] != "INIT"]

        summary["売買回数"] = len(trade_rows[trade_rows["Execute"] == True])

        summary["GO回数"] = len(trade_rows[trade_rows["Reason"] == "GO"])

        summary["1329回復リバランス回数"] = len(
            trade_rows[trade_rows["Reason"] == "1329回復リバランス"]
        )

        summary["1329回復待ち回数"] = len(
            trade_rows[trade_rows["Reason"] == "1329回復待ち"]
        )

        summary["STAY回数"] = len(trade_rows[trade_rows["Execute"] == False])

        ##################################################

        peak = trade_log["Asset"].cummax()

        dd = trade_log["Asset"] - peak

        summary["最大DD"] = dd.min()

        ##################################################

        df = pd.DataFrame(

            summary.items(),

            columns=["項目", "値"]

        )

        os.makedirs(

            self.result_path,

            exist_ok=True

        )

        df.to_csv(

            os.path.join(

                self.result_path,

                "summary.csv"

            ),

            index=False,

            encoding="utf-8-sig"

        )

        return df

    ##########################################################


    ##########################################################

    def create_yearly_performance(self, trade_log):

        df = trade_log.copy()
        df["Date_dt"] = pd.to_datetime(df["Date"])
        df["Year"] = df["Date_dt"].dt.year

        rows = []
        for year, g in df.groupby("Year"):
            first = g.iloc[0]
            last = g.iloc[-1]
            start_asset = float(first["Asset"])
            end_asset = float(last["Asset"])
            profit = end_asset - start_asset
            ret = profit / start_asset if start_asset else 0
            peak = g["Asset"].cummax()
            max_dd = (g["Asset"] - peak).min()
            rows.append({
                "Year": int(year),
                "StartDate": first["Date"],
                "EndDate": last["Date"],
                "StartAsset": start_asset,
                "EndAsset": end_asset,
                "Profit": profit,
                "Return": ret,
                "MaxDD": max_dd,
                "Trades": int((g["Execute"] == True).sum()),
                "GO": int((g["Reason"] == "GO").sum()),
                "RecoveryRebalance": int((g["Reason"] == "1329回復リバランス").sum()),
                "RecoveryWait": int((g["Reason"] == "1329回復待ち").sum()),
            })

        out = pd.DataFrame(rows)
        out.to_csv(
            os.path.join(self.result_path, "yearly_performance.csv"),
            index=False,
            encoding="utf-8-sig",
        )
        return out

    ##########################################################

    def create_benchmark_comparison(self, trade_log):

        df = trade_log.copy()
        first = df.iloc[0]

        start_asset = float(first["Asset"])
        start1329 = float(first["Close_1329"])
        startJT = float(first["Close_JT"])

        df["Benchmark_1329_BuyHold"] = start_asset * df["Close_1329"] / start1329
        df["Benchmark_JT_BuyHold"] = start_asset * df["Close_JT"] / startJT
        df["Benchmark_50_50_BuyHold"] = (
            start_asset * 0.5 * df["Close_1329"] / start1329
            + start_asset * 0.5 * df["Close_JT"] / startJT
        )

        last = df.iloc[-1]
        rows = []
        for name, col in [
            ("Strategy", "Asset"),
            ("1329 Buy&Hold", "Benchmark_1329_BuyHold"),
            ("JT Buy&Hold", "Benchmark_JT_BuyHold"),
            ("50:50 Buy&Hold", "Benchmark_50_50_BuyHold"),
        ]:
            final_asset = float(last[col])
            rows.append({
                "Name": name,
                "StartAsset": start_asset,
                "FinalAsset": final_asset,
                "Profit": final_asset - start_asset,
                "Return": final_asset / start_asset - 1 if start_asset else 0,
            })

        out = pd.DataFrame(rows)
        out.to_csv(
            os.path.join(self.result_path, "benchmark_comparison.csv"),
            index=False,
            encoding="utf-8-sig",
        )

        df[[
            "Date",
            "Asset",
            "Benchmark_1329_BuyHold",
            "Benchmark_JT_BuyHold",
            "Benchmark_50_50_BuyHold",
        ]].to_csv(
            os.path.join(self.result_path, "benchmark_daily.csv"),
            index=False,
            encoding="utf-8-sig",
        )

        return out

    ##########################################################


    ##########################################################

    def create_position_diagnostics(self, trade_log):

        df = trade_log.copy()
        df["Date_dt"] = pd.to_datetime(df["Date"])

        first_zero_1329 = df[df["1329_Qty_Hold"] <= 0]
        first_zero_jt = df[df["JT_Qty_Hold"] <= 0]

        rows = []
        rows.append({
            "項目": "1329初回枯渇日",
            "値": first_zero_1329.iloc[0]["Date"] if len(first_zero_1329) else "未発生",
        })
        rows.append({
            "項目": "JT初回枯渇日",
            "値": first_zero_jt.iloc[0]["Date"] if len(first_zero_jt) else "未発生",
        })
        rows.append({
            "項目": "1329枯渇日数",
            "値": int((df["1329_Qty_Hold"] <= 0).sum()),
        })
        rows.append({
            "項目": "JT枯渇日数",
            "値": int((df["JT_Qty_Hold"] <= 0).sum()),
        })
        rows.append({
            "項目": "最終1329比率",
            "値": float(df.iloc[-1]["1329_Ratio"]),
        })
        rows.append({
            "項目": "最終JT比率",
            "値": float(df.iloc[-1]["JT_Ratio"]),
        })
        rows.append({
            "項目": "最大JT比率",
            "値": float(df["JT_Ratio"].max()),
        })
        rows.append({
            "項目": "最大1329比率",
            "値": float(df["1329_Ratio"].max()),
        })

        no_trade = df[(df["Reason"] == "約定なし") & (df["1329_Action"] == "SELL")]
        rows.append({
            "項目": "1329枯渇によるSELL約定なし疑い日数",
            "値": int((no_trade["1329_Qty_Hold"] <= 0).sum()),
        })

        out = pd.DataFrame(rows)
        out.to_csv(
            os.path.join(self.result_path, "position_diagnostics.csv"),
            index=False,
            encoding="utf-8-sig",
        )

        yearly = []
        for year, g in df.groupby(df["Date_dt"].dt.year):
            yearly.append({
                "Year": int(year),
                "Avg1329Ratio": float(g["1329_Ratio"].mean()),
                "AvgJTRatio": float(g["JT_Ratio"].mean()),
                "End1329Ratio": float(g.iloc[-1]["1329_Ratio"]),
                "EndJTRatio": float(g.iloc[-1]["JT_Ratio"]),
                "End1329Qty": int(g.iloc[-1]["1329_Qty_Hold"]),
                "EndJTQty": int(g.iloc[-1]["JT_Qty_Hold"]),
                "NoTrade": int((g["Reason"] == "約定なし").sum()),
                "OshoFilter": int((g["Reason"] == "王将フィルター").sum()),
                "DeadZone": int((g["Reason"] == "デッドゾーン").sum()),
            })

        yearly_out = pd.DataFrame(yearly)
        yearly_out.to_csv(
            os.path.join(self.result_path, "position_yearly.csv"),
            index=False,
            encoding="utf-8-sig",
        )

        return out, yearly_out

    ##########################################################

    def print_position_diagnostics(self, diagnostics):
        print("========== ポジション診断 ==========")
        print(diagnostics.to_string(index=False))
        print("==================================")

    def print_yearly_performance(self, yearly):
        print("========== 年度別成績 ==========")
        print(yearly.to_string(index=False))
        print("==============================")

    ##########################################################

    def print_benchmark_comparison(self, benchmark):
        print("========== ベンチマーク比較 ==========")
        print(benchmark.to_string(index=False))
        print("====================================")

    def print_summary(self, summary):

        print("========== 結果 ==========")

        for _, row in summary.iterrows():

            print(f"{row['項目']} : {row['値']}")

        print("==========================")
