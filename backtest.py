import os
import pandas as pd

from config import *
from data_loader import load_merged_price_data
from portfolio import Portfolio
from quantity import QuantityTable
from strategy import Strategy, TradeDecision


class BackTester:

    def __init__(self):

        quantity_file = os.path.join(DATA_PATH, FILE_QUANTITY)

        self.quantity = QuantityTable(quantity_file)

        self.strategy = Strategy(self.quantity)

    ##########################################################

    def load_data(self):

        df = load_merged_price_data()

        # Ver1.1: 1329が25日移動平均からどれだけ乖離しているかを計算する。
        # 25営業日分そろうまでは回復リバランス判定を行わない。
        df["1329_MA25"] = df["Close_1329"].rolling(
            window=RECOVERY_MA_WINDOW,
            min_periods=RECOVERY_MA_WINDOW
        ).mean()
        df["1329_Deviation25"] = (
            df["Close_1329"] / df["1329_MA25"] - 1
        )

        return df

    ##########################################################

    def initialize_portfolio(self, first_row):

        portfolio = Portfolio(INITIAL_CAPITAL)

        cash1329 = INITIAL_CAPITAL * INITIAL_RATIO_1329

        cashJT = INITIAL_CAPITAL * INITIAL_RATIO_JT

        qty1329 = int(cash1329 // first_row["Close_1329"])

        qtyJT = int(cashJT // first_row["Close_JT"])

        portfolio.buy1329(
            qty1329,
            first_row["Close_1329"]
        )

        portfolio.buyJT(
            qtyJT,
            first_row["Close_JT"],
            MINI_STOCK_COST
        )

        return portfolio

    ##########################################################

    def is_recovery_watch_mode(self, portfolio):

        if not ENABLE_RECOVERY_REBALANCE:
            return False

        return portfolio.ratioJT() >= RECOVERY_JT_RATIO_THRESHOLD

    ##########################################################

    def is_1329_discounted(self, row):

        ma25 = row.get("1329_MA25")
        deviation = row.get("1329_Deviation25")

        if pd.isna(ma25) or pd.isna(deviation):
            return False

        return deviation <= RECOVERY_1329_DEVIATION_THRESHOLD

    ##########################################################

    def should_recovery_rebalance(self, row, portfolio):

        return (
            self.is_recovery_watch_mode(portfolio)
            and self.is_1329_discounted(row)
        )

    ##########################################################

    def execute_recovery_rebalance(self, row, portfolio):

        price1329 = float(row["Close_1329"])
        priceJT = float(row["Close_JT"])

        before1329 = int(portfolio.position1329.quantity)
        beforeJT = int(portfolio.positionJT.quantity)

        total_asset = portfolio.total_asset
        target1329_value = total_asset * RECOVERY_TARGET_RATIO_1329
        current1329_value = portfolio.position1329.market_value

        executed_1329_qty = 0
        executed_JT_qty = 0

        # 現在の想定ではJT過多から1329を買い戻す用途。
        # ただし将来の検証に備え、1329過多の場合も逆方向に動けるようにしておく。
        diff1329_value = target1329_value - current1329_value

        if diff1329_value > 0:
            # JTを売って1329の買付原資を作る。
            qtyJT_to_sell = int(diff1329_value // (priceJT * (1 - MINI_STOCK_COST))) + 1
            executed_JT_qty = portfolio.sellJT(
                qtyJT_to_sell,
                priceJT,
                MINI_STOCK_COST
            )

            qty1329_to_buy = int(diff1329_value // price1329)
            executed_1329_qty = portfolio.buy1329(
                qty1329_to_buy,
                price1329
            )

        elif diff1329_value < 0:
            # 1329を売ってJTを買う。
            qty1329_to_sell = int(abs(diff1329_value) // price1329)
            executed_1329_qty = portfolio.sell1329(
                qty1329_to_sell,
                price1329
            )

            qtyJT_to_buy = int(abs(diff1329_value) // (priceJT * (1 + MINI_STOCK_COST)))
            executed_JT_qty = portfolio.buyJT(
                qtyJT_to_buy,
                priceJT,
                MINI_STOCK_COST
            )

        return executed_1329_qty, executed_JT_qty

    ##########################################################

    def run(self):

        df = self.load_data()

        first_row = df.iloc[0]
        portfolio = self.initialize_portfolio(first_row)
        portfolio.update_price(first_row["Close_1329"], first_row["Close_JT"])

        logs = []

        # 初期建付け直後の状態もログに残す。
        # これがないと、summaryの「開始資産」が初回売買後になり、
        # 総利益が実際の初期投入額基準とズレる。
        s = portfolio.summary()
        logs.append({
            "Date": first_row["Date"],
            "Execute": False,
            "Reason": "INIT",
            "1329_Action": "INIT",
            "1329_Qty": 0,
            "JT_Action": "INIT",
            "JT_Qty": 0,
            "Year": first_row.get("Year"),
            "Close_1329": first_row["Close_1329"],
            "Close_JT": first_row["Close_JT"],
            "Cash": s["cash"],
            "Asset": s["asset"],
            "Realized": s["realized"],
            "1329_Qty_Hold": s["1329_qty"],
            "1329_Avg": s["1329_avg"],
            "1329_Eval": s["1329_eval"],
            "JT_Qty_Hold": s["JT_qty"],
            "JT_Avg": s["JT_avg"],
            "JT_Eval": s["JT_eval"],
            "1329_Ratio": s["1329_ratio"],
            "JT_Ratio": s["JT_ratio"],
            "Extra_Funding": s["extra_funding"],
            "Total_Fee": s.get("total_fee", 0.0),
            "Pct_1329": 0.0,
            "Pct_JT": 0.0,
            "Gap": 0.0,
            "BasePercent": 0.0,
            "Merit": 0.0,
            "Planned1329Amount": 0.0,
            "PlannedJTAmount": 0.0,
            "JT_MiniQty": 0,
            "1329_MA25": first_row.get("1329_MA25"),
            "1329_Deviation25": first_row.get("1329_Deviation25"),
        })

        ##################################################

        for _, row in df.iloc[1:].iterrows():

            portfolio.update_price(

                row["Close_1329"],

                row["Close_JT"]

            )

            executed_1329_qty = 0
            executed_JT_qty = 0

            daily_pct1329 = self.strategy.calc_percent(row["Close_1329"], row["Diff_1329"])
            daily_pctJT = self.strategy.calc_percent(row["Close_JT"], row["Diff_JT"])
            daily_gap = abs(daily_pct1329 - daily_pctJT)

            if self.should_recovery_rebalance(row, portfolio):

                decision = TradeDecision(
                    execute=True,
                    reason="1329回復リバランス",
                    side1329="BUY",
                    sideJT="SELL",
                    pct1329=daily_pct1329,
                    pctJT=daily_pctJT,
                    gap=daily_gap
                )

                executed_1329_qty, executed_JT_qty = self.execute_recovery_rebalance(
                    row,
                    portfolio
                )

                if executed_1329_qty == 0 and executed_JT_qty == 0:
                    decision.execute = False
                    decision.reason = "約定なし"

            elif self.is_recovery_watch_mode(portfolio):

                # JT比率がしきい値を超えたら、通常売買はいったん止める。
                # 1329が25日線から-3%以上割安になるまで、1329をさらに売らない。
                decision = TradeDecision(
                    execute=False,
                    reason="1329回復待ち",
                    side1329="WAIT",
                    sideJT="WAIT",
                    pct1329=daily_pct1329,
                    pctJT=daily_pctJT,
                    gap=daily_gap
                )

            else:

                decision = self.strategy.judge(

                    close1329=row["Close_1329"],

                    diff1329=row["Diff_1329"],

                    closeJT=row["Close_JT"],

                    diffJT=row["Diff_JT"],

                    avg1329=portfolio.position1329.average_price,

                    avgJT=portfolio.positionJT.average_price

                )

                ##################################################

                if decision.execute:

                    # Ver1.0方針：追加資金は入れず、保有数量と手元資金の範囲内で約定させる。
                    # まず売却を実行し、その売却代金を購入原資にする。
                    if decision.side1329 == "SELL":
                        executed_1329_qty = portfolio.sell1329(
                            decision.qty1329,
                            row["Close_1329"]
                        )

                    if decision.sideJT == "SELL":
                        executed_JT_qty = portfolio.sellJT(
                            decision.qtyJT,
                            row["Close_JT"],
                            MINI_STOCK_COST
                        )

                    if decision.side1329 == "BUY":
                        executed_1329_qty = portfolio.buy1329(
                            decision.qty1329,
                            row["Close_1329"]
                        )

                    if decision.sideJT == "BUY":
                        executed_JT_qty = portfolio.buyJT(
                            decision.qtyJT,
                            row["Close_JT"],
                            MINI_STOCK_COST
                        )

                    if executed_1329_qty == 0 and executed_JT_qty == 0:
                        decision.execute = False
                        decision.reason = "約定なし"
            ##################################################

            s = portfolio.summary()

            logs.append({

                "Date": row["Date"],

                "Execute": decision.execute,

                "Reason": decision.reason,

                "1329_Action": decision.side1329,

                "1329_Qty": executed_1329_qty if decision.execute else 0,

                "JT_Action": decision.sideJT,

                "JT_Qty": executed_JT_qty if decision.execute else 0,

                "Year": row.get("Year"),

                "Close_1329": row["Close_1329"],

                "Close_JT": row["Close_JT"],

                "Cash": s["cash"],

                "Asset": s["asset"],

                "Realized": s["realized"],

                "1329_Qty_Hold": s["1329_qty"],

                "1329_Avg": s["1329_avg"],

                "1329_Eval": s["1329_eval"],

                "JT_Qty_Hold": s["JT_qty"],

                "JT_Avg": s["JT_avg"],

                "JT_Eval": s["JT_eval"],

                "1329_Ratio": s["1329_ratio"],

                "JT_Ratio": s["JT_ratio"],

                "Extra_Funding": s["extra_funding"],

                "Total_Fee": s.get("total_fee", 0.0),

                "Pct_1329": decision.pct1329,

                "Pct_JT": decision.pctJT,

                "Gap": decision.gap,

                "BasePercent": decision.base_percent,

                "Merit": decision.merit,

                "Planned1329Amount": decision.planned_amount1329,

                "PlannedJTAmount": decision.planned_amountJT,

                "JT_MiniQty": decision.miniJTQty,

                "1329_MA25": row.get("1329_MA25"),

                "1329_Deviation25": row.get("1329_Deviation25"),

            })

        ##################################################

        result = pd.DataFrame(logs)

        os.makedirs(RESULT_PATH, exist_ok=True)

        result.to_csv(

            os.path.join(

                RESULT_PATH,

                "trade_log.csv"

            ),

            index=False,

            encoding="utf-8-sig"

        )

        print(result.tail())

        return result