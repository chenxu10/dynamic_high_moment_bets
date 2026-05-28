from dataclasses import dataclass
from typing import List, Tuple, Dict, Any

from src.position_builder import Position


@dataclass
class PlotData:
    """Data container for P&L plot information.

    Decouples data preparation from rendering.
    """
    curve_points: List[Tuple[float, float]]
    max_loss_marker: Dict[str, Any]
    breakeven_points: List[float]


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

    def calculate_breakeven_points(self):
        """Find exact prices where total P&L equals zero.

        P&L is piecewise-linear between critical prices (0 and all strikes).
        We evaluate at critical points and interpolate for zero crossings.
        """
        if not self.position.legs:
            return []

        # Collect critical prices: 0, all unique strikes, and a point above max strike
        critical_prices = set([0.0])
        for leg in self.position.legs:
            critical_prices.add(leg.contract.strike)

        max_strike = max(leg.contract.strike for leg in self.position.legs)
        critical_prices.add(max_strike * 2)

        sorted_prices = sorted(critical_prices)
        pnl_values = [self.position._total_pnl_at(p) for p in sorted_prices]

        breakevens = []
        for i in range(len(sorted_prices) - 1):
            p1, p2 = sorted_prices[i], sorted_prices[i + 1]
            v1, v2 = pnl_values[i], pnl_values[i + 1]

            if v1 == 0:
                breakevens.append(p1)

            # Check for zero crossing between p1 and p2
            if v1 * v2 < 0 and p2 != p1:
                # Linear interpolation: pnl = v1 + (price - p1) * (v2 - v1) / (p2 - p1)
                # Set pnl = 0: price = p1 - v1 * (p2 - p1) / (v2 - v1)
                crossing = p1 - v1 * (p2 - p1) / (v2 - v1)
                breakevens.append(crossing)

        # Handle last point if exactly zero
        if pnl_values[-1] == 0:
            breakevens.append(sorted_prices[-1])

        # Remove duplicates within tolerance and sort
        breakevens = sorted(set(round(b, 6) for b in breakevens))
        return breakevens

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
