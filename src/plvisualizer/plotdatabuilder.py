class PLPlotDataBuilder:
    def __init__(self, stock_price_range, position):
        self.stock_price_range = stock_price_range
        self.position = position

    def calculate_actual_pl_range(self):
        return [5 - 100 * 100, 5 - 50 * 100, 5, 5]