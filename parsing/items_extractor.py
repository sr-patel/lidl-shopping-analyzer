"""Extract receipt items from HTML content."""

import re
from typing import List, Dict, Any
from bs4 import BeautifulSoup

# Price pattern: accepts both comma and dot as decimal separator
_PRICE_RE = re.compile(r"^\d+[.,]\d+$")


def _normalise_amount(value: str) -> float:
    """Convert a price string with either ',' or '.' decimal separator to float."""
    if "," in value and "." in value:
        if value.rfind(".") > value.rfind(","):
            return float(value.replace(",", ""))
        else:
            return float(value.replace(".", "").replace(",", "."))
    return float(value.replace(",", "."))


def extract_receipt_items_from_html(soup: BeautifulSoup) -> List[Dict[str, Any]]:
    """Extract items from receipt HTML."""
    items = []
    try:
        article_spans = soup.find_all("span", class_="article")

        if not article_spans:
            print("No article spans found")
            return items

        items_by_id_and_desc = {}
        for span in article_spans:
            art_id = span.get("data-art-id")
            art_description = span.get("data-art-description", "")
            if art_id and art_description:
                key = f"{art_id}_{art_description}"
                if key not in items_by_id_and_desc:
                    items_by_id_and_desc[key] = []
                items_by_id_and_desc[key].append(span)

        for art_id_and_desc, spans in items_by_id_and_desc.items():
            try:
                main_span = spans[0]

                art_description = main_span.get("data-art-description", "")
                art_quantity = main_span.get("data-art-quantity", "1")
                unit_price = main_span.get("data-unit-price", "")

                if not art_description or not unit_price:
                    continue

                total_price_text = unit_price
                for span in spans:
                    span_class = span.get("class", [])
                    if "css_bold" in span_class:
                        span_text = span.get_text().strip()
                        if _PRICE_RE.match(span_text):
                            try:
                                price_val = _normalise_amount(span_text)
                                unit_val = _normalise_amount(unit_price)
                                qty_val = _normalise_amount(art_quantity)

                                expected_total = unit_val * qty_val
                                if abs(price_val - expected_total) < 0.01:
                                    total_price_text = span_text
                                    break
                            except (ValueError, AttributeError):
                                pass

                # Determine unit from span text content
                unit = "each"
                for span in spans:
                    span_text = span.get_text()
                    if "kg" in span_text or "/kg" in span_text:
                        unit = "kg"
                        break

                items.append(
                    {
                        "name": art_description,
                        "price": unit_price,
                        "quantity": art_quantity,
                        "unit": unit,
                    }
                )

            except Exception as e:
                print(f"Error extracting item: {e}")

    except Exception as e:
        print(f"Items not found: {e}")

    return items
