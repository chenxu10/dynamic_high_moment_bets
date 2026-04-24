
from src.plvisualizer.plotdatabuilder import PLPlotDataBuilder
from src.position_builder import Contract, Position, ShortPut, LongPut

def test_pnl_at_four_points():
    stock_price_range = [0, 50, 100, 150]
    contract = Contract(strike=100, unit_premium=5.0, expiration="2025-12-20", volume=1)
    leg = ShortPut(contract)
    position = Position(legs=[leg])
    actual_pl_range = PLPlotDataBuilder(
        stock_price_range, position).calculate_actual_pl_range()
    assert actual_pl_range == [5 - 100 * 100, 5 - 50 * 100, 5, 5]

def test_multiple_legs_pnl_at_four_points():
    stock_price_range = [0, 50, 100, 150]
    contract = Contract(strike=100, unit_premium=5.0, expiration="2026-04-20", volume=1)
    short_leg = ShortPut(contract)

    contract = Contract(strike=80, unit_premium=3, expiration="2026-06-20", volume=2)
    long_leg = LongPut(contract)
    position = Position(legs=[short_leg, long_leg])

    actual_pl_range = PLPlotDataBuilder(
        stock_price_range, position).calculate_actual_pl_range()
    assert actual_pl_range == [
        5 - 100*100 + 80*2*100 - 3*2,
        5 - 50*100  + 30*2*100 - 3*2,
        5 - 3*2,
        5 - 3*2,
    ]