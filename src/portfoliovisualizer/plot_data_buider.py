
def _compute_pnl_at(price, legs):
    """Total P&L for all legs at a single underlying price."""
    return sum(leg.pnl_at(price) for leg in legs)

class PLPlotDataBuilder:
    def __init__(self, stock_price_range, position):
        self.stock_price_range = stock_price_range
        self.position = position

    def calculate_actual_pl_range(self):
        return [_compute_pnl_at(s, self.position.legs)
                for s in self.stock_price_range]