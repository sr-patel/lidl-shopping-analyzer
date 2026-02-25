"""Browser cookie extraction for authentication."""

import requests
import browser_cookie3

from config import LidlConfig


def extract_browser_cookies(browser="firefox"):
    """
    Extract authentication cookies from browser for Lidl website.

    Args:
        browser: Browser to extract cookies from ('firefox', 'chrome', or 'chromium')

    Returns:
        requests.Session: Session with Lidl authentication cookies
    """
    browser_name = LidlConfig.SUPPORTED_BROWSERS.get(browser, browser)
    cookie_domain = LidlConfig.get_cookie_domain()

    print(f"Extracting cookies for {cookie_domain} from {browser_name}...")

    try:
        if browser == "firefox":
            cookies = browser_cookie3.firefox(domain_name=cookie_domain)
        elif browser == "chrome":
            cookies = browser_cookie3.chrome(domain_name=cookie_domain)
        elif browser == "chromium":
            cookies = browser_cookie3.chromium(domain_name=cookie_domain)
        else:
            raise ValueError(f"Unknown browser: {browser}")

        session = requests.Session()

        for cookie in cookies:
            session.cookies.set_cookie(
                requests.cookies.create_cookie(
                    domain=cookie.domain,
                    name=cookie.name,
                    value=cookie.value,
                    secure=cookie.secure,
                    path=cookie.path,
                )
            )

        print(f"Successfully extracted {len(session.cookies)} cookies from {browser_name}")
        return session

    except Exception as e:
        print(f"Failed to extract {browser_name} cookies: {e}")
        print("Please ensure that:")
        print(f"1. {browser_name} is running and you are logged in to Lidl")
        print(f"2. The Lidl website (www.{cookie_domain}) is open in {browser_name}")
        return None
