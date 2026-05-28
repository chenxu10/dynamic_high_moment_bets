from dataclasses import dataclass
from typing import List, Tuple, Dict, Any

from src.position_builder import (
    Position,
    LongCall,
    ShortCall,
    LongPut,
    ShortPut,
    LongStock,
)


@dataclass
class PlotData:
    """Data container for P&L plot information.

    Decouples data preparation from rendering.
    """
    curve_points: List[Tuple[float, float]]
    max_loss_marker: Dict[str, Any]
    breakeven_points: List[float]


def _compute_pnl_at(price, legs):
    """Total P&L for all legs at a single underlying price."""
    return sum(leg.pnl_at(price) for leg in legs)


def _compute_correct_pnl_at(price, legs):
    """Total P&L with premium multiplied by 100 (correct financial logic)."""
    total = 0
    for leg in legs:
        c = leg.contract
        if isinstance(leg, LongCall):
            intrinsic = max(price - c.strike, 0) * c.volume * 100
            total += intrinsic - c.unit_premium * c.volume * 100
        elif isinstance(leg, ShortCall):
            intrinsic = max(price - c.strike, 0) * c.volume * 100
            total += c.unit_premium * c.volume * 100 - intrinsic
        elif isinstance(leg, LongPut):
            intrinsic = max(c.strike - price, 0) * c.volume * 100
            total += intrinsic - c.unit_premium * c.volume * 100
        elif isinstance(leg, ShortPut):
            intrinsic = max(c.strike - price, 0) * c.volume * 100
            total += c.unit_premium * c.volume * 100 - intrinsic
        elif isinstance(leg, LongStock):
            total += (price - c.strike) * c.volume
    return total


def _collect_critical_prices(position):
    """Gather the kink points where P&L slope may change.

    Returns 0, every unique strike, and a point well above the
    highest strike so the far-right linear segment is captured.
    """
    critical_prices = {0.0}
    for leg in position.legs:
        critical_prices.add(leg.contract.strike)

    max_strike = max(leg.contract.strike for leg in position.legs)
    critical_prices.add(max_strike * 2)

    return sorted(critical_prices)


def _sample_pnl_at_prices(prices, position):
    """Evaluate total P&L at each price in the given list."""
    return [_compute_pnl_at(p, position.legs) for p in prices]


def _interpolate_zero_crossing(p1, v1, p2, v2):
    """Linearly interpolate the price where P&L crosses zero.

    Precondition: v1 and v2 have opposite signs and p1 != p2.
    """
    # pnl = v1 + (price - p1) * (v2 - v1) / (p2 - p1)
    # Set pnl = 0: price = p1 - v1 * (p2 - p1) / (v2 - v1)
    return p1 - v1 * (p2 - p1) / (v2 - v1)


def _find_zero_crossings(prices, pnls):
    """Scan adjacent (price, pnl) pairs and collect all breakevens."""
    breakevens = []
    for i in range(len(prices) - 1):
        p1, p2 = prices[i], prices[i + 1]
        v1, v2 = pnls[i], pnls[i + 1]

        if v1 == 0:
            breakevens.append(p1)

        if v1 * v2 < 0:
            crossing = _interpolate_zero_crossing(p1, v1, p2, v2)
            breakevens.append(crossing)

    return breakevens


def _append_last_point_if_zero(prices, pnls, breakevens):
    """If the rightmost price has exactly zero P&L, add it."""
    if pnls and pnls[-1] == 0:
        breakevens.append(prices[-1])
    return breakevens


def _deduplicate_and_sort(values):
    """Round to 6 decimals, remove duplicates, and return sorted."""
    return sorted(set(round(v, 6) for v in values))


def _find_worst_loss_point(stock_price_range, pnl_range):
    """Return (price, pnl) of the most negative P&L value."""
    min_pnl = min(pnl_range)
    min_index = pnl_range.index(min_pnl)
    price = stock_price_range[min_index]
    return (price, min_pnl)


class PLPlotDataBuilder:
    def __init__(self, stock_price_range, position):
        self.stock_price_range = stock_price_range
        self.position = position

    def calculate_actual_pl_range(self):
        return [_compute_pnl_at(s, self.position.legs)
                for s in self.stock_price_range]

    def identify_worst_loss_point(self):
        pnl_range = self.calculate_actual_pl_range()
        return _find_worst_loss_point(self.stock_price_range, pnl_range)

    def calculate_breakeven_points(self):
        """Find exact prices where total P&L equals zero.

        P&L is piecewise-linear between critical prices (0 and all strikes).
        We evaluate at critical points and interpolate for zero crossings.
        """
        if not self.position.legs:
            return []

        critical_prices = _collect_critical_prices(self.position)
        pnl_values = [
            _compute_correct_pnl_at(p, self.position.legs)
            for p in critical_prices
        ]

        breakevens = _find_zero_crossings(critical_prices, pnl_values)
        breakevens = _append_last_point_if_zero(critical_prices, pnl_values, breakevens)
        return _deduplicate_and_sort(breakevens)

    def build(self):
        """Build a PlotData object from the position and price range."""
        pnl_range = self.calculate_actual_pl_range()
        curve_points = list(zip(self.stock_price_range, pnl_range))

        worst_price, worst_pnl = self.identify_worst_loss_point()
        max_loss_marker = {
            "x": worst_price,
            "y": worst_pnl,
            "color": "black"
        }

        breakeven_points = self.calculate_breakeven_points()

        return PlotData(
            curve_points=curve_points,
            max_loss_marker=max_loss_marker,
            breakeven_points=breakeven_points
        )
