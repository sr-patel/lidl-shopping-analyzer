"""Main receipt HTML parser."""

import re
from typing import Dict, Any
from bs4 import BeautifulSoup

from .info_extractor import extract_basic_receipt_info_from_html
from .items_extractor import extract_receipt_items_from_html

# Deposit return line keywords (German: Pfandrückgabe, English: deposit return / bottle return)
_DEPOSIT_RETURN_PATTERNS = [
    "pfandrückgabe",
    "deposit return",
    "bottle return",
]


def _normalise_amount(value: str) -> float:
    """Convert a price string with either ',' or '.' decimal separator to float."""
    if "," in value and "." in value:
        if value.rfind(".") > value.rfind(","):
            return float(value.replace(",", ""))
        else:
            return float(value.replace(".", "").replace(",", "."))
    return float(value.replace(",", "."))


def _format_amount(value: float) -> str:
    """Format a float as a price string (e.g. '1.99')."""
    return f"{value:.2f}"


def parse_receipt_html(
    html_content: str, receipt_id: str, receipt_date: str, total_amount: float, store: str
) -> Dict[str, Any]:
    """
    Parse receipt HTML content to extract items and other data.

    Args:
        html_content: HTML content of the receipt (from ticket.htmlPrintedReceipt)
        receipt_id: Receipt ID
        receipt_date: Receipt date
        total_amount: Total amount from API (might be 0)
        store: Store name

    Returns:
        dict: Parsed receipt data
    """
    soup = BeautifulSoup(html_content, "html.parser")

    receipt_data = extract_basic_receipt_info_from_html(
        soup, receipt_id, receipt_date, store
    )

    receipt_data["items"] = extract_receipt_items_from_html(soup)

    # Calculate total from items (price before savings)
    total_from_items = 0.0
    for item in receipt_data.get("items", []):
        try:
            item_price = _normalise_amount(item.get("price", "0"))
            item_qty = _normalise_amount(item.get("quantity", "1"))
            total_from_items += item_price * item_qty
        except (ValueError, AttributeError):
            pass

    if total_from_items > 0:
        receipt_data["total_price_no_saving"] = _format_amount(total_from_items)

        total_savings = 0.0

        if receipt_data.get("saved_amount"):
            try:
                total_savings += _normalise_amount(receipt_data["saved_amount"])
            except (ValueError, AttributeError):
                pass

        if receipt_data.get("lidlplus_saved_amount"):
            try:
                total_savings += _normalise_amount(receipt_data["lidlplus_saved_amount"])
            except (ValueError, AttributeError):
                pass

        # Extract deposit return savings from HTML
        deposit_savings = 0.0
        try:
            purchase_list = soup.find("span", class_="purchase_list")
            if purchase_list:
                purchase_text = purchase_list.get_text()

                for dep_pattern in _DEPOSIT_RETURN_PATTERNS:
                    # Match deposit return lines with an amount on the same line
                    matches = re.findall(
                        rf"{re.escape(dep_pattern)}\s*(-?\d+[.,]\d+)",
                        purchase_text,
                        re.IGNORECASE,
                    )
                    for match in matches:
                        try:
                            deposit_savings += abs(_normalise_amount(match))
                        except (ValueError, AttributeError):
                            pass

                # Fallback: quantity × price calculation lines near deposit keywords
                if deposit_savings == 0:
                    text_lower = purchase_text.lower()
                    for dep_pattern in _DEPOSIT_RETURN_PATTERNS:
                        if dep_pattern in text_lower:
                            calc_matches = re.findall(r"(-?\d+)\s*x\s*(-?\d+[.,]\d+)", purchase_text)
                            for qty_match, price_match in calc_matches:
                                try:
                                    qty = float(qty_match)
                                    price = _normalise_amount(price_match)
                                    deposit_savings += abs(qty * price)
                                except (ValueError, AttributeError):
                                    pass
                            break
        except Exception:
            pass

        if deposit_savings > 0:
            receipt_data["saved_deposit"] = _format_amount(deposit_savings)
            total_savings += deposit_savings

        final_paid = total_from_items - total_savings
        if final_paid > 0:
            receipt_data["total_price"] = _format_amount(final_paid)

    return receipt_data
