"""User input and selection prompts."""


def select_auth_method() -> str:
    """
    Let user select authentication method (browser extraction or file).

    Returns:
        str: 'file' for cookie file, or browser name ('firefox', 'chrome', or 'chromium')
    """
    print("\n=== Authentication Method ===")
    print("How would you like to authenticate?")
    print("1. Firefox browser (must be open and logged in)")
    print("2. Chrome browser (must be open and logged in)")
    print("3. Chromium browser (must be open and logged in)")
    print("4. Cookie file (must contain valid cookies)")

    while True:
        try:
            choice = input("\nChoose an option (1-4): ").strip()

            if choice == "1":
                return "firefox"
            elif choice == "2":
                return "chrome"
            elif choice == "3":
                return "chromium"
            elif choice == "4":
                return "file"
            else:
                print("Invalid input. Please choose 1, 2, 3 or 4.")

        except KeyboardInterrupt:
            print("\n\nAuthentication selection cancelled.")
            return "firefox"  # Default fallback


def select_browser() -> str:
    """
    DEPRECATED: Use select_auth_method() instead.
    Let user select browser for cookie extraction.

    Returns:
        str: Browser name ('firefox' or 'chrome')
    """
    print("\n=== Browser Selection ===")
    print("Which browser would you like to extract credentials from?")
    print("1. Firefox")
    print("2. Chrome")

    while True:
        try:
            choice = input("\nChoose a browser (1-2): ").strip()

            if choice == "1":
                return "firefox"
            elif choice == "2":
                return "chrome"
            else:
                print("Invalid input. Please choose 1 or 2.")

        except KeyboardInterrupt:
            print("\n\nBrowser selection cancelled.")
            return "firefox"  # Default fallback
