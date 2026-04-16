from src.position_builder import Position, ShortPut, ShortCall, LongCall, LongPut


def test_naked_short_put_max_loss():
    """A naked short put max loss is strike - premium (stock goes to 0)."""
    leg = ShortPut(strike=100, premium=5.0, expiration="2025-12-20")
    position = Position(legs=[leg])
    actual_max_loss = position.max_loss()
    assert actual_max_loss == 100 - 5


def test_naked_short_call_max_loss():
    """A naked short call has theoretically unlimited max loss."""
    leg = ShortCall(strike=100, premium=5.0, expiration="2025-12-20")
    position = Position(legs=[leg])
    assert position.max_loss() == float("inf")


def test_long_call_max_loss():
    """A long call max loss is the premium paid."""
    leg = LongCall(strike=100, premium=5.0, expiration="2025-12-20")
    position = Position(legs=[leg])
    assert position.max_loss() == 5.0


def test_long_put_max_loss():
    """A long put max loss is the premium paid."""
    leg = LongPut(strike=100, premium=5.0, expiration="2025-12-20")
    position = Position(legs=[leg])
    assert position.max_loss() == 5.0


def test_polymorphism_position_doesnt_care_about_type():
    """Position.max_loss() works the same way regardless of leg type.

    This is the whole point of polymorphism -- the caller (Position) uses
    a uniform interface and the concrete type determines the behavior.
    """
    legs = [
        ShortPut(strike=100, premium=5.0, expiration="2025-12-20"),
        LongCall(strike=110, premium=3.0, expiration="2025-12-20"),
    ]
    position = Position(legs=legs)
    # sum of individual max losses: (100 - 5) + 3.0 = 98.0
    assert position.max_loss() == 98.0
