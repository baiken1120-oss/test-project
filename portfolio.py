from dataclasses import dataclass

from config import JT_ROUND_LOT


@dataclass
class Position:
    quantity: float = 0.0
    average_price: float = 0.0
    market_price: float = 0.0

    @property
    def market_value(self):
        return self.quantity * self.market_price

    @property
    def unrealized_profit(self):
        return (self.market_price - self.average_price) * self.quantity


class Portfolio:

    def __init__(self, initial_cash):
        self.cash = float(initial_cash)
        self.realized_profit = 0.0
        self.extra_funding = 0.0
        self.total_fee = 0.0

        self.position1329 = Position()
        self.positionJT = Position()

    def update_price(self, price1329, priceJT):
        self.position1329.market_price = float(price1329)
        self.positionJT.market_price = float(priceJT)

    def jt_mini_quantity(self, quantity):
        quantity = int(quantity)
        if quantity <= 0:
            return 0
        return quantity % JT_ROUND_LOT

    def jt_fee(self, quantity, price, cost_rate=0):
        mini_qty = self.jt_mini_quantity(quantity)
        return mini_qty * float(price) * float(cost_rate)

    def buy1329(self, quantity, price):
        quantity = int(quantity)
        price = float(price)

        if quantity <= 0 or price <= 0:
            return 0

        affordable_qty = int(self.cash // price)
        quantity = min(quantity, affordable_qty)

        if quantity <= 0:
            return 0

        cost = quantity * price

        p = self.position1329
        total_cost = p.average_price * p.quantity + cost

        p.quantity += quantity
        p.average_price = total_cost / p.quantity

        self.cash -= cost
        return quantity

    def sell1329(self, quantity, price):
        quantity = int(quantity)
        price = float(price)

        p = self.position1329
        quantity = min(quantity, int(p.quantity))

        if quantity <= 0:
            return 0

        profit = (price - p.average_price) * quantity
        self.realized_profit += profit

        p.quantity -= quantity
        self.cash += quantity * price

        if p.quantity == 0:
            p.average_price = 0.0

        return quantity

    def buyJT(self, quantity, price, cost_rate=0):
        quantity = int(quantity)
        price = float(price)
        cost_rate = float(cost_rate)

        if quantity <= 0 or price <= 0:
            return 0

        # 単元部分は通常取引、100株未満の端数だけミニ株コストを掛ける。
        # 手元資金内に収めるため、必要なら1株ずつ落とす。
        while quantity > 0:
            cost = quantity * price
            fee = self.jt_fee(quantity, price, cost_rate)
            if cost + fee <= self.cash:
                break
            quantity -= 1

        if quantity <= 0:
            return 0

        cost = quantity * price
        fee = self.jt_fee(quantity, price, cost_rate)
        total = cost + fee

        p = self.positionJT
        total_cost = p.average_price * p.quantity + total

        p.quantity += quantity
        p.average_price = total_cost / p.quantity

        self.cash -= total
        self.total_fee += fee
        return quantity

    def sellJT(self, quantity, price, cost_rate=0):
        quantity = int(quantity)
        price = float(price)
        cost_rate = float(cost_rate)

        p = self.positionJT
        quantity = min(quantity, int(p.quantity))

        if quantity <= 0:
            return 0

        proceeds = quantity * price
        fee = self.jt_fee(quantity, price, cost_rate)
        net_proceeds = proceeds - fee

        profit = (price - p.average_price) * quantity - fee
        self.realized_profit += profit

        p.quantity -= quantity
        self.cash += net_proceeds
        self.total_fee += fee

        if p.quantity == 0:
            p.average_price = 0.0

        return quantity

    @property
    def total_asset(self):
        return (
            self.cash
            + self.position1329.market_value
            + self.positionJT.market_value
        )

    def ratio1329(self):
        if self.total_asset == 0:
            return 0
        return self.position1329.market_value / self.total_asset

    def ratioJT(self):
        if self.total_asset == 0:
            return 0
        return self.positionJT.market_value / self.total_asset

    def summary(self):
        return {
            "cash": self.cash,
            "asset": self.total_asset,
            "realized": self.realized_profit,
            "extra_funding": self.extra_funding,
            "total_fee": self.total_fee,

            "1329_qty": self.position1329.quantity,
            "1329_avg": self.position1329.average_price,
            "1329_eval": self.position1329.unrealized_profit,
            "1329_ratio": self.ratio1329(),

            "JT_qty": self.positionJT.quantity,
            "JT_avg": self.positionJT.average_price,
            "JT_eval": self.positionJT.unrealized_profit,
            "JT_ratio": self.ratioJT(),
        }
