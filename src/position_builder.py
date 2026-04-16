import numpy as np
from dataclasses import dataclass

class ShortPut:
    def __init__(self, strike, premium, expiration):
        self.strike = strike
        self.premium = premium
        self.expiration = expiration

    def max_loss(self):
        return self.strike - self.premium


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
        leg = self.legs[0]
        return leg.max_loss()