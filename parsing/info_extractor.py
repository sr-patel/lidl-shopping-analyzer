"""Extract basic receipt information from HTML content."""

import re
from typing import Dict, Any
from bs4 import BeautifulSoup


# Text patterns for the "amount to pay" line, covering both English (UK) and German receipts
_TO_PAY_PATTERNS = ["to pay", "amount due", "amount payable", "total to pay", "zu zahlen"]

# Text patterns for regular (non-Lidl-Plus) savings lines
# Exclusion list prevents double-counting Lidl Plus lines
_SAVINGS_INCLUDE_PATTERNS = ["price advantage", "savings", "saving", "preisvorteil"]
_DISCOUNT_INCLUDE_PATTERNS = ["discount", "reduction", "rabatt"]
_SAVINGS_EXCLUDE_PATTERNS = ["lidl plus discount", "lidl plus saving", "lidl plus rabatt", "total savings"]

# Patterns for the Lidl Plus savings summary box
_LIDL_PLUS_SAVED_PATTERNS = [
    r"(\d+[.,]\d+)\s+GBP\s+saved",
    r"(\d+[.,]\d+)\s+EUR\s+saved",
    r"(\d+[.,]\d+)\s+gespart",
    r"saved\s+(\d+[.,]\d+)",
]

# Amount pattern: accepts both comma and dot as decimal separator
_AMOUNT_RE = re.compile(r"-(\d+[.,]\d+)")
_PRICE_RE = re.compile(r"^\d+[.,]\d+$")


def _normalise_amount(value: str) -> float:
    """Convert a price string with either ',' or '.' decimal separator to float."""
    # If both separators are present, the last one is the decimal separator
    if "," in value and "." in value:
        # e.g. "1,234.56" (UK thousands) or "1.234,56" (DE thousands)
        if value.rfind(".") > value.rfind(","):
            return float(value.replace(",", ""))
        else:
            return float(value.replace(".", "").replace(",", "."))
    return float(value.replace(",", "."))


def _format_amount(value: float) -> str:
    """Format a float as a string with '.' decimal separator (UK style)."""
    return f"{value:.2f}"


def extract_basic_receipt_info_from_html(
    soup: BeautifulSoup, receipt_id: str, receipt_date: str, store: str
) -> Dict[str, Any]:
    """Extract basic receipt information from the HTML receipt."""
    receipt_data = {
        "id": receipt_id,
        "purchase_date": receipt_date,
        "total_price": None,
        "total_price_no_saving": None,
        "saved_amount": None,
        "saved_pfand": None,
        "lidlplus_saved_amount": None,
        "store": store,
        "items": [],
    }

    # --- Total price ("amount to pay") ---
    try:
        purchase_summary_elements = soup.find_all(id=re.compile(r"^purchase_summary_"))
        for element in purchase_summary_elements:
            element_text = element.get_text().strip().lower()
            if any(pattern in element_text for pattern in _TO_PAY_PATTERNS):
                parent = element.parent
                amount_spans = parent.find_all("span", class_="css_bold")
                for span in amount_spans:
                    span_text = span.get_text().strip()
                    if _PRICE_RE.match(span_text):
                        receipt_data["total_price"] = span_text
                        break
                if receipt_data["total_price"]:
                    break
    except Exception:
        try:
            total_element = soup.find(id="purchase_tender_information_5")
            if total_element:
                parts = total_element.get_text().strip().split()
                if len(parts) >= 2:
                    receipt_data["total_price"] = parts[-2]
        except Exception:
            pass

    # --- Regular savings (price advantages / discounts, excluding Lidl Plus) ---
    try:
        total_regular_savings = 0.0
        purchase_list = soup.find("span", class_="purchase_list")
        if purchase_list:
            purchase_text = purchase_list.get_text()
            lines = purchase_text.split("\n")
            for line in lines:
                line_lower = line.lower()
                # Skip lines that are Lidl Plus savings
                if any(excl in line_lower for excl in _SAVINGS_EXCLUDE_PATTERNS):
                    continue
                matched = False
                if any(pat in line_lower for pat in _SAVINGS_INCLUDE_PATTERNS):
                    matched = True
                elif any(pat in line_lower for pat in _DISCOUNT_INCLUDE_PATTERNS):
                    matched = True
                if matched:
                    amount_match = _AMOUNT_RE.search(line)
                    if amount_match:
                        try:
                            total_regular_savings += _normalise_amount(amount_match.group(1))
                        except (ValueError, AttributeError):
                            pass

        if total_regular_savings > 0:
            receipt_data["saved_amount"] = _format_amount(total_regular_savings)
    except Exception:
        pass

    # --- Lidl Plus savings ---
    try:
        vat_info_elements = soup.find_all("span", class_="vat_info")
        for element in vat_info_elements:
            element_text = element.get_text().strip()
            for pattern in _LIDL_PLUS_SAVED_PATTERNS:
                match = re.search(pattern, element_text, re.IGNORECASE)
                if match:
                    receipt_data["lidlplus_saved_amount"] = _format_amount(
                        _normalise_amount(match.group(1))
                    )
                    break
            if receipt_data["lidlplus_saved_amount"]:
                break

        if not receipt_data["lidlplus_saved_amount"]:
            page_text = soup.get_text()
            for pattern in _LIDL_PLUS_SAVED_PATTERNS:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    receipt_data["lidlplus_saved_amount"] = _format_amount(
                        _normalise_amount(match.group(1))
                    )
                    break
    except Exception:
        pass

    return receipt_data
