import numpy as np
from dataclasses import dataclass

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
        return leg["strike"] - leg["premium"] 