import pandas as pd


class QuantityTable:

    def __init__(self, filename):

        self.table = pd.read_csv(filename)

        self.table = self.table.sort_values("percent")

    def get_quantity(self, percent):

        p = abs(percent)

        qty = self.table.iloc[-1]["quantity"]

        for _, row in self.table.iterrows():

            if p < row["percent"]:

                break

            qty = row["quantity"]

        return int(qty)