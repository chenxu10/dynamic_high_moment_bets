"""
Presenter Layer - Orchestrates the application flow.

The Presenter:
- Knows WHAT the application should do
- Does NOT know HOW to interact with users (UI Adapter handles that)
- Works with ANY UI that implements UserInterfacePort
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List

from src.position_builder import Contract, ShortPut, ShortCall, LongCall, LongPut, LongStock, Position


class UserInterfacePort(ABC):
    """
    PORT: Abstract interface for user interaction.
    
    Any UI adapter (CLI, GUI, Web, etc.) must implement this interface.
    This is the "contract" between the Presenter and any UI.
    """
    
    @abstractmethod
    def ask_number_of_legs(self) -> int:
        """Ask user for number of legs in the position."""
        pass
    
    @abstractmethod
    def ask_leg_info(self, valid_types: Dict[str, str]) -> Dict[str, Any]:
        """Ask user for information about one leg."""
        pass
    
    @abstractmethod
    def display_result(self, max_loss: float) -> None:
        """Display the calculated max loss to the user."""
        pass
    
    @abstractmethod
    def display_error(self, message: str) -> None:
        """Display an error message to the user."""
        pass


class PositionPresenter:
    """
    PRESENTER: Orchestrates the max loss calculation flow.
    
    This class is UI-agnostic. It works with ANY adapter that implements
    UserInterfacePort (CLI today, GUI/Web/Mobile in the future).
    
    Usage:
        ui = CliAdapter()
        presenter = PositionPresenter(ui)
        presenter.run()
    """
    
    # Map short codes to leg classes
    TYPE_MAPPING = {
        'sp': ShortPut,
        'sc': ShortCall,
        'lc': LongCall,
        'lp': LongPut,
        'ls': LongStock,
    }
    
    def __init__(self, ui: UserInterfacePort):
        """
        Initialize with any UI adapter that implements UserInterfacePort.
        
        Args:
            ui: The user interface adapter (e.g., CliAdapter)
        """
        self.ui = ui
    
    def run(self) -> str:
        """
        Run the main application flow.
        
        Returns:
            String with the max loss result
        """
        # Step 1: Get number of legs
        num_legs = self.ui.ask_number_of_legs()
        
        # Step 2: Collect leg information
        valid_types = {code: cls.__name__ for code, cls in self.TYPE_MAPPING.items()}
        legs_data = []
        
        for i in range(num_legs):
            leg = self.ui.ask_leg_info(valid_types)
            legs_data.append(leg)
        
        # Step 3: Build position and calculate max loss
        try:
            position = self._build_position(legs_data)
            max_loss = position.max_loss()
            
            # Step 4: Display result
            self.ui.display_result(max_loss)
            return f"Max loss of Position: {max_loss}"
            
        except Exception as e:
            self.ui.display_error(f"Error calculating max loss: {e}")
            return f"Error: {e}"
    
    def _build_position(self, legs_data: List[Dict[str, Any]]) -> Position:
        """
        Build a Position from leg data dictionaries.
        
        Args:
            legs_data: List of leg info dictionaries
            
        Returns:
            Position object with all legs
        """
        legs = []
        
        for leg_data in legs_data:
            leg_type = leg_data['type']
            
            contract = Contract(
                strike=leg_data['strike'],
                premium=leg_data['premium'],
                expiration=leg_data.get('expiration', ''),
                volume=leg_data.get('volume', 1)
            )
            
            leg_class = self.TYPE_MAPPING.get(leg_type)
            if leg_class:
                legs.append(leg_class(contract))
            else:
                raise ValueError(f"Unknown leg type: {leg_type}")
        
        return Position(legs=legs)
