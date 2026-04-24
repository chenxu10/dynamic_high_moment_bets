
from src.plvisualizer.plotdatabuilder import PLPlotDataBuilder
from src.position_builder import Contract, Position, ShortPut

def test_pl_at_four_points():
    stock_price_range = [0, 50, 100, 150]
    contract = Contract(strike=100, premium=5.0, expiration="2025-12-20", volume=1)
    leg = ShortPut(contract)
    position = Position(legs=[leg])
    actual_pl_range = PLPlotDataBuilder(
        stock_price_range, position).calculate_actual_pl_range()
    assert actual_pl_range == [5 - 100 * 100, 5 - 50 * 100, 5, 5]