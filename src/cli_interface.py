def ask_for_number_of_legs():
    return _get_validated_input(
        "How many legs in your portfolio? ",
        int,
        "Please enter a valid number.",
        lambda x: x > 0,
        "Please enter a positive number."
    )

def _get_validated_input(prompt, converter, error_msg, validator=None, validation_error_msg=None):
    """Get and validate user input with a type converter and optional validator."""
    while True:
        try:
            value = converter(input(prompt))
            if validator is None or validator(value):
                return value
            if validation_error_msg:
                print(validation_error_msg)
        except ValueError:
            print(error_msg)

def define_valid_leg_types():
    valid_types = {
        'sp': 'ShortPut',
        'sc': 'ShortCall', 
        'lc': 'LongCall',
        'lp': 'LongPut',
        'ls': 'LongStock'
    }
    
    return valid_types

def display_info():
    """Ask users for the number of legs and collect leg information."""
    legs = []
    
    num_legs = ask_for_number_of_legs()
    valid_types = define_valid_leg_types()
    
    # Collect information for each leg
    for i in range(num_legs):
        print(f"\n--- Leg {i + 1} ---")
        
        # Get leg type
        print(f"Valid leg types: {', '.join(valid_types.keys())}")
        while True:
            leg_type = input("Enter leg type: ").strip().lower()
            if leg_type in valid_types:
                break
            print("Invalid leg type. Please choose from the valid options.")
        
        # Get strike
        strike = _get_validated_input(
            "Enter strike price: ",
            float,
            "Please enter a valid number for strike price."
        )
        
        # Get premium
        premium = _get_validated_input(
            "Enter premium: ",
            float,
            "Please enter a valid number for premium."
        )
        
        # Get expiration
        expiration = input("Enter expiration date (YYYY-MM-DD): ").strip()
        
        # Get volume
        volume = _get_validated_input(
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
        legs.append(leg_info)
        print(f"Added {leg_type} leg with strike={strike}, premium={premium}, expiration={expiration}, volume={volume}")
    
    return legs



def parse_user_input(user_input):
    """Parse user input string in format 'type key=value key=value ...'.
    
    Example: 'long_call strike=100 premium=5.0 expiration=2025-12-20 volume=1'
    """
    parts = user_input.split()
    leg_type = parts[0]
    
    # Parse key=value pairs
    kwargs = {}
    for part in parts[1:]:
        key, value = part.split('=')
        if key in ['strike', 'premium']:
            kwargs[key] = float(value)
        elif key == 'volume':
            kwargs[key] = int(value)
        else:
            kwargs[key] = value
    
    return {'type': leg_type, **kwargs}


def run_cli():
    """Run the CLI in interactive mode."""
    legs_data = display_info()
    position = _build_position_from_leg_data(legs_data)
    max_loss = position.max_loss()
    return f"Max loss of Position: {max_loss}"


def _build_position_from_leg_data(legs_data):
    """Build a Position from parsed leg data."""
    from src.position_builder import Contract, ShortPut, ShortCall, LongCall, LongPut, LongStock, Position
    
    type_mapping = {
        'sp': ShortPut,
        'sc': ShortCall,
        'lc': LongCall,
        'lp': LongPut,
        'ls': LongStock,
    }
    
    legs = []
    for leg_data in legs_data:
        leg_type = leg_data['type']
        contract = Contract(
            strike=leg_data['strike'],
            premium=leg_data['premium'],
            expiration=leg_data.get('expiration', ''),
            volume=leg_data.get('volume', 1)
        )
        leg_class = type_mapping.get(leg_type)
        if leg_class:
            legs.append(leg_class(contract))
    
    return Position(legs=legs)


if __name__ == "__main__":
    run_cli()