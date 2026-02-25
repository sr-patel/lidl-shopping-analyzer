"""File-based cookie loading for authentication."""

import os
import json
from typing import Optional
import requests

from config import LidlConfig


def load_cookies_from_file(file_path: Optional[str] = None) -> Optional[requests.Session]:
    """
    Load authentication cookies from a JSON file (e.g., exported from EditThisCookie).
    
    The JSON file should contain an array of cookie objects with fields like:
    - domain, name, value, path, secure, httpOnly, etc.
    
    Args:
        file_path: Path to the cookie JSON file. If None, uses default from config.
    
    Returns:
        requests.Session: Session with loaded cookies, or None if error
    """
    if file_path is None:
        file_path = LidlConfig.COOKIES_JSON_FILE

    cookie_domain = LidlConfig.get_cookie_domain()

    print(f"Loading cookies from file: {file_path}...")
    
    try:
        if not os.path.exists(file_path):
            print(f"✗ Cookie file not found: {file_path}")
            print(f"\nPlease create a file '{file_path}' containing your cookies.")
            print("You can export cookies using browser extensions such as:")
            print("  - EditThisCookie (export as JSON)")
            print("  - Cookie-Editor")
            print("\nThe file should contain a JSON array of cookie objects.")
            return None
        
        with open(file_path, 'r', encoding='utf-8') as f:
            cookies_data = json.load(f)
        
        if isinstance(cookies_data, dict) and 'cookies' in cookies_data:
            cookies_list = cookies_data['cookies']
        elif isinstance(cookies_data, list):
            cookies_list = cookies_data
        else:
            print("✗ Invalid cookie file format. Expected a JSON array or an object with a 'cookies' field.")
            return None
        
        session = requests.Session()
        
        cookie_count = 0
        for cookie_data in cookies_list:
            domain = cookie_data.get('domain', '')
            if cookie_domain not in domain:
                continue
            
            session.cookies.set_cookie(
                requests.cookies.create_cookie(
                    domain=cookie_data.get('domain', ''),
                    name=cookie_data.get('name', ''),
                    value=cookie_data.get('value', ''),
                    path=cookie_data.get('path', '/'),
                    secure=cookie_data.get('secure', False),
                    expires=cookie_data.get('expirationDate', None),
                )
            )
            cookie_count += 1
        
        if cookie_count == 0:
            print(f"✗ No cookies found for {cookie_domain} in the file.")
            return None
        
        print(f"✓ Successfully loaded {cookie_count} cookies from file")
        return session
    
    except json.JSONDecodeError as e:
        print(f"✗ Failed to parse cookie file: {e}")
        print("Please ensure the file contains valid JSON.")
        return None
    except Exception as e:
        print(f"✗ Failed to load cookie file: {e}")
        return None
