import numpy as np
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class Contract:
    strike: float
    premium: float
    expiration: float
    volume: int

class Leg(ABC):
    def __init__(self, contract):
        self.contract = contract
    
    @abstractmethod
    def max_loss(self):
        pass

class ShortPut(Leg):
    def max_loss(self):
        c = self.contract
        return c.strike * c.volume * 100 - c.premium
    
class ShortCall(Leg):
    def max_loss(self):
        return float("inf")

class LongPut(Leg):
    def max_loss(self):
        c = self.contract
        return c.premium
    
class LongCall(Leg):
    def max_loss(self):
        c = self.contract
        return c.premium

class LongStock(Leg):
    def max_loss(self):
        c = self.contract
        return c.strike * c.volume * 100

class Position:
    def __init__(self, legs):
        self.legs = legs

    def max_loss(self):
        # Check for covered call: LongStock + ShortCall combination
        long_stock_volume = sum(
            leg.contract.volume for leg in self.legs if isinstance(leg, LongStock)
        )
        short_call_volume = sum(
            leg.contract.volume for leg in self.legs if isinstance(leg, ShortCall)
        )
        
        # If we have a covered call (stock covers the short call)
        if long_stock_volume > 0 and short_call_volume > 0:
            covered_volume = min(long_stock_volume, short_call_volume)
            total_loss = 0
            
            for leg in self.legs:
                if isinstance(leg, LongStock):
                    # Stock at risk if price goes to $0
                    total_loss += leg.contract.strike * leg.contract.volume * 100
                elif isinstance(leg, ShortCall):
                    # For covered calls, short call premium offsets the loss
                    # The covered portion has limited loss (just premium received)
                    total_loss -= leg.contract.premium * (covered_volume / leg.contract.volume)
                    # Any uncovered portion still has infinite loss
                    if leg.contract.volume > covered_volume:
                        return float("inf")
                else:
                    total_loss += leg.max_loss()
            return total_loss
        
        # Default: simple sum of individual leg max losses
        return sum(leg.max_loss() for leg in self.legs)