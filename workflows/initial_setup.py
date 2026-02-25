"""Initial setup workflow for extracting all historical receipt data."""

from typing import Optional

from auth import setup_and_test_session
from storage import sort_receipts_by_date
from .collector import process_all_tickets


def initial_setup(
    auth_method: Optional[str] = None,
    cookies_file: Optional[str] = None,
) -> bool:
    """
    Extract all historical receipt data using the API.

    Args:
        auth_method: Authentication method - 'firefox', 'chrome', 'chromium', or 'file'.
                     If None, prompts user interactively.
        cookies_file: Path to cookies file (only used when auth_method is 'file').

    Returns:
        bool: True if successful, False otherwise
    """
    print("=== INITIAL SETUP: Extracting all receipts ===")

    session = setup_and_test_session(auth_method, cookies_file)
    if not session:
        return False

    processed_count, skipped_count, total_pages = process_all_tickets(session)

    total_receipts = sort_receipts_by_date()
    print("All receipts sorted by date.")

    print("\n=== INITIAL SETUP COMPLETE ===")
    print(f"Pages processed: {total_pages}")
    print(f"New receipts extracted: {processed_count}")
    print(f"Receipts skipped: {skipped_count}")
    print(f"Total receipts in file: {total_receipts}")

    return True
