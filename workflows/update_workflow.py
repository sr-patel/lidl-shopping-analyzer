"""Update workflow for adding only new receipts."""

import time
from typing import Optional

from config import LidlConfig
from auth import setup_and_test_session
from api import get_tickets_page, get_receipt_details_and_html
from storage import load_existing_receipts, add_receipt_to_json, sort_receipts_by_date


def update_data(
    auth_method: Optional[str] = None,
    cookies_file: Optional[str] = None,
) -> bool:
    """
    Add only new receipts and sort by date at the end.

    Args:
        auth_method: Authentication method - 'firefox', 'chrome', 'chromium', or 'file'.
                     If None, prompts user interactively.
        cookies_file: Path to cookies file (only used when auth_method is 'file').

    Returns:
        bool: True if successful, False otherwise
    """
    print("=== UPDATE: Adding new receipts ===")

    session = setup_and_test_session(auth_method, cookies_file)
    if not session:
        return False

    recent_receipt_ids = []

    for page in range(1, LidlConfig.PAGES_TO_CHECK + 1):
        tickets_data = get_tickets_page(session, page)

        if not tickets_data or "items" not in tickets_data:
            break

        tickets = tickets_data["items"]
        if not tickets:
            break

        for ticket in tickets:
            if isinstance(ticket, dict):
                if "ticket" in ticket:
                    ticket_data = ticket["ticket"]
                    receipt_id = ticket_data["id"]
                    has_html = ticket_data.get("isHtml", False)
                else:
                    receipt_id = ticket.get("id", "")
                    has_html = ticket.get("isHtml", False)

                if receipt_id and has_html:
                    recent_receipt_ids.append(receipt_id)

    existing_ids, existing_receipts = load_existing_receipts()
    print(f"Existing receipts already stored: {len(existing_receipts)}")

    new_receipt_ids = [rid for rid in recent_receipt_ids if rid not in existing_ids]

    print(f"New receipts to process: {len(new_receipt_ids)}")

    processed_count = 0

    for i, receipt_id in enumerate(new_receipt_ids, 1):
        print(f"Processing new receipt {i}/{len(new_receipt_ids)}: {receipt_id}")

        receipt_data = get_receipt_details_and_html(session, receipt_id)

        if receipt_data and receipt_data["items"]:
            add_receipt_to_json(receipt_data)
            processed_count += 1
            print(f"✓ Added: {len(receipt_data['items'])} items")
        else:
            print("⚠ Failed to process receipt")

        time.sleep(LidlConfig.REQUEST_DELAY)

    if processed_count > 0:
        total_receipts = sort_receipts_by_date()
        print(f"\n{processed_count} new receipt(s) added and sorted.")
    else:
        total_receipts = len(existing_receipts)
        print("\nNo new receipts found.")

    print("\n=== UPDATE COMPLETE ===")
    print(f"New receipts added: {processed_count}")
    print(f"Total receipts in file: {total_receipts}")

    return True
