import numpy as np
from src.position_builder import Position, Leg


def test_naked_short_call_has_unbounded_max_loss():
    """A naked short call has theoretically unlimited max loss."""
    short_call = Leg.short_call(strike=100, premium=5.0, expiration="2025-12-20")
    position = Position(legs=[short_call])
    
    actual_max_loss = position.max_loss()
    
    assert actual_max_loss == -np.Infinity


def test_long_call_has_bounded_max_loss():
    """A long call's max loss is limited to the premium paid."""
    long_call = Leg.long_call(strike=100, premium=5.0, expiration="2025-12-20")
    position = Position(legs=[long_call])
    
    actual_max_loss = position.max_loss()
    
    assert actual_max_loss == -5.0  # Premium paid is max loss
