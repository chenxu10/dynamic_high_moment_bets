# Given a position with four legs able to 
# calculate max_loss
# calculate breakeven_point
# calculate max_gain
# calculate probability of winning
# calculate expected_payoff
# plot payoff
# plot when time and volatility changes


import numpy as np
from src.position_builder import Position, Leg

def test_calculate_max_loss():
    one_leg_position = Position(legs=[
        Leg.short_call(strike=630, premium=5, expiration="2026-04-17")
    ])
    actual_max_loss = one_leg_position.max_loss()
    assert actual_max_loss == -np.inf

if __name__ == "__main__":
    test_calculate_max_loss()
