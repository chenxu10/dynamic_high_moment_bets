import numpy as np
from dataclasses import dataclass
from abc import ABC, abstractmethod

class Leg:
    def __init__(self, strike, premium, expiration):
        self.strike = strike
        self.premium = premium
        self.expiration = expiration
    
    @abstractmethod
    def max_loss(self):
        pass

class ShortPut(Leg):
    def max_loss(self):
        return self.strike - self.premium
    
class ShortCall(Leg):
    def max_loss(self):
        return float("inf")

class LongPut(Leg):
    def max_loss(self):
        return self.premium
    
class LongCall(Leg):
    def max_loss(self):
        return self.premium 


class Leg:
    def short_call(self, strike, premium, expiration):
        pass

    def short_put(self, strike, premium, expiration):
        return {"type": "short_put", "strike": strike, "premium": premium}

@dataclass
class Position:
    def __init__(self, legs):
        self.legs = legs

    def max_loss(self):
        return sum(leg.max_loss()for leg in self.legs)