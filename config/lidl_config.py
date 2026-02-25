"""Configuration constants for Lidl API integration."""


class LidlConfig:
    """Configuration constants for Lidl API integration."""

    # File paths
    RECEIPTS_JSON_FILE = "lidl_receipts.json"
    COOKIES_JSON_FILE = "lidl_cookies.json"

    # Country settings (can be changed via set_country)
    COUNTRY = "gb"

    # Request settings
    DEFAULT_TIMEOUT = 15
    REQUEST_DELAY = 0.5
    PAGES_TO_CHECK = 3

    # Browser settings
    SUPPORTED_BROWSERS = {"firefox": "Firefox", "chrome": "Chrome", "chromium": "Chromium"}

    # API settings
    DEFAULT_PAGE_SIZE = 10

    # Countries that use a non-standard TLD (not lidl.<country>)
    _DOMAIN_OVERRIDES = {
        "gb": "lidl.co.uk",
    }

    # Countries whose language code differs from the <country>-<COUNTRY> default
    _LANGUAGE_OVERRIDES = {
        "gb": "en-GB",
    }

    @classmethod
    def get_base_url(cls) -> str:
        """Get the base URL for the current country."""
        domain = cls.get_cookie_domain()
        return f"https://www.{domain}"

    @classmethod
    def get_tickets_url(cls) -> str:
        """Get the tickets API URL."""
        return f"{cls.get_base_url()}/mre/api/v1/tickets"

    @classmethod
    def get_receipt_url(cls, receipt_id: str) -> str:
        """Get the receipt API URL for a specific receipt."""
        return f"{cls.get_base_url()}/mre/api/v1/tickets/{receipt_id}"

    @classmethod
    def get_country_code(cls) -> str:
        """Get the country code in uppercase (e.g., 'GB', 'DE', 'BG')."""
        return cls.COUNTRY.upper()

    @classmethod
    def get_language_code(cls) -> str:
        """Get the language code (e.g., 'en-GB', 'de-DE', 'bg-BG')."""
        return cls._LANGUAGE_OVERRIDES.get(
            cls.COUNTRY, f"{cls.COUNTRY}-{cls.COUNTRY.upper()}"
        )

    @classmethod
    def get_cookie_domain(cls) -> str:
        """Get the domain for cookie extraction (e.g., 'lidl.co.uk', 'lidl.de')."""
        return cls._DOMAIN_OVERRIDES.get(cls.COUNTRY, f"lidl.{cls.COUNTRY}")

    @classmethod
    def set_country(cls, country: str) -> None:
        """
        Set the country and update all derived settings.

        Args:
            country: Two-letter country code (e.g., 'gb', 'de', 'nl')
        """
        cls.COUNTRY = country.lower()
