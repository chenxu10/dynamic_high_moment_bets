import numpy as np
from src.position_builder import Position, Leg


def test_naked_short_call_has_unbounded_max_loss():
    """A naked short call has theoretically unlimited max loss."""
    leg = Leg()
    short_call = leg.short_put(strike=100, premium=5.0, expiration="2025-12-20")
    position = Position(legs=[short_call])
    
    actual_max_loss = position.max_loss()
    
    assert actual_max_loss == -np.inf
