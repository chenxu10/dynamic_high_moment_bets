from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class Contract:
    strike: float
    unit_premium: float
    expiration: float
    volume: int

class Leg(ABC):
    def __init__(self, contract):
        self.contract = contract
    
    @abstractmethod
    def pnl_at(self, price):
        """Return this leg's P&L when the underlying is at `price` at expiration."""
        pass

class ShortPut(Leg):
    def pnl_at(self, price):
        c = self.contract
        intrinsic = max(c.strike - price, 0) * c.volume * 100
        return c.unit_premium * c.volume - intrinsic

class ShortCall(Leg):
    def pnl_at(self, price):
        c = self.contract
        intrinsic = max(price - c.strike, 0) * c.volume * 100
        return c.unit_premium * c.volume - intrinsic

class LongPut(Leg):
    def pnl_at(self, price):
        c = self.contract
        intrinsic = max(c.strike - price, 0) * c.volume * 100
        return intrinsic - c.unit_premium * c.volume

class LongCall(Leg):
    def pnl_at(self, price):
        c = self.contract
        intrinsic = max(price - c.strike, 0) * c.volume * 100
        return intrinsic - c.unit_premium * c.volume

class LongStock(Leg):
    def pnl_at(self, price):
        c = self.contract
        # Stock volume is in individual shares, not 100-share contracts
        return (price - c.strike) * c.volume

class Position:
    def __init__(self, legs):
        self.legs = legs

    def _total_pnl_at(self, price):
        return sum(leg.pnl_at(price) for leg in self.legs)

    def max_loss(self):
        # Detect unbounded loss: if P&L keeps falling as price rises,
        # loss is infinite. Two points past the max strike suffice because
        # option P&L is piecewise-linear above the highest strike.
        high = max(leg.contract.strike for leg in self.legs) * 10 + 1
        if self._total_pnl_at(high * 2) < self._total_pnl_at(high):
            return float("inf")

        # Evaluate at all critical prices: 0 and every strike.
        # Option P&L is piecewise-linear; extremes occur at kink points.
        prices = [0] + [leg.contract.strike for leg in self.legs]
        worst_pnl = min(self._total_pnl_at(p) for p in prices)
        return -worst_pnl
