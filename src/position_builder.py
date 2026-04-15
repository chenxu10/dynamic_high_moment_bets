import numpy as np
from dataclasses import dataclass

class Leg:
    pass

@dataclass
class Position:
    def calculate_max_loss(self):
        return -np.Infinity