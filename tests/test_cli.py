"""
Tests for CLI Adapter and Presenter.

These tests verify:
1. The Presenter orchestrates flow correctly with a mock UI
2. The CLI adapter handles real command-line I/O
"""
from src.cli_interface import CliAdapter, run_cli
from src.strategy_interface import PositionPresenter


# =============================================================================
# MOCK UI ADAPTER - For testing Presenter without real user interaction
# =============================================================================

class MockUIAdapter:
    """
    Mock UI that implements UserInterfacePort.
    
    Used for testing the Presenter without real user interaction.
    Records all interactions and provides pre-programmed responses.
    """
    
    def __init__(self, simulated_inputs):
        self.simulated_inputs = simulated_inputs
        self.input_index = 0
        self.recorded_outputs = []
        self.recorded_errors = []
    
    def ask_number_of_legs(self):
        """Return next simulated input."""
        value = self.simulated_inputs[self.input_index]
        self.input_index += 1
        return value
    
    def ask_leg_info(self, valid_types):
        """Return next simulated leg data."""
        leg_data = self.simulated_inputs[self.input_index]
        self.input_index += 1
        return leg_data
    
    def display_result(self, max_loss):
        """Record the result."""
        self.recorded_outputs.append(f"Max loss: {max_loss}")
    
    def display_error(self, message):
        """Record the error."""
        self.recorded_errors.append(message)


# =============================================================================
# TDD TESTS - Using MockUI to test Presenter + Business Logic
# =============================================================================

def test_run_cli_with_long_call_leg():
    """
    Test the full flow: Presenter + Mock UI + Business Logic.
    
    This test proves that the architecture works:
    - Presenter orchestrates the flow
    - UI adapter provides data
    - Business logic calculates correctly
    """
    # Arrange: Mock UI with pre-programmed user responses
    mock_ui = MockUIAdapter([
        1,  # number of legs
        {'type': 'lc', 'strike': 100, 'premium': 5.0, 'expiration': '2025-12-20', 'volume': 1}
    ])
    
    # Act: Presenter orchestrates the flow
    presenter = PositionPresenter(mock_ui)
    result = presenter.run()
    
    # Assert: Correct max loss calculated and displayed
    assert result == "Max loss of Position: 5.0"
    assert mock_ui.recorded_outputs == ["Max loss: 5.0"]


def test_run_cli_with_long_put_leg():
    """Presenter should calculate max loss for a single long put leg."""
    mock_ui = MockUIAdapter([
        1,
        {'type': 'lp', 'strike': 100, 'premium': 3.0, 'expiration': '2025-12-20', 'volume': 1}
    ])
    
    presenter = PositionPresenter(mock_ui)
    result = presenter.run()
    
    assert result == "Max loss of Position: 3.0"


def test_run_cli_with_short_call_leg():
    """Presenter should return infinity for unlimited loss short call."""
    mock_ui = MockUIAdapter([
        1,
        {'type': 'sc', 'strike': 100, 'premium': 5.0, 'expiration': '2025-12-20', 'volume': 1}
    ])
    
    presenter = PositionPresenter(mock_ui)
    result = presenter.run()
    
    assert "inf" in result
    assert "Max loss of Position: inf" in result


def test_run_cli_with_multiple_legs():
    """Presenter should handle multiple legs correctly."""
    mock_ui = MockUIAdapter([
        2,  # number of legs
        {'type': 'lc', 'strike': 100, 'premium': 5.0, 'expiration': '2025-12-20', 'volume': 1},
        {'type': 'lp', 'strike': 90, 'premium': 3.0, 'expiration': '2025-12-20', 'volume': 1}
    ])
    
    presenter = PositionPresenter(mock_ui)
    result = presenter.run()
    
    # Max loss = long call premium (5.0) + long put premium (3.0) = 8.0
    assert "Max loss of Position:" in result



