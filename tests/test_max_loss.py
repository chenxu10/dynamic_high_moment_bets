# Given a position with four legs able to 
# calculate max_loss
# calculate breakeven_point
# calculate max_gain
# calculate probability of winning
# calculate expected_payoff
# plot payoff
# plot when time and volatility changes


import numpy as np
from src.position_builder import Position

def test_calculate_max_loss():
    one_leg_position = Position()
    actual_max_loss = one_leg_position.calculate_max_loss()
    assert actual_max_loss == -np.Infinity

if __name__ == "__main__":
    test_calculate_max_loss()