class PLPlotDataBuilder:
    def __init__(self, stock_price_range, position):
        self.stock_price_range = stock_price_range
        self.position = position

    def calculate_actual_pl_range(self):
        
        pnl_range = []
        
        for s in self.stock_price_range:
            pnl_at_s = sum(leg.pnl_at(s) for leg in self.position.legs)
            pnl_range.append(pnl_at_s)  
            
        return pnl_range
    
    def identify_worst_loss_point(self):
        pnl_range = self.calculate_actual_pl_range()
        min_pnl = min(pnl_range)
        min_index = pnl_range.index(min_pnl)
        price = self.stock_price_range[min_index]
        return (price, min_pnl)