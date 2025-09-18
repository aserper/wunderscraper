#!/usr/bin/env python3
"""
Debug script to test sensor availability from a Wunderground PWS page.
Usage: python debug/test_sensors.py [URL]
"""
import sys
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import json
import random


def get_value_from_additional_conditions(soup, label):
    """Extract value from additional conditions section."""
    additional_conditions = soup.select_one("lib-additional-conditions")
    if additional_conditions:
        for row in additional_conditions.select(".row"):
            if label in row.text:
                value_tag = row.select_one("span.wu-value.wu-value-to")
                if value_tag:
                    return value_tag.text
    return None


def extract_clouds(soup):
    """Extract clouds/sky condition with special handling."""
    additional_conditions = soup.select_one("lib-additional-conditions")
    if additional_conditions:
        for row in additional_conditions.select(".row"):
            if "Clouds" in row.text:
                spans = row.find_all("span")
                for span in spans:
                    text = span.text.strip()
                    if text and text != "Clouds":
                        return text
    return None


def generate_user_agent():
    """Generate a randomized Chrome user agent string."""
    # Use realistic Chrome version ranges
    major_version = random.randint(120, 134)  # Recent Chrome versions (2023-2024)
    build_number = random.randint(6000, 6500)  # Realistic build range
    patch_number = random.randint(0, 200)     # Typical patch range

    return (
        f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        f"(KHTML, like Gecko) Chrome/{major_version}.0.{build_number}.{patch_number} "
        f"Safari/537.36"
    )


def fahrenheit_to_celsius(fahrenheit_str):
    """Convert Fahrenheit string to Celsius string."""
    if not fahrenheit_str:
        return None

    try:
        # Remove any non-numeric characters except for minus sign and decimal point
        fahrenheit_clean = "".join(c for c in fahrenheit_str if c.isdigit() or c in ['-', '.'])
        if not fahrenheit_clean:
            return None

        fahrenheit = float(fahrenheit_clean)
        celsius = (fahrenheit - 32) * 5 / 9
        return f"{celsius:.1f}"
    except (ValueError, TypeError):
        return None


def test_weather_station(url):
    """Test all sensors for a given weather station URL."""
    print(f"🌦️  Testing Weather Station: {url}")
    print(f"📅 Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print("=" * 80)

    # Generate randomized user agent for each test
    headers = {'User-Agent': generate_user_agent()}
    print(f"🤖 User Agent: {headers['User-Agent']}")

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Test all sensors
        sensors = {}

        # Basic sensors
        temp_elem = soup.select_one("span.wu-value.wu-value-to")
        sensors['temperature'] = temp_elem.text if temp_elem else None

        feels_like_elem = soup.select_one("div.feels-like span.temp")
        sensors['feels_like'] = feels_like_elem.text.replace("°", "") if feels_like_elem else None

        wind_speed_elem = soup.select_one("header.wind-speed strong")
        sensors['wind_speed'] = wind_speed_elem.text if wind_speed_elem else None

        # Additional conditions sensors
        additional_sensors = [
            'Pressure', 'Visibility', 'Dew Point', 'Humidity',
            'Rainfall', 'Snow Depth', 'Wind Gust', 'Precipitation Rate',
            'UV Index', 'UV', 'Solar Radiation', 'Solar'
        ]

        for sensor in additional_sensors:
            value = get_value_from_additional_conditions(soup, sensor)
            if value:
                # Map to our sensor names
                if sensor == 'Rainfall':
                    sensors['precipitation_accumulation'] = value
                elif sensor == 'Dew Point':
                    sensors['dew_point'] = value
                elif sensor in ['UV Index', 'UV']:
                    sensors['uv_index'] = value
                elif sensor in ['Solar Radiation', 'Solar']:
                    sensors['solar_radiation'] = value
                else:
                    sensors[sensor.lower().replace(' ', '_')] = value

        # Special handling for clouds
        sensors['clouds'] = extract_clouds(soup)

        # Wind direction
        wind_dir = soup.select_one(".wind-direction")
        if wind_dir:
            sensors['wind_direction'] = wind_dir.text.strip()
        else:
            wind_compass = soup.select_one(".compass-container")
            if wind_compass:
                sensors['wind_direction'] = wind_compass.text.strip()

        # Print results
        print("\n📊 SENSOR AVAILABILITY REPORT")
        print("-" * 50)

        available_count = 0
        total_count = 0

        # Temperature sensors that need Celsius conversion
        temp_sensors = ['temperature', 'feels_like', 'dew_point']

        sensor_categories = {
            "🌡️  Temperature Sensors": temp_sensors,
            "💨 Wind Sensors": ['wind_speed', 'wind_gust', 'wind_direction'],
            "💧 Moisture Sensors": ['humidity', 'precipitation_accumulation', 'precipitation_rate'],
            "🌫️  Atmospheric Sensors": ['pressure', 'visibility', 'clouds'],
            "❄️  Winter Sensors": ['snow_depth'],
            "☀️  Solar Sensors": ['uv_index', 'solar_radiation']
        }

        for category, sensor_list in sensor_categories.items():
            print(f"\n{category}:")
            for sensor in sensor_list:
                total_count += 1
                if sensor in sensors and sensors[sensor] is not None:
                    available_count += 1
                    fahrenheit_value = sensors[sensor]

                    # Show both F and C for temperature sensors
                    if sensor in temp_sensors:
                        celsius_value = fahrenheit_to_celsius(fahrenheit_value)
                        if celsius_value:
                            print(f"  ✅ {sensor:<25}: {fahrenheit_value}°F ({celsius_value}°C)")
                        else:
                            print(f"  ✅ {sensor:<25}: {fahrenheit_value}°F")
                    else:
                        print(f"  ✅ {sensor:<25}: {fahrenheit_value}")
                else:
                    print(f"  ❌ {sensor:<25}: Not available")

        print(f"\n📈 SUMMARY:")
        print(f"  Available: {available_count}/{total_count} sensors")
        print(f"  Success Rate: {available_count/total_count*100:.1f}%")

        # Time-based recommendations
        current_hour = datetime.now().hour
        if 6 <= current_hour <= 18:
            print(f"  ☀️  Daytime test - UV/Solar sensors should be available if supported")
        else:
            print(f"  🌙 Nighttime test - UV/Solar sensors not expected")

        # Export data
        export_data = {
            'timestamp': datetime.now().isoformat(),
            'url': url,
            'sensors': {k: v for k, v in sensors.items() if v is not None},
            'available_count': available_count,
            'total_count': total_count
        }

        with open('sensor_test_results.json', 'w') as f:
            json.dump(export_data, f, indent=2)

        print(f"\n💾 Results saved to: sensor_test_results.json")

    except requests.exceptions.RequestException as e:
        print(f"❌ Network Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Parsing Error: {e}")
        return False

    return True


if __name__ == "__main__":
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        # Default test URL
        url = "https://www.wunderground.com/dashboard/pws/KNYNEWYO1959"
        print("No URL provided, using default test station")

    test_weather_station(url)