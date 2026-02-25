"""Main menu interface for the shopping analyzer."""

from workflows import initial_setup, update_data


def main() -> None:
    """
    Main function that provides a simple menu for choosing between
    initial setup and update modes.
    """
    print("=== Welcome - which receipts would you like to add? ===")
    print("1. Initial Setup (all receipts)")
    print("2. Update (only add new receipts)")
    print("3. Exit")

    while True:
        try:
            choice = input("\nChoose an option (1-3): ").strip()

            if choice == "1":
                print("\nStarting Initial Setup...")
                success = initial_setup()
                if success:
                    print("✓ Initial Setup completed successfully!")
                else:
                    print("✗ Initial Setup failed!")
                break

            elif choice == "2":
                print("\nStarting Update...")
                success = update_data()
                if success:
                    print("✓ Update completed successfully!")
                else:
                    print("✗ Update failed!")
                break

            elif choice == "3":
                print("Goodbye!")
                break

            else:
                print("Invalid input. Please choose 1, 2 or 3.")

        except KeyboardInterrupt:
            print("\n\nProgram interrupted.")
            break
        except Exception as e:
            print(f"An error occurred: {e}")
            break
