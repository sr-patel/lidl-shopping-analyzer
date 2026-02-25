"""Receipt ID collection and processing logic."""

import time
from typing import List, Tuple
import requests

from config import LidlConfig
from api import get_tickets_page, get_receipt_details_and_html
from storage import load_existing_receipts, add_receipt_to_json


def collect_all_receipt_ids(session: requests.Session) -> List[str]:
    """
    Collect all receipt IDs from all pages efficiently.

    Args:
        session: requests.Session with authentication

    Returns:
        list: List of all receipt IDs
    """
    all_receipt_ids = []
    page = 1

    print("Collecting all receipt IDs with digital receipts via API...")

    while True:
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
                    all_receipt_ids.append(receipt_id)

        page += 1

        total_count = tickets_data.get("totalCount", 0)
        page_size = tickets_data.get("size", 10)
        total_pages = (total_count + page_size - 1) // page_size

        if page > total_pages:
            break

    print(f"Found: {len(all_receipt_ids)} receipt IDs")
    return all_receipt_ids


def process_all_tickets(session: requests.Session) -> Tuple[int, int, int]:
    """
    Process all tickets efficiently by collecting IDs first, then fetching HTML.

    Args:
        session: requests.Session with authentication

    Returns:
        tuple: (processed_count, skipped_count, total_pages)
    """
    processed_count = 0
    skipped_count = 0

    existing_ids, _ = load_existing_receipts()

    all_receipt_ids = collect_all_receipt_ids(session)

    print(f"Receipts to process: {len(all_receipt_ids)}")
    print(f"Already stored: {len(existing_ids)}")

    new_receipt_ids = [rid for rid in all_receipt_ids if rid not in existing_ids]

    print(f"New receipts to process: {len(new_receipt_ids)}")

    for i, receipt_id in enumerate(new_receipt_ids, 1):
        print(f"Processing receipt {i}/{len(new_receipt_ids)}: {receipt_id}")

        receipt_data = get_receipt_details_and_html(session, receipt_id)

        if receipt_data and receipt_data["items"]:
            add_receipt_to_json(receipt_data)
            processed_count += 1
            print(f"✓ Processed: {len(receipt_data['items'])} items")
        else:
            print("⚠ Failed to process receipt")
            skipped_count += 1

        time.sleep(LidlConfig.REQUEST_DELAY)

    return processed_count, skipped_count, len(all_receipt_ids) // 10 + 1
