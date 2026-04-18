from src.cli_interface import run_cli


def test_run_cli_with_long_call_leg(monkeypatch):
    """run_cli should calculate max loss for a single long call leg in interactive mode."""
    # Simulate user input: 1 leg, lc type, strike=100, premium=5.0, expiration, volume=1
    user_inputs = iter(['1', 'lc', '100', '5.0', '2025-12-20', '1'])
    monkeypatch.setattr('builtins.input', lambda _: next(user_inputs))
    
    result = run_cli()
    assert result == "Max loss of Position: 5.0"


def test_run_cli_with_long_put_leg(monkeypatch):
    """run_cli should calculate max loss for a single long put leg in interactive mode."""
    user_inputs = iter(['1', 'lp', '100', '3.0', '2025-12-20', '1'])
    monkeypatch.setattr('builtins.input', lambda _: next(user_inputs))
    
    result = run_cli()
    assert result == "Max loss of Position: 3.0"