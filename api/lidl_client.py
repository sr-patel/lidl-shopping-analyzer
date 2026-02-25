"""Lidl API client for fetching receipt data."""

import json
from typing import Optional, Dict, Any
import requests

from config import LidlConfig
from parsing import parse_receipt_html


def get_tickets_page(
    session: requests.Session, page: int = 1
) -> Optional[Dict[str, Any]]:
    """
    Fetch tickets for a specific page using the API.

    Args:
        session: requests.Session with authentication
        page: Page number to fetch

    Returns:
        dict: API response data or None if error
    """
    try:
        response = session.get(
            f"{LidlConfig.get_tickets_url()}?country={LidlConfig.get_country_code()}&page={page}",
            timeout=LidlConfig.DEFAULT_TIMEOUT,
        )
        response.raise_for_status()

        data = response.json()

        if isinstance(data, list):
            return {
                "items": data,
                "page": page,
                "size": len(data),
                "totalCount": len(data),
            }
        elif isinstance(data, dict):
            return data
        else:
            print(f"Unexpected API response structure for page {page}")
            return None

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            print(f"✗ Unauthorised when fetching tickets page {page}")
            print("Please ensure you are logged in to Lidl in your browser.")
        else:
            print(f"✗ HTTP error fetching tickets page {page}: {e}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"✗ Error fetching tickets page {page}: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"✗ JSON decode error for page {page}: {e}")
        return None


def get_receipt_details_and_html(
    session: requests.Session, receipt_id: str
) -> Optional[Dict[str, Any]]:
    """
    Fetch receipt details and HTML content for a specific receipt.

    Args:
        session: requests.Session with authentication
        receipt_id: Receipt ID to fetch

    Returns:
        dict: Parsed receipt data or None if error
    """
    try:
        url = LidlConfig.get_receipt_url(receipt_id)
        full_url = f"{url}?country={LidlConfig.get_country_code()}&languageCode={LidlConfig.get_language_code()}"

        response = session.get(full_url, timeout=LidlConfig.DEFAULT_TIMEOUT)
        response.raise_for_status()

        data = response.json()

        if "ticket" in data:
            ticket_data = data["ticket"]
        else:
            ticket_data = data

        receipt_date = ticket_data["date"][:10].replace("-", ".")
        total_amount = ticket_data["totalAmount"]

        if isinstance(ticket_data.get("store"), dict):
            store = ticket_data["store"].get("name", "Unknown")
        else:
            store = ticket_data.get("store", "Unknown")

        html_content = ticket_data.get("htmlPrintedReceipt", "")

        if not html_content:
            print(f"  No HTML content found for receipt_id: {receipt_id}")
            return None

        parsed_data = parse_receipt_html(
            html_content, receipt_id, receipt_date, total_amount, store
        )

        return parsed_data

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            print(f"  Unauthorised when fetching receipt_id: {receipt_id}")
            print("  Please ensure you are logged in to Lidl in your browser.")
        else:
            print(f"  HTTP error fetching receipt: {e}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"  Error fetching receipt: {e}")
        return None
    except Exception as e:
        print(f"  Unexpected error: {e}")
        return None
