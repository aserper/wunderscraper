#!/usr/bin/env python3
"""
Debug script to help find and validate Wunderground Personal Weather Station URLs.
Usage: python debug/find_stations.py [location]
"""
import sys
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse


def search_stations_by_location(location):
    """Search for weather stations near a location."""
    print(f"🔍 Searching for weather stations near: {location}")

    # Search URL format for Wunderground
    search_url = f"https://www.wunderground.com/wundermap"

    print(f"📍 Manual search suggestion:")
    print(f"   1. Visit: {search_url}")
    print(f"   2. Search for: {location}")
    print(f"   3. Click on PWS icons on the map")
    print(f"   4. Copy the station URL from your browser")
    print(f"   5. Test with: python debug/test_sensors.py <station_url>")


def validate_pws_url(url):
    """Validate if a URL is a valid Wunderground PWS URL."""
    print(f"🔍 Validating PWS URL: {url}")

    # Check URL format
    pws_patterns = [
        r"wunderground\.com/dashboard/pws/[A-Z0-9]+",
        r"wunderground\.com/weather/.+/[A-Z0-9]+",
    ]

    is_valid_format = any(re.search(pattern, url) for pattern in pws_patterns)

    if not is_valid_format:
        print("❌ Invalid URL format")
        print("✅ Valid formats:")
        print("   - https://www.wunderground.com/dashboard/pws/STATION_ID")
        print("   - https://www.wunderground.com/weather/us/state/city/STATION_ID")
        return False

    print("✅ URL format looks valid")

    # Test if URL is accessible
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (compatible; WundergroundScraper/1.0)'}
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            print("✅ URL is accessible")

            # Check if it has weather data
            soup = BeautifulSoup(response.text, 'html.parser')
            temp_elem = soup.select_one("span.wu-value.wu-value-to")

            if temp_elem:
                print(f"✅ Weather data found (Temperature: {temp_elem.text})")
                return True
            else:
                print("⚠️  URL accessible but no weather data found")
                return False
        else:
            print(f"❌ URL returned status code: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Error accessing URL: {e}")
        return False


def extract_station_id_from_url(url):
    """Extract station ID from various URL formats."""
    patterns = [
        r"/pws/([A-Z0-9]+)",
        r"/([A-Z0-9]+)/?$",
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)

    return None


def suggest_alternative_urls(base_url):
    """Suggest alternative URL formats for a station."""
    station_id = extract_station_id_from_url(base_url)

    if not station_id:
        print("❌ Could not extract station ID from URL")
        return []

    print(f"📋 Station ID: {station_id}")
    print(f"🔄 Alternative URL formats to try:")

    alternatives = [
        f"https://www.wunderground.com/dashboard/pws/{station_id}",
        f"https://www.wunderground.com/weather/us/state/city/{station_id}",
    ]

    for i, alt_url in enumerate(alternatives, 1):
        print(f"   {i}. {alt_url}")

    return alternatives


def test_multiple_urls(urls):
    """Test multiple URLs and report which ones work."""
    print(f"\n🧪 Testing {len(urls)} URLs...")

    working_urls = []

    for i, url in enumerate(urls, 1):
        print(f"\n--- Test {i}/{len(urls)} ---")
        if validate_pws_url(url):
            working_urls.append(url)

    print(f"\n📊 Results: {len(working_urls)}/{len(urls)} URLs working")

    if working_urls:
        print("✅ Working URLs:")
        for url in working_urls:
            print(f"   • {url}")

    return working_urls


if __name__ == "__main__":
    if len(sys.argv) > 1:
        arg = sys.argv[1]

        # Check if argument looks like a URL
        if arg.startswith("http"):
            print("🔗 Testing provided URL...")
            validate_pws_url(arg)
            suggest_alternative_urls(arg)
        else:
            # Treat as location search
            search_stations_by_location(arg)
    else:
        print("🌦️  Wunderground PWS URL Finder & Validator")
        print("=" * 50)
        print("Usage:")
        print("  python debug/find_stations.py <location>     # Search for stations")
        print("  python debug/find_stations.py <url>         # Validate PWS URL")
        print("")
        print("Examples:")
        print("  python debug/find_stations.py 'Boston, MA'")
        print("  python debug/find_stations.py https://www.wunderground.com/dashboard/pws/KMABOSTO123")
        print("")

        # Test with default example
        print("Testing with default example...")
        test_url = "https://www.wunderground.com/weather/us/ma/wellesley/KMAWELLE41"
        validate_pws_url(test_url)