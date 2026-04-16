from src.position_builder import Contract, Position, ShortPut, ShortCall, LongCall, LongPut


def test_naked_short_put_max_loss():
    """A naked short put max loss is strike - premium (stock goes to 0)."""
    contract = Contract(strike=56, premium=50, expiration="2025-12-20", volume=1)
    leg = ShortPut(contract)
    position = Position(legs=[leg])
    actual_max_loss = position.max_loss()
    assert actual_max_loss == 5600 - 50


def test_naked_short_call_max_loss():
    """A naked short call has theoretically unlimited max loss."""
    contract = Contract(strike=100, premium=5.0, expiration="2025-12-20", volume=1)
    leg = ShortCall(contract)
    position = Position(legs=[leg])
    assert position.max_loss() == float("inf")


def test_long_call_max_loss():
    """A long call max loss is the premium paid."""
    contract = Contract(strike=100, premium=5.0, expiration="2025-12-20", volume=1)
    leg = LongCall(contract)
    position = Position(legs=[leg])
    assert position.max_loss() == 5.0


def test_long_put_max_loss():
    """A long put max loss is the premium paid."""
    contract = Contract(strike=100, premium=5.0, expiration="2025-12-20", volume=1)
    leg = LongPut(contract)
    position = Position(legs=[leg])
    assert position.max_loss() == 5.0


def test_polymorphism_position_doesnt_care_about_type():
    """Position.max_loss() works the same way regardless of leg type.

    This is the whole point of polymorphism -- the caller (Position) uses
    a uniform interface and the concrete type determines the behavior.
    """
    legs = [
        ShortPut(Contract(strike=100, premium=5.0, expiration="2025-12-20", volume=1)),
        LongCall(Contract(strike=110, premium=3.0, expiration="2025-12-20", volume=1)),
    ]
    position = Position(legs=legs)
    assert position.max_loss() == (100 * 100 - 5) + 3
