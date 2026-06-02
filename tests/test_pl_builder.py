from src.position_builder import Contract, Position, ShortPut
from src.portfoliovisualizer.plot_data_buider  import PLPlotDataBuilder

def test_pnl_at_four_points():
    stock_price_range = [0, 88, 100, 150]
    contract = Contract(
        strike=100, 
        premium=12, 
        expiration="2026-06-20", 
        volume=1)
    leg = ShortPut(contract)
    position = Position(legs=[leg])
    actual_pl_range = PLPlotDataBuilder(
        stock_price_range, position).calculate_actual_pl_range()
    assert actual_pl_range == [
        0 - 100 * 100 + 12,
        12 - (100 - 88) * 100,
        100 - 100 + 12,
        12] 