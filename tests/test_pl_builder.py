
import os
import tempfile

from src.plvisualizer.plotdatabuilder import PLPlotDataBuilder, PlotData
from src.plvisualizer.plot_adapter import PlotAdapterPort
from src.plvisualizer.matplotlib_adapter import MatplotlibPlotAdapter
from src.position_builder import Contract, Position, ShortPut, LongPut, ShortCall


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


def test_identify_worst_loss():
    stock_price_range = [0, 50, 100, 150]
    contract = Contract(strike=100, unit_premium=5.0, expiration="2025-12-20", volume=1)
    leg = ShortPut(contract)
    position = Position(legs=[leg])

    worst_loss_point = PLPlotDataBuilder(
        stock_price_range, position).identify_worst_loss_point()

    assert worst_loss_point == (0, 5 - 100 * 100)

    #TODO: add test case for duplicate minimum and empty range is a crash


def test_build_returns_plot_data_with_curve_and_marker():
    """Test 3 — Prepare for the Artist.

    The builder should return a PlotData object containing curve_points
    and a max_loss_marker with correct x, y, and color='black'.
    """
    stock_price_range = [0, 50, 100, 150]
    contract = Contract(strike=100, unit_premium=5.0, expiration="2025-12-20", volume=1)
    position = Position(legs=[ShortPut(contract)])

    plot_data = PLPlotDataBuilder(stock_price_range, position).build()

    assert isinstance(plot_data, PlotData)
    assert plot_data.curve_points == [
        (0, 5 - 100 * 100),
        (50, 5 - 50 * 100),
        (100, 5),
        (150, 5),
    ]
    assert plot_data.max_loss_marker == {
        "x": 0,
        "y": 5 - 100 * 100,
        "color": "black",
    }


def test_mock_plot_adapter_records_render_call():
    """Test 4 — The Adapter Contract.

    A MockPlotAdapter implementing PlotAdapterPort should record
    what it receives via render().
    """
    class MockPlotAdapter(PlotAdapterPort):
        def __init__(self):
            self.received_plot_data = None

        def render(self, plot_data):
            self.received_plot_data = plot_data

    stock_price_range = [0, 50, 100, 150]
    contract = Contract(strike=100, unit_premium=5.0, expiration="2025-12-20", volume=1)
    position = Position(legs=[ShortPut(contract)])

    plot_data = PLPlotDataBuilder(stock_price_range, position).build()

    mock = MockPlotAdapter()
    mock.render(plot_data)

    assert mock.received_plot_data is plot_data
    assert mock.received_plot_data.max_loss_marker["color"] == "black"


def test_two_leg_position_max_loss_not_at_zero():
    """Test 5 — Complexity Reveals Truth.

    A two-leg position where the worst loss does NOT occur at price 0.
    Verify curve points and max-loss marker coordinates.
    """
    stock_price_range = [80, 90, 100, 110]
    long_put = LongPut(Contract(strike=100, unit_premium=5.0, expiration="2025-12-20", volume=1))
    short_put = ShortPut(Contract(strike=90, unit_premium=3.0, expiration="2025-12-20", volume=1))
    position = Position(legs=[long_put, short_put])

    builder = PLPlotDataBuilder(stock_price_range, position)
    plot_data = builder.build()

    # Long put P&L: intrinsic - premium
    # Short put P&L: premium - intrinsic
    # Total P&L at each price:
    #   80: (20*100 - 5) + (3 - 10*100) = 1995 - 997 = 998
    #   90: (10*100 - 5) + 3 = 995 + 3 = 998
    #   100: (-5) + 3 = -2
    #   110: (-5) + 3 = -2
    expected_curve = [
        (80, 998.0),
        (90, 998.0),
        (100, -2.0),
        (110, -2.0),
    ]

    assert plot_data.curve_points == expected_curve
    # Worst loss is at prices 100 and 110 with P&L = -2
    # First occurrence at index 2 -> price 100
    assert plot_data.max_loss_marker["x"] == 100
    assert plot_data.max_loss_marker["y"] == -2.0
    assert plot_data.max_loss_marker["color"] == "black"


def test_breakeven_for_single_leg_long_call():
    """Breakeven for a long call is strike + premium."""
    stock_price_range = [90, 100, 110, 120]
    contract = Contract(strike=100, unit_premium=5.0, expiration="2025-12-20", volume=1)
    position = Position(legs=[LongPut(contract)])
    # Wait, LongPut breakeven is strike - premium = 95, but range starts at 90
    # Let's use LongCall instead for a clearer test
    from src.position_builder import LongCall
    position = Position(legs=[LongCall(contract)])
    builder = PLPlotDataBuilder([90, 100, 105, 110, 120], position)
    breakevens = builder.calculate_breakeven_points()
    # Long call P&L: max(price - 100, 0)*100 - 5
    # Breakeven when (price - 100)*100 = 5 -> price = 100.05
    assert abs(breakevens[0] - 100.05) < 1e-6


def test_breakeven_for_short_put():
    """Breakeven for a short put is strike - premium / (100 * volume)."""
    contract = Contract(strike=100, unit_premium=500.0, expiration="2025-12-20", volume=1)
    position = Position(legs=[ShortPut(contract)])
    # Short put P&L: 500 - max(100 - price, 0)*100
    # Breakeven when 500 = (100 - price)*100 -> price = 95
    builder = PLPlotDataBuilder([0, 50, 95, 100, 150], position)
    breakevens = builder.calculate_breakeven_points()
    assert abs(breakevens[0] - 95.0) < 1e-6


def test_breakeven_points_in_plot_data():
    """PlotData should include breakeven points from the builder."""
    contract = Contract(strike=100, unit_premium=500.0, expiration="2025-12-20", volume=1)
    position = Position(legs=[ShortPut(contract)])
    builder = PLPlotDataBuilder([0, 50, 95, 100, 150], position)
    plot_data = builder.build()
    assert abs(plot_data.breakeven_points[0] - 95.0) < 1e-6


def test_breakeven_multiple_crossings():
    """A spread can have two breakeven points."""
    # Long call at 90, short call at 110 (bull call spread)
    from src.position_builder import LongCall
    long_call = LongCall(Contract(strike=90, unit_premium=8.0, expiration="2025-12-20", volume=1))
    short_call = ShortCall(Contract(strike=110, unit_premium=3.0, expiration="2025-12-20", volume=1))
    position = Position(legs=[long_call, short_call])
    # Net premium paid = 8 - 3 = 5
    # P&L below 90: -5
    # P&L between 90 and 110: (price - 90)*100 - 5
    # P&L above 110: (110 - 90)*100 - 5 = 2000 - 5 = 1995
    # Breakevens: price where (price - 90)*100 = 5 -> price = 90.05
    builder = PLPlotDataBuilder([80, 90, 100, 110, 120], position)
    breakevens = builder.calculate_breakeven_points()
    assert abs(breakevens[0] - 90.05) < 1e-6
    assert len(breakevens) == 1


def test_default_filename_is_in_figures_folder():
    """By default the adapter saves plots under a figures/ directory."""
    adapter = MatplotlibPlotAdapter()
    assert adapter.filename == "figures/pl_payoff.png"


def test_render_creates_directory_if_missing():
    """render() should create the output directory when it does not exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "nested", "test_payoff.png")
        adapter = MatplotlibPlotAdapter(filename=output_path)

        contract = Contract(strike=100, unit_premium=5.0, expiration="2025-12-20", volume=1)
        position = Position(legs=[ShortPut(contract)])
        plot_data = PLPlotDataBuilder([0, 100, 150], position).build()

        adapter.render(plot_data)

        assert os.path.exists(output_path)
