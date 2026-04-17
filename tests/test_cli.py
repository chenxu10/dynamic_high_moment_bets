from src.cli_interface import run_cli


def test_single_long_call_prints_max_loss():
    user_input = "long_call strike=100 premium=5.0 expiration=2025-12-20 volume=1"
    result = run_cli(user_input)
    assert result == "Max loss of Position: 5.0."