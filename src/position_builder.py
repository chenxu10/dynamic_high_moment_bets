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
    
class Position:
    def __init__(self, legs):
        self.legs = legs

    def max_loss(self):
        return sum(leg.max_loss()for leg in self.legs)