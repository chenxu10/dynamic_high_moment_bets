"""
CLI Adapter - Implements UserInterfacePort for command-line interface.

This adapter knows HOW to interact via command line (input(), print()).
It does NOT know about business logic (that's in Presenter).
"""
from typing import Dict, Any

from src.presenter import UserInterfacePort, PositionPresenter


class CliAdapter(UserInterfacePort):
    """
    CLI Adapter: Implements UserInterfacePort using command-line I/O.
    
    This is the "HOW" for CLI - it handles:
    - Prompting user with input()
    - Validating user input
    - Printing results with print()
    """
    
    def ask_number_of_legs(self) -> int:
        """Ask user for number of legs via command line."""
        return self._get_validated_input(
            "How many legs in your portfolio? ",
            int,
            "Please enter a valid number.",
            lambda x: x > 0,
            "Please enter a positive number."
        )
    
    def ask_leg_info(self, valid_types: Dict[str, str]) -> Dict[str, Any]:
        """Ask user for leg information via command line."""
        print(f"\n--- New Leg ---")
        print("Valid leg types:")
        for code, name in valid_types.items():
            print(f"  {code} (for {name.lower().replace('short', 'short ').replace('long', 'long ')})")
        
        # Get leg type
        while True:
            leg_type = input("Enter leg type: ").strip().lower()
            if leg_type in valid_types:
                break
            print("Invalid leg type. Please choose from the valid options.")
        
        # Get strike
        strike = self._get_validated_input(
            "Enter strike price: ",
            float,
            "Please enter a valid number for strike price."
        )
        
        # Get premium
        premium = self._get_validated_input(
            "Enter premium: ",
            float,
            "Please enter a valid number for premium."
        )
        
        # Get expiration
        expiration = input("Enter expiration date (YYYY-MM-DD): ").strip()
        
        # Get volume
        volume = self._get_validated_input(
            "Enter volume (number of contracts): ",
            int,
            "Please enter a valid integer for volume.",
            lambda x: x > 0,
            "Please enter a positive number."
        )
        
        leg_info = {
            'type': leg_type,
            'strike': strike,
            'premium': premium,
            'expiration': expiration,
            'volume': volume
        }
        
        print(f"Added {leg_type} leg with strike={strike}, premium={premium}, "
              f"expiration={expiration}, volume={volume}")
        
        return leg_info
    
    def display_result(self, max_loss: float) -> None:
        """Display max loss result via command line."""
        print(f"\n{'='*50}")
        print(f"Max loss of Position: {max_loss}")
        print(f"{'='*50}")
    
    def display_error(self, message: str) -> None:
        """Display error message via command line."""
        print(f"\nERROR: {message}")
    
    def _get_validated_input(self, prompt, converter, error_msg, 
                             validator=None, validation_error_msg=None):
        """Get and validate user input with a type converter."""
        while True:
            try:
                value = converter(input(prompt))
                if validator is None or validator(value):
                    return value
                if validation_error_msg:
                    print(validation_error_msg)
            except ValueError:
                print(error_msg)


def run_cli():
    """
    Run the CLI application.
    
    This is the entry point for CLI mode.
    """
    ui = CliAdapter()
    presenter = PositionPresenter(ui)
    return presenter.run()


if __name__ == "__main__":
    run_cli()
