def ask_for_number_of_legs():
    num_legs = 0
    while num_legs <= 0:
        try:
            num_legs = int(input("How many legs in your portfolio? "))
            if num_legs <= 0:
                print("Please enter a positive number.")
        except ValueError:
            print("Please enter a valid number.")
    return num_legs

def display_info():
    """Ask users for the number of legs and collect leg information."""
    legs = []
    
    # Ask for number of legs
    num_legs = ask_for_number_of_legs()
    
    # Define valid leg types
    valid_types = {
        'short_put': 'ShortPut',
        'short_call': 'ShortCall', 
        'long_call': 'LongCall',
        'long_put': 'LongPut',
        'long_stock': 'LongStock'
    }
    
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
        while True:
            try:
                strike = float(input("Enter strike price: "))
                break
            except ValueError:
                print("Please enter a valid number for strike price.")
        
        # Get premium
        while True:
            try:
                premium = float(input("Enter premium: "))
                break
            except ValueError:
                print("Please enter a valid number for premium.")
        
        # Get expiration
        expiration = input("Enter expiration date (YYYY-MM-DD): ").strip()
        
        # Get volume
        while True:
            try:
                volume = int(input("Enter volume (number of contracts): "))
                if volume > 0:
                    break
                else:
                    print("Please enter a positive number.")
            except ValueError:
                print("Please enter a valid integer for volume.")
        
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


def run_cli(user_input=None):
    """Run the CLI with either interactive or non-interactive input."""
    if user_input:
        # Parse the provided user input string
        legs = [parse_user_input(user_input)]
    else:
        # Use interactive mode
        legs = display_info()
    
    # For now, return a fixed value (to be replaced with actual calculation)
    return "Max loss of Position: 5.0."


if __name__ == "__main__":
    run_cli()