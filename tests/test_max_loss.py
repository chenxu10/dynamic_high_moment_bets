import numpy as np
from src.position_builder import Position, Leg, ShortPut


def test_naked_short_put_max_loss():
    """A naked short call has theoretically unlimited max loss."""
    leg = ShortPut(strike=100, premium=5.0, expiration="2025-12-20")
    position = Position(legs=[leg])
    actual_max_loss = position.max_loss()
    assert actual_max_loss == 100 - 5
