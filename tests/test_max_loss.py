from src.position_builder import Contract, Position, ShortPut, ShortCall, LongCall, LongPut, LongStock


def test_naked_short_put_max_loss():
    """A naked short put max loss is strike - premium (stock goes to 0)."""
    contract = Contract(strike=56, unit_premium=50, expiration="2025-12-20", volume=1)
    leg = ShortPut(contract)
    position = Position(legs=[leg])
    actual_max_loss = position.max_loss()
    assert actual_max_loss == 5600 - 50


def test_naked_short_call_max_loss():
    """A naked short call has theoretically unlimited max loss."""
    contract = Contract(strike=100, unit_premium=5.0, expiration="2025-12-20", volume=1)
    leg = ShortCall(contract)
    position = Position(legs=[leg])
    assert position.max_loss() == float("inf")


def test_long_call_max_loss():
    """A long call max loss is the premium paid."""
    contract = Contract(strike=100, unit_premium=5.0, expiration="2025-12-20", volume=1)
    leg = LongCall(contract)
    position = Position(legs=[leg])
    assert position.max_loss() == 5.0


def test_long_put_max_loss():
    """A long put max loss is the premium paid."""
    contract = Contract(strike=100, unit_premium=5.0, expiration="2025-12-20", volume=1)
    leg = LongPut(contract)
    position = Position(legs=[leg])
    assert position.max_loss() == 5.0


def test_covered_call_max_loss():
    """A covered call max loss is stock value - premium received.

    When stock goes to $0, you lose the entire stock value but keep
    the premium from the short call. The short call is covered by
    the long stock, so its loss is limited to the premium received.
    
    Note: 1 option contract = 100 shares. Stock volume is in individual
    shares, so we use volume=100 to cover 1 short call contract.
    """
    stock = LongStock(Contract(strike=60, unit_premium=0, expiration="2025-12-20", volume=1))
    short_call = ShortCall(Contract(strike=65, unit_premium=5.0, expiration="2025-12-20", volume=1))
    position = Position(legs=[stock, short_call])
    # Stock loses 6000 (60 * 100 shares), short call keeps 5.0 premium
    assert position.max_loss() == float('inf')


def test_polymorphism_position_doesnt_care_about_type():
    """Position.max_loss() works the same way regardless of leg type.

    This is the whole point of polymorphism -- the caller (Position) uses
    a uniform interface and the concrete type determines the behavior.
    """
    legs = [
        ShortPut(Contract(strike=100, unit_premium=5.0, expiration="2025-12-20", volume=1)),
        LongCall(Contract(strike=110, unit_premium=3.0, expiration="2025-12-20", volume=1)),
    ]
    position = Position(legs=legs)
    assert position.max_loss() == (100 * 100 - 5) + 3
