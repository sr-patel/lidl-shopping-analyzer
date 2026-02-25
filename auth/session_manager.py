"""Session management and API connection testing."""

import json
from typing import Optional
import requests

from config import LidlConfig
from cli.prompts import select_auth_method
from .file_auth import load_cookies_from_file
from .browser_auth import extract_browser_cookies


def setup_and_test_session(
    auth_method: Optional[str] = None,
    cookies_file: Optional[str] = None,
) -> Optional[requests.Session]:
    """
    Common setup logic for both initial_setup and update_data.
    Handles browser selection, cookie extraction, and API testing.

    Args:
        auth_method: Authentication method - 'firefox', 'chrome', 'chromium', or 'file'.
                     If None, prompts user interactively.
        cookies_file: Path to cookies file (only used when auth_method is 'file').

    Returns:
        requests.Session: Authenticated session if successful, None otherwise
    """
    if auth_method is None:
        auth_method = select_auth_method()

    if auth_method == "file":
        session = load_cookies_from_file(cookies_file)
    else:
        session = extract_browser_cookies(auth_method)
    
    if not session:
        return None

    if not test_api_connection(session):
        return None

    return session


def test_api_connection(session: requests.Session) -> bool:
    """
    Test if the API connection with extracted cookies works.

    Args:
        session: requests.Session with authentication cookies

    Returns:
        bool: True if connection works, False otherwise
    """
    print("Testing API connection...")

    try:
        response = session.get(
            f"{LidlConfig.get_tickets_url()}?country={LidlConfig.get_country_code()}&page=1",
            timeout=LidlConfig.DEFAULT_TIMEOUT,
        )
        response.raise_for_status()

        data = response.json()
        if "items" in data and len(data["items"]) > 0:
            print(f"✓ API connection successful! {data['totalCount']} receipts found")
            return True
        else:
            print("⚠ API response contains no receipts")
            return False

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            print("✗ API connection failed: Unauthorised (401)")
            print("Please ensure you are logged in to Lidl in your browser.")
            print(
                f"Open {LidlConfig.get_base_url()} in your browser and sign in before running this program."
            )
        else:
            print(f"✗ API connection error ({e.response.status_code}): {e}")
        return False
    except requests.exceptions.RequestException as e:
        print(f"✗ API connection error: {e}")
        return False
    except json.JSONDecodeError as e:
        print(f"✗ JSON decode error: {e}")
        return False
