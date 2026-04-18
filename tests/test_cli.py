"""
Tests for CLI Adapter and Presenter.

These tests verify:
1. The Presenter orchestrates flow correctly with a mock UI
2. The CLI adapter handles real command-line I/O
"""
from src.cli_interface import CliAdapter, run_cli
from src.presenter import PositionPresenter


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


# =============================================================================
# MONKEYPATCH EXAMPLES - Testing real CLI adapter with mocked input()
# =============================================================================

"""
WHAT IS MONKEYPATCH?
====================
monkeypatch is a pytest fixture that lets you TEMPORARILY replace functions 
or variables during a test. After the test ends, everything goes back to normal.

Think of it like putting a sticker over something - the original is still 
there underneath, but while the sticker is on, you see the new version.
"""


# Real input() function - normally waits for user to type
def ask_name():
    name = input("What's your name? ")  # This pauses for real user input!
    return f"Hello, {name}!"


# TEST 1: Basic monkeypatch example
def test_monkeypatch_hello_world(monkeypatch):
    """Hello World example of monkeypatch - replacing input() with fake data."""
    # Instead of waiting for real user input, we provide fake input
    monkeypatch.setattr('builtins.input', lambda prompt: "Alice")
    
    result = ask_name()
    assert result == "Hello, Alice!"


# TEST 2: Multiple inputs using an iterator
def ask_full_name():
    first = input("First name: ")
    last = input("Last name: ")
    return f"{first} {last}"


def test_monkeypatch_multiple_inputs(monkeypatch):
    """Using an iterator to provide multiple fake inputs in sequence."""
    # Create an iterator that yields values one at a time
    fake_inputs = iter(["John", "Doe"])
    monkeypatch.setattr('builtins.input', lambda prompt: next(fake_inputs))
    
    result = ask_full_name()
    assert result == "John Doe"


# =============================================================================
# CLI ADAPTER TESTS - Testing the real CLI with monkeypatched input()
# =============================================================================

def test_cli_adapter_ask_number_of_legs(monkeypatch):
    """CliAdapter.ask_number_of_legs() should return validated integer."""
    cli = CliAdapter()
    
    # Simulate user entering "3"
    monkeypatch.setattr('builtins.input', lambda prompt: "3")
    
    result = cli.ask_number_of_legs()
    assert result == 3


def test_cli_adapter_ask_leg_info(monkeypatch):
    """CliAdapter.ask_leg_info() should collect and return leg data."""
    cli = CliAdapter()
    
    # Simulate user entering leg info in sequence
    fake_inputs = iter(['lc', '100', '5.0', '2025-12-20', '1'])
    monkeypatch.setattr('builtins.input', lambda prompt: next(fake_inputs))
    
    valid_types = {'lc': 'LongCall', 'lp': 'LongPut'}
    result = cli.ask_leg_info(valid_types)
    
    assert result == {
        'type': 'lc',
        'strike': 100.0,
        'premium': 5.0,
        'expiration': '2025-12-20',
        'volume': 1
    }


def test_full_cli_flow_with_monkeypatch(monkeypatch):
    """Test full CLI flow with monkeypatched input."""
    # Simulate user entering: 1 leg, lc, strike 100, premium 5.0, expiration, volume 1
    fake_inputs = iter(['1', 'lc', '100', '5.0', '2025-12-20', '1'])
    monkeypatch.setattr('builtins.input', lambda prompt: next(fake_inputs))
    
    result = run_cli()
    
    assert "Max loss of Position: 5.0" in result


# =============================================================================
# MONKEYPATCH QUIZ - Fill in the blanks to test your understanding!
# =============================================================================

# QUIZ 1: Basic replacement
def ask_age():
    age = input("How old are you? ")
    return f"You are {age} years old"


def test_quiz_1_basic_replacement(monkeypatch):
    """QUIZ 1: Replace input() to return '25' without actually asking the user."""
    # FILL IN THE BLANK: Replace input() with a function that always returns "25"
    monkeypatch.__________('builtins.input', lambda prompt: ________)
    
    result = ask_age()
    assert result == "You are 25 years old"


# QUIZ 2: Using iter() for multiple values
def ask_coordinates():
    x = input("Enter X: ")
    y = input("Enter Y: ")
    return (x, y)


def test_quiz_2_iter_with_two_values(monkeypatch):
    """QUIZ 2: Use iter() to provide two different fake inputs."""
    # FILL IN THE BLANK: Create an iterator with values "10" and "20"
    fake_values = ________([________, ________])
    
    # FILL IN THE BLANK: Replace input() to use next() on our iterator
    monkeypatch.setattr('builtins.input', lambda prompt: ________(fake_values))
    
    result = ask_coordinates()
    assert result == ("10", "20")


# QUIZ 3: Testing a calculator function
def simple_calculator():
    num1 = int(input("Enter first number: "))
    num2 = int(input("Enter second number: "))
    return num1 + num2


def test_quiz_3_calculator_with_integers(monkeypatch):
    """QUIZ 3: Test calculator by faking inputs '5' and '3', expecting result 8."""
    # FILL IN THE BLANK: Create iterator with string values "5" and "3"
    fake_inputs = ________([________, ________])
    
    # FILL IN THE BLANK: Patch input() to use next(fake_inputs)
    ____________.setattr(__________, lambda _: ________(fake_inputs))
    
    result = simple_calculator()
    assert result == ________


# =============================================================================
# ANSWERS (Hidden at bottom - try first before looking!)
# =============================================================================
# QUIZ 1: monkeypatch.setattr('builtins.input', lambda prompt: "25")
# QUIZ 2: iter(["10", "20"]), next(fake_values)
# QUIZ 3: iter(["5", "3"]), monkeypatch, 'builtins.input', next, 8
# =============================================================================
