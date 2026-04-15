import numpy as np
from dataclasses import dataclass

class Leg:
    def short_call(self, strike, premium, expiration):
        pass

    def short_put(self, strike, premium, expiration):
        pass

@dataclass
class Position:
    def __init__(self, legs):
        self.legs = []

    def max_loss(self):
        return -np.inf