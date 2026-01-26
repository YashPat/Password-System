"""
Main entry point for password generation and recovery system.
Provides interactive CLI for generating passwords and recovering them.
"""
import sys
from password_generator import create_password_with_keys
from password_recovery import recover_password
from utils import format_keys, parse_keys, validate_keys
import config


def print_separator():
    """Print a visual separator."""
    print("\n" + "=" * 60 + "\n")


def generation_mode():
    """Handle password generation mode."""
    print_separator()
    print("PASSWORD GENERATION MODE")
    print_separator()
    print("Generating new password and recovery keys...")
    print("(This will be quick)")
    print()
    
    # Create password and keys
    password, seed, iterations = create_password_with_keys()
    
    # Format keys
    keys_string = format_keys(seed, iterations)
    
    print_separator()
    print("✓ Password generated successfully!")
    print_separator()
    print("YOUR PASSWORD:")
    print(f"  {password}")
    print()
    print("YOUR RECOVERY KEYS (save these securely!):")
    print(keys_string)
    print_separator()
    print("IMPORTANT: Save the recovery keys above. You will need them")
    print("to recover your password later (this will take ~15 hours).")
    print_separator()


def recovery_mode():
    """Handle password recovery mode."""
    print_separator()
    print("PASSWORD RECOVERY MODE")
    print_separator()
    print("Enter your recovery keys below.")
    print("(This computation will take approximately 15 hours)")
    print()
    
    # Get keys from user
    print("Paste your recovery keys (JSON format):")
    print("(Press Enter, then paste the keys, then press Enter again)")
    
    keys_lines = []
    try:
        while True:
            line = input()
            if line.strip() == "" and keys_lines:
                break
            keys_lines.append(line)
    except EOFError:
        pass
    
    keys_string = "\n".join(keys_lines).strip()
    
    if not keys_string:
        print("Error: No keys provided.")
        return
    
    # Parse keys
    keys = parse_keys(keys_string)
    if not keys or not validate_keys(keys):
        print("Error: Invalid recovery keys format.")
        print("Keys must be valid JSON with 'seed' and 'iterations' fields.")
        return
    
    seed = keys["seed"]
    iterations = keys["iterations"]
    
    # Estimate time
    estimated_time = config.estimate_time(iterations)
    estimated_hours = estimated_time / 3600
    
    print_separator()
    print(f"Recovery parameters:")
    print(f"  Iterations: {iterations:,}")
    print(f"  Estimated time: {estimated_hours:.1f} hours")
    print()
    print("Starting password recovery computation...")
    print("(You can monitor progress with the progress bar below)")
    print_separator()
    
    # Recover password
    password = recover_password(seed, iterations)
    
    if password:
        print_separator()
        print("✓ Password recovered successfully!")
        print_separator()
        print("YOUR PASSWORD:")
        print(f"  {password}")
        print_separator()
    else:
        print_separator()
        print("✗ Error: Failed to recover password.")
        print("Please check that your recovery keys are correct.")
        print_separator()


def main():
    """Main function with interactive menu."""
    print("=" * 60)
    print("PASSWORD GENERATION & RECOVERY SYSTEM")
    print("=" * 60)
    print()
    print("Select mode:")
    print("  1. Generate new password (quick)")
    print("  2. Recover password from keys (~15 hours)")
    print("  3. Exit")
    print()
    
    while True:
        try:
            choice = input("Enter choice (1-3): ").strip()
            
            if choice == "1":
                generation_mode()
                break
            elif choice == "2":
                recovery_mode()
                break
            elif choice == "3":
                print("Exiting...")
                sys.exit(0)
            else:
                print("Invalid choice. Please enter 1, 2, or 3.")
        except KeyboardInterrupt:
            print("\n\nExiting...")
            sys.exit(0)
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
