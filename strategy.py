from dataclasses import dataclass

from config import DEAD_ZONE


@dataclass
class TradeDecision:

    execute: bool = False

    reason: str = ""

    side1329: str = ""

    qty1329: int = 0

    sideJT: str = ""

    qtyJT: int = 0

    # Ver1.1.1: 判定理由を後から分析するためのデバッグ項目
    pct1329: float = 0.0
    pctJT: float = 0.0
    gap: float = 0.0
    base_percent: float = 0.0
    merit: float = 0.0
    planned_amount1329: float = 0.0
    planned_amountJT: float = 0.0
    miniJTQty: int = 0


class Strategy:

    def __init__(self, quantity_table):

        self.quantity_table = quantity_table

    ##################################################

    def calc_percent(self, close, diff):

        yesterday = close - diff

        if yesterday == 0:

            return 0

        return diff / yesterday * 100

    ##################################################

    def judge(

        self,

        close1329,

        diff1329,

        closeJT,

        diffJT,

        avg1329,

        avgJT,

    ):

        decision = TradeDecision()

        pct1329 = self.calc_percent(close1329, diff1329)

        pctJT = self.calc_percent(closeJT, diffJT)

        gap = abs(pct1329 - pctJT)

        decision.pct1329 = pct1329
        decision.pctJT = pctJT
        decision.gap = gap

        ##################################################

        if gap < DEAD_ZONE:

            decision.reason = "デッドゾーン"

            return decision

        ##################################################

        if (pct1329 >= 0 and pctJT >= 0) or (pct1329 <= 0 and pctJT <= 0):

            base = pct1329 if abs(pct1329) >= abs(pctJT) else pctJT

        else:

            base = pct1329

        decision.base_percent = base

        ##################################################

        qty1329 = self.quantity_table.get_quantity(abs(base))

        ##################################################

        if base < 0:

            decision.side1329 = "BUY"

            decision.qty1329 = qty1329

            decision.sideJT = "SELL"

        else:

            decision.side1329 = "SELL"

            decision.qty1329 = qty1329

            decision.sideJT = "BUY"

        ##################################################
        # JT数量計算
        ##################################################

        amount = qty1329 * close1329

        qtyJT = int(round(amount / closeJT))

        decision.qtyJT = qtyJT
        decision.planned_amount1329 = amount
        decision.planned_amountJT = qtyJT * closeJT
        decision.miniJTQty = qtyJT % 100

        ##################################################
        # 王将フィルター
        ##################################################

        merit = 0

        if decision.side1329 == "SELL":

            merit += (close1329 - avg1329) * qty1329

        else:

            merit += (avg1329 - close1329) * qty1329

        if decision.sideJT == "SELL":

            merit += (closeJT - avgJT) * qtyJT

        else:

            merit += (avgJT - closeJT) * qtyJT

        decision.merit = merit

        ##################################################

        if merit <= 0:

            decision.reason = "王将フィルター"

            return decision

        ##################################################

        decision.execute = True

        decision.reason = "GO"

        return decision
